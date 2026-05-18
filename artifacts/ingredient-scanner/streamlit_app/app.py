import streamlit as st
import sys
import os
import sqlite3
import json
from datetime import datetime
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__) + "/../..")

from backend.scan_service import analyze_ingredients_from_image, get_ingredient_database
from backend.database import SessionLocal, init_db
from backend import models

# Initialize database
init_db()

st.set_page_config(
    page_title="SafeScan — AI Ingredient Scanner",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Session state for database operations
db = SessionLocal()

# ── Custom CSS (dark-theme accents) ───────────────────────────────────────────
st.markdown("""
<style>
/* Tier badge pills */
.tier-safe             { background:#1a4731; color:#4ade80; border:1px solid #166534;
                          padding:2px 10px; border-radius:12px; font-size:0.75rem; font-weight:600; }
.tier-low-concern      { background:#1e3a5f; color:#60a5fa; border:1px solid #1d4ed8;
                          padding:2px 10px; border-radius:12px; font-size:0.75rem; font-weight:600; }
.tier-moderate-concern { background:#3b2a00; color:#fbbf24; border:1px solid #92400e;
                          padding:2px 10px; border-radius:12px; font-size:0.75rem; font-weight:600; }
.tier-high-concern     { background:#3b0a0a; color:#f87171; border:1px solid #991b1b;
                          padding:2px 10px; border-radius:12px; font-size:0.75rem; font-weight:600; }
.tier-unknown          { background:#1f2937; color:#9ca3af; border:1px solid #374151;
                          padding:2px 10px; border-radius:12px; font-size:0.75rem; font-weight:600; }
/* Confidence bar */
.conf-bar-wrap { background:#1f2937; border-radius:4px; height:6px; width:100%; margin-top:4px; }
.conf-bar-fill { border-radius:4px; height:6px; }
/* OCR badge */
.ocr-badge { background:#161b22; border:1px solid #30363d; color:#8b949e;
              padding:2px 8px; border-radius:8px; font-size:0.72rem; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ────────────────────────────────────────────────────────────────────
st.sidebar.title("🔬 SafeScan")
st.sidebar.markdown("AI-powered ingredient safety analyzer")
st.sidebar.markdown("---")
st.sidebar.caption("v3 · PaddleOCR + NLP pipeline · 1,403 ingredients")

PROFILES = {
    "general":  "General Adult",
    "children": "Children",
    "pregnant": "Pregnant",
    "elderly":  "Elderly",
}

GRADE_ICON = {"A": "🟢", "B": "🟡", "C": "🟠", "D": "🔴", "F": "⛔"}
TIER_ORDER = ["high_concern", "moderate_concern", "low_concern", "safe", "unknown"]

TIER_CSS_CLASS = {
    "safe":             "tier-safe",
    "low_concern":      "tier-low-concern",
    "moderate_concern": "tier-moderate-concern",
    "high_concern":     "tier-high-concern",
    "unknown":          "tier-unknown",
}

CONF_BAR_COLOR = {
    "safe":             "#4ade80",
    "low_concern":      "#60a5fa",
    "moderate_concern": "#fbbf24",
    "high_concern":     "#f87171",
    "unknown":          "#6b7280",
}


# ── OCR engine wrapper ─────────────────────────────────────────────────────────

def run_ocr_engine(image_bytes: bytes) -> tuple[list, str]:
    """
    Try PaddleOCR first (better accuracy), fall back to EasyOCR.

    Returns:
      (list of (bbox, text, confidence), engine_name)
    """
    try:
        from paddleocr import PaddleOCR
        paddle = PaddleOCR(
            use_angle_cls=True, lang="en", use_gpu=False,
            show_log=False, use_doc_orientation_classify=False,
            use_doc_unwarping=False,
        )
        raw = paddle.ocr(image_bytes, cls=True)
        results = []
        for page in (raw or []):
            for line in (page or []):
                bbox, (text, conf) = line
                results.append((bbox, text, float(conf)))
        return results, "PaddleOCR"
    except Exception:
        pass

    try:
        import easyocr
        reader  = easyocr.Reader(["en"], gpu=False)
        results = reader.readtext(image_bytes, detail=1)
        return [(bbox, text, float(conf)) for bbox, text, conf in results], "EasyOCR"
    except Exception as e:
        raise RuntimeError(f"Both OCR engines failed: {e}")


# ── Header ─────────────────────────────────────────────────────────────────────
st.title("🔬 Analyze Product Safety")
st.markdown(
    "Paste an ingredient list or upload a product label photo. "
    "The AI pipeline isolates the ingredient section, removes noise, and "
    "scores every ingredient against a 1,403-entry verified database."
)

tab_paste, tab_ocr = st.tabs(["📋 Paste Text", "📷 Scan Label (OCR)"])

raw_text_input = ""
ocr_final_text = ""
is_ocr_mode    = False

# ════════════════════════════════════════════════════════════════════════════════
# TAB 1 — Paste text
# ════════════════════════════════════════════════════════════════════════════════
with tab_paste:
    raw_text_input = st.text_area(
        "Ingredient List",
        placeholder=(
            "e.g. Water, Sugar, E211 (Sodium Benzoate), E102, "
            "Citric Acid, Natural Flavors, Palm Oil, Modified Starch..."
        ),
        height=180,
        key="paste_input",
    )

# ════════════════════════════════════════════════════════════════════════════════
# TAB 2 — OCR
# ════════════════════════════════════════════════════════════════════════════════
with tab_ocr:
    uploaded_file = st.file_uploader(
        "Upload a product label photo (JPG / PNG / WEBP)",
        type=["jpg", "jpeg", "png", "bmp", "webp"],
        key="ocr_upload",
    )

    if uploaded_file is not None:
        from PIL import Image
        orig_img = Image.open(uploaded_file)

        # ── Enhancement options ────────────────────────────────────────────────
        st.markdown("#### Image Pre-processing")
        st.caption("Applied before OCR to maximise text readability.")

        ec1, ec2, ec3, ec4 = st.columns(4)
        with ec1:
            do_upscale  = st.checkbox("Upscale resolution",   value=True, key="enh_upscale")
            do_glare    = st.checkbox("Glare/shadow removal", value=True, key="enh_glare")
        with ec2:
            do_denoise  = st.checkbox("Denoising",            value=True, key="enh_denoise")
            do_deskew   = st.checkbox("Text straightening",   value=True, key="enh_deskew")
        with ec3:
            do_contrast = st.checkbox("Contrast (CLAHE)",     value=True, key="enh_contrast")
            do_sharpen  = st.checkbox("Sharpening",           value=True, key="enh_sharpen")
        with ec4:
            do_bg       = st.checkbox("Background cleaning",  value=True, key="enh_bg")
            run_enhance = st.button("✨ Enhance Image", key="btn_enhance", use_container_width=True)

        steps = {
            "upscale": do_upscale, "glare_shadow": do_glare, "denoise": do_denoise,
            "deskew": do_deskew, "contrast": do_contrast, "sharpen": do_sharpen,
            "background": do_bg,
        }

        for key, default in [
            ("enhanced_img", None), ("applied_steps", []),
            ("ocr_extracted", ""), ("ocr_raw_detail", []),
            ("ocr_engine", ""), ("ocr_reconstruction", {}),
        ]:
            if key not in st.session_state:
                st.session_state[key] = default

        if run_enhance:
            with st.spinner("Enhancing image…"):
                enh, applied = enhance_for_ocr(orig_img, steps)
                st.session_state.enhanced_img  = enh
                st.session_state.applied_steps = applied

        bc, ac = st.columns(2)
        with bc:
            st.markdown("**Original**")
            st.image(orig_img, use_container_width=True)
        with ac:
            st.markdown("**Enhanced**")
            if st.session_state.enhanced_img is not None:
                st.image(st.session_state.enhanced_img, use_container_width=True)
                st.download_button(
                    "⬇️ Download enhanced",
                    image_to_bytes(st.session_state.enhanced_img),
                    "safescan_enhanced.png", "image/png", key="dl_enh",
                )
                if st.session_state.applied_steps:
                    with st.expander("Enhancement steps applied"):
                        for s in st.session_state.applied_steps:
                            st.markdown(f"- {s}")
            else:
                st.info("Click **Enhance Image** to apply pre-processing, then run OCR.")

        st.markdown("---")

        ocr_src = st.radio(
            "Run OCR on:",
            ["enhanced", "original"],
            format_func=lambda x: "Enhanced image" if x == "enhanced" else "Original image",
            horizontal=True, key="ocr_source",
            disabled=st.session_state.enhanced_img is None,
        )

        run_ocr_btn = st.button("🔍 Extract Text (OCR)", key="btn_ocr", type="primary")

        if run_ocr_btn:
            ocr_img = (
                st.session_state.enhanced_img
                if ocr_src == "enhanced" and st.session_state.enhanced_img is not None
                else orig_img
            )
            try:
                with st.spinner("Running OCR engine (PaddleOCR → EasyOCR fallback)…"):
                    raw_bytes   = image_to_bytes(ocr_img)
                    ocr_raw, engine = run_ocr_engine(raw_bytes)

                # Spatial line reconstruction — preserves multi-word phrases
                recon = reconstruct_lines_from_bbox(ocr_raw, min_confidence=0.35)

                st.session_state.ocr_raw_detail     = ocr_raw
                st.session_state.ocr_reconstruction = recon
                st.session_state.ocr_extracted      = recon["full_text"]
                st.session_state.ocr_engine         = engine
                st.session_state.ocr_mean_conf      = recon["mean_conf"]

                st.success(
                    f"**{engine}** extracted **{recon['total_tokens']}** text regions "
                    f"(mean confidence **{recon['mean_conf']:.0%}**). "
                    f"{recon['rejected_low_conf']} low-confidence tokens discarded."
                )

            except Exception as e:
                st.error(f"OCR failed: {e}")

        # Show raw OCR detail
        if st.session_state.get("ocr_raw_detail"):
            with st.expander(
                f"Raw OCR output — {st.session_state.get('ocr_engine','?')} "
                f"({len(st.session_state.ocr_raw_detail)} regions)",
                expanded=False,
            ):
                for bbox, txt, conf in sorted(
                    st.session_state.ocr_raw_detail, key=lambda r: r[2], reverse=True
                ):
                    filled = int(conf * 20)
                    bar    = "█" * filled + "░" * (20 - filled)
                    icon   = "🟢" if conf > 0.8 else "🟡" if conf > 0.5 else "🔴"
                    st.markdown(f"{icon} `{txt}` &nbsp; {conf:.0%} `{bar}`")

        # Reconstructed / editable text
        if st.session_state.get("ocr_extracted"):
            st.markdown("##### Reconstructed text (edit to fix OCR mistakes)")
            engine_tag = st.session_state.get("ocr_engine", "")
            mean_c     = st.session_state.get("ocr_mean_conf", 0.0)
            st.markdown(
                f'<span class="ocr-badge">📷 {engine_tag}</span> &nbsp; '
                f'<span class="ocr-badge">confidence {mean_c:.0%}</span>',
                unsafe_allow_html=True,
            )
            ocr_final_text = st.text_area(
                label="Reconstructed OCR text",
                value=st.session_state.ocr_extracted,
                height=150,
                key="ocr_edit",
                label_visibility="collapsed",
            )
            is_ocr_mode = True

# ════════════════════════════════════════════════════════════════════════════════
# Analysis controls
# ════════════════════════════════════════════════════════════════════════════════
st.markdown("---")
ctrl1, ctrl2, ctrl3 = st.columns([2, 1, 1])
with ctrl1:
    product_name = st.text_input(
        "Product Name (optional)", placeholder="e.g. Chocolate Cookie",
        key="product_name",
    )
with ctrl2:
    profile_key = st.selectbox(
        "Safety Profile",
        options=list(PROFILES.keys()),
        format_func=lambda x: PROFILES[x],
        key="profile",
    )
with ctrl3:
    st.markdown("<br>", unsafe_allow_html=True)
    analyze_btn = st.button(
        "🛡️ Analyze Ingredients", type="primary", use_container_width=True
    )

active_text = (
    ocr_final_text.strip() if is_ocr_mode and ocr_final_text.strip()
    else raw_text_input.strip()
)

# ════════════════════════════════════════════════════════════════════════════════
# Results
# ════════════════════════════════════════════════════════════════════════════════
if analyze_btn:
    if not active_text:
        st.warning("Please paste an ingredient list or run OCR on a label photo first.")
    else:
        with st.spinner("Running ingredient analysis pipeline…"):
            result = analyze_ingredients(active_text, profile_key, is_ocr=is_ocr_mode)

        pname = product_name.strip() or "Untitled Product"
        save_scan(pname, active_text, result["grade"], result["risk_score"], profile_key, result)

        grade       = result["grade"]
        risk_score  = result["risk_score"]
        tier_counts = result["tier_counts"]
        groups      = result["groups"]
        rejected    = result["rejected"]
        child_warns = result["child_warnings"]
        avg_conf    = result["avg_confidence"]
        ocr_stats   = result.get("ocr_stats")

        st.markdown("---")
        st.subheader("Analysis Results")

        # ── Metrics row ────────────────────────────────────────────────────────
        mc1, mc2, mc3, mc4, mc5, mc6, mc7 = st.columns(7)
        mc1.metric("Grade",            f"{GRADE_ICON.get(grade,'')} {grade}")
        mc2.metric("Risk Score",       f"{risk_score}/100")
        mc3.metric("🔴 High Concern",  tier_counts.get("high_concern", 0))
        mc4.metric("🟠 Moderate",      tier_counts.get("moderate_concern", 0))
        mc5.metric("🟡 Low Concern",   tier_counts.get("low_concern", 0))
        mc6.metric("🟢 Safe",          tier_counts.get("safe", 0))
        mc7.metric("DB Confidence",    f"{avg_conf:.0%}")

        # ── Grade banner ───────────────────────────────────────────────────────
        grade_descs = {
            "A": "Excellent — mostly safe, well-known ingredients.",
            "B": "Good — minor concerns; a few low-concern additives.",
            "C": "Fair — moderate-concern ingredients detected.",
            "D": "Poor — several high-concern or controversial ingredients.",
            "F": "Dangerous — multiple high-concern ingredients found. Avoid.",
        }
        banner_fn = {"A": st.success, "B": st.info, "C": st.warning,
                     "D": st.warning, "F": st.error}
        banner_fn.get(grade, st.info)(
            f"**{GRADE_ICON.get(grade,'')} Grade {grade}** — {grade_descs.get(grade,'')}"
        )

        # ── OCR pipeline report ────────────────────────────────────────────────
        if ocr_stats:
            with st.expander("🔬 OCR extraction pipeline report", expanded=False):
                r1, r2, r3 = st.columns(3)
                r1.metric("Ingredient section",  "Found" if ocr_stats["section_found"] else "Not found (full text)")
                r2.metric("Section confidence",  f"{ocr_stats['section_confidence']:.0%}")
                r3.metric("Noise items removed", ocr_stats["noise_removed"])
                if ocr_stats.get("start_keyword"):
                    st.markdown(f"**Start trigger:** `{ocr_stats['start_keyword']}`")
                if ocr_stats.get("stop_keyword"):
                    st.markdown(f"**Stop trigger:** `{ocr_stats['stop_keyword']}`")
                rs = ocr_stats.get("removal_stats", {})
                if any(rs.values()):
                    cols = st.columns(4)
                    for i, (cat, cnt) in enumerate(
                        [(k, v) for k, v in rs.items() if v]
                    ):
                        cols[i % 4].metric(cat.replace("_", " ").title(), cnt)
                if ocr_stats.get("cleaned_text"):
                    with st.expander("Cleaned text sent to analyzer"):
                        st.code(ocr_stats["cleaned_text"], language=None)

        # ── Child safety panel ─────────────────────────────────────────────────
        if profile_key == "children" and child_warns:
            st.markdown("### 👶 Child Safety Warnings")
            st.error(
                f"**{len(child_warns)} ingredient(s) flagged for children** — "
                "associated with hyperactivity, developmental concerns, or banned "
                "in children's products in some countries."
            )
            for cw in child_warns:
                st.markdown(f"- **{cw['name']}**: {cw['warning']}")
        elif child_warns:
            with st.expander(f"👶 Child safety notes ({len(child_warns)} ingredients)"):
                for cw in child_warns:
                    st.markdown(f"- **{cw['name']}**: {cw['warning']}")

        # ── Grouped ingredient breakdown ───────────────────────────────────────
        st.markdown("### Ingredient Breakdown")

        for tier_key in TIER_ORDER:
            items = groups.get(tier_key, [])
            if not items:
                continue
            tier_cfg = TIERS[tier_key]
            badge    = f'<span class="{TIER_CSS_CLASS[tier_key]}">{tier_cfg["icon"]} {tier_cfg["label"]}</span>'
            header   = f"{tier_cfg['icon']} {tier_cfg['label']} — {len(items)} ingredient(s)"
            expand_default = tier_key in ("high_concern", "moderate_concern")

            with st.expander(header, expanded=expand_default):
                for item in items:
                    conf        = item.get("confidence", 0.0)
                    conf_pct    = int(conf * 100)
                    bar_color   = CONF_BAR_COLOR.get(tier_key, "#6b7280")
                    src_tag     = {
                        "code_table": "🏷️ additive code",
                        "db_fuzzy":   "🗄️ database",
                        "none":       "❓ unmatched",
                    }.get(item.get("match_source", "none"), "")

                    name_disp   = item["name"] if item["matched"] else item["raw"]
                    code_str    = f" `{item['code']}`" if item.get("code") else ""
                    tier_badge  = (
                        f'<span class="{TIER_CSS_CLASS[tier_key]}">'
                        f'{tier_cfg["icon"]} {tier_cfg["label"]}</span>'
                    )

                    st.markdown(
                        f"**{name_disp}**{code_str} &nbsp; {tier_badge}",
                        unsafe_allow_html=True,
                    )

                    col_a, col_b = st.columns([1, 1])
                    with col_a:
                        if item.get("category"):
                            st.caption(f"Category: {item['category']}")
                        if item.get("code"):
                            st.caption(f"Code: `{item['code']}`")
                        # Confidence bar
                        st.markdown(
                            f'<div style="font-size:0.72rem;color:#8b949e;">'
                            f'Match: {src_tag} &nbsp;|&nbsp; '
                            f'Confidence: {conf_pct}%</div>'
                            f'<div class="conf-bar-wrap">'
                            f'<div class="conf-bar-fill" style="width:{conf_pct}%;'
                            f'background:{bar_color};"></div></div>',
                            unsafe_allow_html=True,
                        )
                    with col_b:
                        if item.get("description"):
                            st.markdown(f"ℹ️ {item['description']}")
                        if item.get("warning"):
                            if tier_key == "high_concern":
                                st.error(item["warning"])
                            elif tier_key == "moderate_concern":
                                st.warning(item["warning"])
                            else:
                                st.info(item["warning"])
                        if item.get("child_warning") and profile_key == "children":
                            st.error(f"👶 {item['child_warning']}")
                        if not item["matched"]:
                            st.caption(
                                "⚠️ Not found in verified database — "
                                "cannot assess risk. Check label manually."
                            )

                    st.markdown(
                        '<hr style="border-color:#21262d;margin:6px 0;">',
                        unsafe_allow_html=True,
                    )

        # ── Rejected / filtered tokens ─────────────────────────────────────────
        if rejected:
            with st.expander(
                f"🗑️ Filtered-out tokens ({len(rejected)}) — noise, hallucination guards, short words"
            ):
                st.caption(
                    "These were detected in the raw text but discarded by the "
                    "validation and anti-hallucination pipeline."
                )
                for r in rejected[:50]:
                    st.markdown(f"- `{r['token']}` — *{r['reason']}*")
