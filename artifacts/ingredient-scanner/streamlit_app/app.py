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

st.sidebar.title("🔬 SafeScan")
st.sidebar.markdown("AI-powered ingredient safety analyzer")
st.sidebar.markdown("---")

PROFILES = {
    "general": "General Adult",
    "children": "Children",
    "pregnant": "Pregnant",
    "elderly": "Elderly",
}

GRADE_COLORS = {"A": "🟢", "B": "🟡", "C": "🟠", "D": "🔴", "F": "⛔"}
RISK_COLORS = {"low": "🟢", "medium": "🟡", "high": "🔴", "unknown": "⚪"}
RISK_LABELS = {"low": "Low Risk", "medium": "Medium Risk", "high": "High Risk", "unknown": "Unknown"}

st.title("🔬 Analyze Product Safety")
st.markdown("Paste an ingredient list or upload a product label photo to get instant safety analysis.")

tab_paste, tab_ocr = st.tabs(["📋 Paste Text", "📷 Scan Label (OCR)"])

raw_text = ""

with tab_paste:
    raw_text_input = st.text_area(
        "Ingredient List",
        placeholder="e.g. Water, Sugar, E211, Sodium Benzoate, E102 (Tartrazine), CI 16035, Citric Acid, Natural Flavors...",
        height=180,
        key="paste_input",
    )

with tab_ocr:
    uploaded_file = st.file_uploader(
        "Upload a product label photo",
        type=["jpg", "jpeg", "png", "bmp", "webp"],
        key="ocr_upload",
    )
    ocr_text = ""
    if uploaded_file is not None:
        from PIL import Image
        orig_img = Image.open(uploaded_file)

        st.markdown("#### Image Enhancement Options")
        st.caption("Each step is applied in sequence to maximise OCR accuracy.")

        enh_col1, enh_col2, enh_col3, enh_col4 = st.columns(4)
        with enh_col1:
            do_upscale   = st.checkbox("Resolution upscaling",      value=True, key="enh_upscale")
            do_glare     = st.checkbox("Glare & shadow removal",    value=True, key="enh_glare")
        with enh_col2:
            do_denoise   = st.checkbox("Denoising",                 value=True, key="enh_denoise")
            do_deskew    = st.checkbox("Text straightening",        value=True, key="enh_deskew")
        with enh_col3:
            do_contrast  = st.checkbox("Contrast enhancement",      value=True, key="enh_contrast")
            do_sharpen   = st.checkbox("Sharpening",                value=True, key="enh_sharpen")
        with enh_col4:
            do_background = st.checkbox("Background cleaning",      value=True, key="enh_bg")
            run_enhance  = st.button("✨ Enhance Image",            key="btn_enhance", use_container_width=True)

        steps = {
            "upscale":      do_upscale,
            "glare_shadow": do_glare,
            "denoise":      do_denoise,
            "deskew":       do_deskew,
            "contrast":     do_contrast,
            "sharpen":      do_sharpen,
            "background":   do_background,
        }

        if "enhanced_img" not in st.session_state:
            st.session_state.enhanced_img = None
            st.session_state.applied_steps = []

        if run_enhance:
            with st.spinner("Enhancing image for OCR…"):
                enhanced, applied = enhance_for_ocr(orig_img, steps)
                st.session_state.enhanced_img = enhanced
                st.session_state.applied_steps = applied

        before_col, after_col = st.columns(2)
        with before_col:
            st.markdown("**Original**")
            st.image(orig_img, use_container_width=True)
        with after_col:
            st.markdown("**Enhanced**")
            if st.session_state.enhanced_img is not None:
                st.image(st.session_state.enhanced_img, use_container_width=True)
                st.download_button(
                    label="⬇️ Download enhanced image",
                    data=image_to_bytes(st.session_state.enhanced_img),
                    file_name="safescan_enhanced.png",
                    mime="image/png",
                    key="dl_enhanced",
                )
                if st.session_state.applied_steps:
                    with st.expander("Applied enhancement steps"):
                        for s in st.session_state.applied_steps:
                            st.markdown(f"- {s}")
            else:
                st.info("Click **Enhance Image** to apply processing.")

        st.markdown("---")
        ocr_source = st.radio(
            "Run OCR on:",
            options=["enhanced", "original"],
            format_func=lambda x: "Enhanced image" if x == "enhanced" else "Original image",
            horizontal=True,
            key="ocr_source",
            disabled=st.session_state.enhanced_img is None,
        )

        run_ocr = st.button("🔍 Extract Text (OCR)", key="btn_ocr", type="primary")

        if run_ocr:
            ocr_img = st.session_state.enhanced_img if (ocr_source == "enhanced" and st.session_state.enhanced_img is not None) else orig_img
            try:
                import easyocr
                with st.spinner("Reading text from image with EasyOCR…"):
                    reader = easyocr.Reader(["en"], gpu=False)
                    raw_bytes = image_to_bytes(ocr_img)
                    ocr_results = reader.readtext(raw_bytes, detail=1)

                detected_texts = []
                for (bbox, text, confidence) in ocr_results:
                    if confidence > 0.2:
                        detected_texts.append(text)

                ocr_text = ", ".join(detected_texts)
                st.session_state["ocr_extracted"] = ocr_text

                st.success(f"Extracted {len(detected_texts)} text region(s).")

                with st.expander("Detailed OCR results (text + confidence)", expanded=False):
                    for (bbox, text, confidence) in ocr_results:
                        bar = "█" * int(confidence * 10)
                        st.markdown(f"`{text}` — {confidence:.0%} {bar}")

            except ImportError:
                st.warning("EasyOCR is not installed. Run: `pip install easyocr`")
            except Exception as e:
                st.error(f"OCR failed: {e}")

        if st.session_state.get("ocr_extracted"):
            ocr_text = st.session_state["ocr_extracted"]
            st.text_area("Extracted text (editable — correct any OCR mistakes before analyzing)", ocr_text, height=130, key="ocr_result")

