import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from database import init_db, save_scan
from scan_engine import analyze_ingredients

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
        import io
        img = Image.open(uploaded_file)
        st.image(img, caption="Uploaded label", use_container_width=True)

        try:
            import easyocr
            with st.spinner("Reading text from image..."):
                reader = easyocr.Reader(["en"], gpu=False)
                img_bytes = io.BytesIO()
                img.save(img_bytes, format="PNG")
                result = reader.readtext(img_bytes.getvalue(), detail=0)
                ocr_text = ", ".join(result)
                st.success("Text extracted successfully!")
                st.text_area("Extracted Text", ocr_text, height=120, key="ocr_result")
        except ImportError:
            st.warning("EasyOCR is not installed. Please install it with: `pip install easyocr`")
        except Exception as e:
            st.error(f"OCR failed: {e}")

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
