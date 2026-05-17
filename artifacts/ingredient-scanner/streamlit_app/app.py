import streamlit as st
import sys
import os
import io

sys.path.insert(0, os.path.dirname(__file__))

from database import init_db, save_scan
from scan_engine import analyze_ingredients
from image_enhancer import enhance_for_ocr, image_to_bytes

init_db()

st.set_page_config(
    page_title="SafeScan — AI Ingredient Scanner",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Sidebar ────────────────────────────────────────────────────────────────────
st.sidebar.title("🔬 SafeScan")
st.sidebar.markdown("AI-powered ingredient safety analyzer")
st.sidebar.markdown("---")
st.sidebar.caption("v2 · EasyOCR + NLP pipeline")

PROFILES = {
    "general":  "General Adult",
    "children": "Children",
    "pregnant": "Pregnant",
    "elderly":  "Elderly",
}

GROUP_CONFIG = {
    "harmful":  {"label": "Harmful",       "icon": "🔴", "color": "error"},
    "moderate": {"label": "Moderate Risk", "icon": "🟡", "color": "warning"},
    "safe":     {"label": "Safe",          "icon": "🟢", "color": "success"},
    "unknown":  {"label": "Unknown",       "icon": "⚪", "color": "info"},
}
GRADE_ICON = {"A": "🟢", "B": "🟡", "C": "🟠", "D": "🔴", "F": "⛔"}
RISK_ICON  = {"low": "🟢", "medium": "🟡", "high": "🔴", "unknown": "⚪"}

# ── Header ─────────────────────────────────────────────────────────────────────
st.title("🔬 Analyze Product Safety")
st.markdown(
    "Paste an ingredient list or upload a product label photo. "
    "The AI pipeline extracts ingredients, removes OCR noise, and scores each ingredient."
)

tab_paste, tab_ocr = st.tabs(["📋 Paste Text", "📷 Scan Label (OCR)"])

raw_text_input = ""
ocr_text       = ""
is_ocr_mode    = False

# ════════════════════════════════════════════════════════════════════════════════
# TAB 1 — Paste text
# ════════════════════════════════════════════════════════════════════════════════
with tab_paste:
    raw_text_input = st.text_area(
        "Ingredient List",
        placeholder=(
            "e.g. Water, Sugar, E211, Sodium Benzoate, E102 (Tartrazine), "
            "CI 16035, Citric Acid, Natural Flavors, Palm Oil..."
        ),
        height=180,
        key="paste_input",
    )

# ════════════════════════════════════════════════════════════════════════════════
# TAB 2 — OCR
# ════════════════════════════════════════════════════════════════════════════════
with tab_ocr:
    uploaded_file = st.file_uploader(
        "Upload a product label photo",
        type=["jpg", "jpeg", "png", "bmp", "webp"],
        key="ocr_upload",
    )

    if uploaded_file is not None:
        from PIL import Image
        orig_img = Image.open(uploaded_file)

        st.markdown("#### Image Enhancement")
        st.caption("Applied in sequence before OCR to maximize text readability.")

        ec1, ec2, ec3, ec4 = st.columns(4)
        with ec1:
            do_upscale  = st.checkbox("Upscale resolution",    value=True, key="enh_upscale")
            do_glare    = st.checkbox("Glare/shadow removal",  value=True, key="enh_glare")
        with ec2:
            do_denoise  = st.checkbox("Denoising",             value=True, key="enh_denoise")
            do_deskew   = st.checkbox("Text straightening",    value=True, key="enh_deskew")
        with ec3:
            do_contrast = st.checkbox("Contrast (CLAHE)",      value=True, key="enh_contrast")
            do_sharpen  = st.checkbox("Sharpening",            value=True, key="enh_sharpen")
        with ec4:
            do_bg       = st.checkbox("Background cleaning",   value=True, key="enh_bg")
            run_enhance = st.button("✨ Enhance Image", key="btn_enhance", use_container_width=True)

        steps = {
            "upscale": do_upscale, "glare_shadow": do_glare, "denoise": do_denoise,
            "deskew": do_deskew, "contrast": do_contrast, "sharpen": do_sharpen,
            "background": do_bg,
        }

        if "enhanced_img"   not in st.session_state: st.session_state.enhanced_img   = None
        if "applied_steps"  not in st.session_state: st.session_state.applied_steps  = []
        if "ocr_extracted"  not in st.session_state: st.session_state.ocr_extracted  = ""
        if "ocr_raw_detail" not in st.session_state: st.session_state.ocr_raw_detail = []

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
                    "⬇️ Download enhanced", image_to_bytes(st.session_state.enhanced_img),
                    "safescan_enhanced.png", "image/png", key="dl_enh",
                )
                if st.session_state.applied_steps:
                    with st.expander("Applied steps"):
                        for s in st.session_state.applied_steps:
                            st.markdown(f"- {s}")
            else:
                st.info("Click **Enhance Image** to apply processing.")

        st.markdown("---")

        ocr_src = st.radio(
            "Run OCR on:", ["enhanced", "original"],
            format_func=lambda x: "Enhanced image" if x == "enhanced" else "Original image",
            horizontal=True, key="ocr_source",
            disabled=st.session_state.enhanced_img is None,
        )
        run_ocr = st.button("🔍 Extract Text (OCR)", key="btn_ocr", type="primary")

        if run_ocr:
            ocr_img = (
                st.session_state.enhanced_img
                if ocr_src == "enhanced" and st.session_state.enhanced_img is not None
                else orig_img
            )
            try:
                import easyocr
                with st.spinner("Running EasyOCR…"):
                    reader    = easyocr.Reader(["en"], gpu=False)
                    raw_bytes = image_to_bytes(ocr_img)
                    ocr_raw   = reader.readtext(raw_bytes, detail=1)

                # Filter by confidence threshold
                high_conf = [(bbox, txt, conf) for bbox, txt, conf in ocr_raw if conf > 0.25]
                texts     = [txt for _, txt, _ in high_conf]
                mean_conf = sum(c for _, _, c in high_conf) / max(1, len(high_conf))

                st.session_state.ocr_extracted  = "\n".join(texts)
                st.session_state.ocr_raw_detail = ocr_raw
                st.session_state.ocr_mean_conf  = mean_conf

                st.success(
                    f"Extracted **{len(texts)}** text regions — "
                    f"mean OCR confidence **{mean_conf:.0%}**"
                )

            except ImportError:
                st.error("EasyOCR is not installed.")
            except Exception as e:
                st.error(f"OCR failed: {e}")

        if st.session_state.get("ocr_raw_detail"):
            with st.expander("Raw OCR output (all regions + confidence)", expanded=False):
                for _, txt, conf in st.session_state.ocr_raw_detail:
                    bar_filled = int(conf * 20)
                    bar = "█" * bar_filled + "░" * (20 - bar_filled)
                    color = "🟢" if conf > 0.8 else "🟡" if conf > 0.5 else "🔴"
                    st.markdown(f"{color} `{txt}` &nbsp; {conf:.0%} `{bar}`")

        if st.session_state.get("ocr_extracted"):
            ocr_text = st.text_area(
                "Extracted text (edit to correct OCR mistakes before analyzing)",
                value=st.session_state.ocr_extracted,
                height=140, key="ocr_edit",
            )
            is_ocr_mode = True