col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    product_name = st.text_input("Product Name (optional)", placeholder="e.g. Chocolate Cookie", key="product_name")
with col2:
    profile_key = st.selectbox("Safety Profile", options=list(PROFILES.keys()), format_func=lambda x: PROFILES[x], key="profile")
with col3:
    st.markdown("<br>", unsafe_allow_html=True)
    analyze_btn = st.button("🛡️ Analyze Ingredients", type="primary", use_container_width=True)

active_text = ocr_text if ocr_text else raw_text_input

if analyze_btn:
    if not active_text.strip():
        st.warning("Please paste an ingredient list or upload a label image.")
    else:
        with st.spinner("Analyzing ingredients..."):
            result = analyze_ingredients(active_text, profile_key)

        grade = result["grade"]
        risk_score = result["risk_score"]
        counts = result["counts"]
        ingredients = result["ingredients"]
        total = result["total"]

        pname = product_name.strip() or "Untitled Product"
        save_scan(pname, active_text, grade, risk_score, profile_key, result)

        st.markdown("---")
        st.subheader("Analysis Results")

        col_grade, col_score, col_high, col_med, col_low, col_unk = st.columns(6)
        with col_grade:
            st.metric("Grade", f"{GRADE_COLORS.get(grade, '')} {grade}")
        with col_score:
            st.metric("Risk Score", f"{risk_score}/100")
        with col_high:
            st.metric("🔴 High Risk", counts["high"])
        with col_med:
            st.metric("🟡 Medium Risk", counts["medium"])
        with col_low:
            st.metric("🟢 Low Risk", counts["low"])
        with col_unk:
            st.metric("⚪ Unknown", counts["unknown"])

        grade_descriptions = {
            "A": "Excellent — mostly safe ingredients.",
            "B": "Good — minor concerns present.",
            "C": "Fair — moderate risk ingredients found.",
            "D": "Poor — several high-risk ingredients.",
            "F": "Dangerous — multiple high-risk ingredients. Avoid.",
        }
        grade_colors_bg = {"A": "success", "B": "info", "C": "warning", "D": "warning", "F": "error"}
        msg_fn = getattr(st, grade_colors_bg.get(grade, "info"))
        msg_fn(f"**{GRADE_COLORS.get(grade, '')} Grade {grade}** — {grade_descriptions.get(grade, '')}")

        st.markdown("### Ingredient Breakdown")

        for item in ingredients:
            rl = item["risk_level"]
            icon = RISK_COLORS.get(rl, "⚪")
            label = RISK_LABELS.get(rl, "Unknown")
            name_display = item["name"] if item["matched"] else item["raw"]

            with st.expander(f"{icon} {name_display}  —  {label}"):
                c1, c2 = st.columns(2)
                with c1:
                    if item.get("code"):
                        st.markdown(f"**Code:** `{item['code']}`")
                    if item.get("category"):
                        st.markdown(f"**Category:** {item['category']}")
                    st.markdown(f"**Risk Level:** {icon} {label}")
                with c2:
                    if item.get("description"):
                        st.markdown(f"**Info:** {item['description']}")
                    if item.get("warning"):
                        st.warning(item["warning"])
                    if not item["matched"]:
                        st.caption("No database match found for this ingredient.")