# ════════════════════════════════════════════════════════════════════════════════
# Analysis controls
# ════════════════════════════════════════════════════════════════════════════════
st.markdown("---")
ctrl1, ctrl2, ctrl3 = st.columns([2, 1, 1])
with ctrl1:
    product_name = st.text_input(
        "Product Name (optional)", placeholder="e.g. Chocolate Cookie", key="product_name"
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
    analyze_btn = st.button("🛡️ Analyze Ingredients", type="primary", use_container_width=True)

active_text = ocr_text.strip() if is_ocr_mode and ocr_text.strip() else raw_text_input.strip()

# ════════════════════════════════════════════════════════════════════════════════
# Analysis + results
# ════════════════════════════════════════════════════════════════════════════════
if analyze_btn:
    if not active_text:
        st.warning("Please paste an ingredient list or run OCR on a label image first.")
    else:
        with st.spinner("Running AI ingredient analysis pipeline…"):
            result = analyze_ingredients(active_text, profile_key, is_ocr=is_ocr_mode)

        pname = product_name.strip() or "Untitled Product"
        save_scan(pname, active_text, result["grade"], result["risk_score"], profile_key, result)

        grade       = result["grade"]
        risk_score  = result["risk_score"]
        counts      = result["counts"]
        groups      = result["groups"]
        rejected    = result["rejected"]
        child_warns = result["child_warnings"]
        avg_conf    = result["avg_confidence"]
        ocr_stats   = result.get("ocr_stats")

        st.markdown("---")
        st.subheader("Analysis Results")

        # ── Top metrics ───────────────────────────────────────────────────────
        m1, m2, m3, m4, m5, m6, m7 = st.columns(7)
        m1.metric("Grade",         f"{GRADE_ICON.get(grade, '')} {grade}")
        m2.metric("Risk Score",    f"{risk_score}/100")
        m3.metric("🔴 Harmful",    counts.get("high", 0))
        m4.metric("🟡 Moderate",   counts.get("medium", 0))
        m5.metric("🟢 Safe",       counts.get("low", 0))
        m6.metric("⚪ Unknown",    counts.get("unknown", 0))
        m7.metric("DB Confidence", f"{avg_conf:.0%}")

        # ── Grade banner ──────────────────────────────────────────────────────
        grade_descs = {
            "A": "Excellent — mostly safe, well-understood ingredients.",
            "B": "Good — minor concerns; a few moderate-risk additives.",
            "C": "Fair — notable moderate/high-risk ingredients present.",
            "D": "Poor — several high-risk or controversial ingredients.",
            "F": "Dangerous — multiple high-risk ingredients. Avoid.",
        }
        fn = {"A": st.success, "B": st.info, "C": st.warning, "D": st.warning, "F": st.error}
        fn.get(grade, st.info)(
            f"**{GRADE_ICON.get(grade,'')} Grade {grade}** — {grade_descs.get(grade,'')}"
        )

        # ── OCR pipeline stats (only for OCR mode) ────────────────────────────
        if ocr_stats:
            with st.expander("OCR extraction pipeline report", expanded=False):
                oc1, oc2, oc3 = st.columns(3)
                oc1.metric("Section detected",  "Yes" if ocr_stats["section_found"] else "No (full text used)")
                oc2.metric("Section confidence", f"{ocr_stats['section_confidence']:.0%}")
                oc3.metric("Noise items removed", ocr_stats["noise_removed"])
                if ocr_stats["start_keyword"]:
                    st.markdown(f"**Start trigger:** `{ocr_stats['start_keyword']}`")
                if ocr_stats["stop_keyword"]:
                    st.markdown(f"**Stop trigger:** `{ocr_stats['stop_keyword']}`")
                rs = ocr_stats.get("removal_stats", {})
                if any(rs.values()):
                    st.markdown("**Removed by category:**")
                    for cat, cnt in rs.items():
                        if cnt:
                            st.markdown(f"  - {cat.replace('_',' ').title()}: **{cnt}**")
                if ocr_stats.get("noise_items"):
                    with st.expander("Removed items detail"):
                        for tok, reason in ocr_stats["noise_items"]:
                            st.markdown(f"  - `{tok}` — *{reason}*")
                if ocr_stats.get("cleaned_text"):
                    with st.expander("Cleaned ingredient text sent to analyzer"):
                        st.code(ocr_stats["cleaned_text"], language=None)

        # ── Child safety panel ────────────────────────────────────────────────
        if profile_key == "children" and child_warns:
            st.markdown("### 👶 Child Safety Warnings")
            st.error(
                f"**{len(child_warns)} ingredient(s) flagged for children** — "
                "these have known associations with hyperactivity, developmental concerns, or are banned in children's products in some countries."
            )
            for cw in child_warns:
                st.markdown(f"- **{cw['name']}**: {cw['warning']}")

        if profile_key != "children" and child_warns:
            with st.expander(f"👶 Child safety notes ({len(child_warns)} items)"):
                for cw in child_warns:
                    st.markdown(f"- **{cw['name']}**: {cw['warning']}")

        # ── Grouped ingredient breakdown ──────────────────────────────────────
        st.markdown("### Ingredient Breakdown")

        GROUP_ORDER = ["harmful", "moderate", "safe", "unknown"]
        for gkey in GROUP_ORDER:
            items = groups.get(gkey, [])
            if not items:
                continue
            cfg   = GROUP_CONFIG[gkey]
            label = f"{cfg['icon']} {cfg['label']} ({len(items)})"

            # Expand harmful + moderate by default
            expand_default = gkey in ("harmful", "moderate")
            with st.expander(label, expanded=expand_default):
                for item in items:
                    conf     = item.get("confidence", 0.0)
                    conf_bar = "█" * int(conf * 10) + "░" * (10 - int(conf * 10))
                    src_tag  = {
                        "code_table": "🏷️ code",
                        "db_fuzzy":   "🗄️ database",
                        "none":       "❓ unmatched",
                    }.get(item.get("match_source", "none"), "")

                    name_disp = item["name"] if item["matched"] else item["raw"]
                    code_str  = f" `{item['code']}`" if item.get("code") else ""
                    risk_icon = RISK_ICON.get(item["risk_level"], "⚪")

                    header = f"{risk_icon} **{name_disp}**{code_str}"
                    with st.container():
                        st.markdown(header)
                        col_a, col_b = st.columns([1, 1])
                        with col_a:
                            if item.get("category"):
                                st.caption(f"Category: {item['category']}")
                            if item.get("code"):
                                st.caption(f"Code: `{item['code']}`")
                            st.caption(
                                f"Match: {src_tag}  |  Confidence: {conf:.0%} `{conf_bar}`"
                            )
                        with col_b:
                            if item.get("description"):
                                st.markdown(f"ℹ️ {item['description']}")
                            if item.get("warning"):
                                if gkey == "harmful":
                                    st.error(item["warning"])
                                elif gkey == "moderate":
                                    st.warning(item["warning"])
                                else:
                                    st.info(item["warning"])
                            if item.get("child_warning") and profile_key == "children":
                                st.error(f"👶 {item['child_warning']}")
                            if not item["matched"]:
                                st.caption("No database match — could not validate this ingredient.")
                        st.markdown("---")

        # ── Rejected tokens ───────────────────────────────────────────────────
        if rejected:
            with st.expander(f"🗑️ Rejected OCR/noise tokens ({len(rejected)})"):
                st.caption(
                    "These tokens were detected in the text but filtered out by the "
                    "noise-removal and validation pipeline."
                )
                for r in rejected[:40]:
                    st.markdown(f"- `{r['token']}` — *{r['reason']}*")
