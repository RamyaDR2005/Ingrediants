import streamlit as st
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from database import get_all_ingredients, get_categories, init_db

init_db()

st.set_page_config(page_title="Ingredient Database — SafeScan", page_icon="📚", layout="wide")

st.title("📚 Ingredient Database")
st.markdown("Browse and search our database of ingredients with safety ratings.")

RISK_COLORS = {"low": "🟢", "medium": "🟡", "high": "🔴", "unknown": "⚪"}
RISK_LABELS = {"low": "Low", "medium": "Medium", "high": "High", "unknown": "Unknown"}

col1, col2, col3 = st.columns([3, 1, 1])
with col1:
    search = st.text_input("🔍 Search by name, code, or category", placeholder="e.g. Sodium, E211, Colorant", key="db_search")
with col2:
    categories = [""] + get_categories()
    category = st.selectbox("Category", options=categories, format_func=lambda x: x or "All Categories", key="db_cat")
with col3:
    risk_filter = st.selectbox("Risk Level", options=["", "low", "medium", "high"],
                                format_func=lambda x: {"": "All Risks", "low": "🟢 Low", "medium": "🟡 Medium", "high": "🔴 High"}.get(x, x),
                                key="db_risk")

PAGE_SIZE = 25
if "db_page" not in st.session_state:
    st.session_state.db_page = 0

ingredients, total = get_all_ingredients(
    search=search,
    category=category,
    risk=risk_filter,
    limit=PAGE_SIZE,
    offset=st.session_state.db_page * PAGE_SIZE,
)

total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
st.markdown(f"**{total}** ingredients found &nbsp;·&nbsp; Page {st.session_state.db_page + 1} of {total_pages}")

if not ingredients:
    st.info("No ingredients match your search. Try different filters.")
else:
    for ing in ingredients:
        rl = ing.get("risk_level", "unknown")
        icon = RISK_COLORS.get(rl, "⚪")
        label = RISK_LABELS.get(rl, "Unknown")
        code_str = f" (`{ing['code']}`)" if ing.get("code") else ""
        with st.expander(f"{icon} {ing['name']}{code_str}  —  {label} Risk"):
            c1, c2 = st.columns(2)
            with c1:
                if ing.get("code"):
                    st.markdown(f"**Code:** `{ing['code']}`")
                st.markdown(f"**Category:** {ing.get('category') or 'N/A'}")
                st.markdown(f"**Risk Level:** {icon} {label}")
            with c2:
                if ing.get("description"):
                    st.markdown(f"**Description:** {ing['description']}")
                if ing.get("safety_notes"):
                    st.markdown(f"**Safety Notes:** {ing['safety_notes']}")
                if ing.get("profile_flags"):
                    flags = [f.strip() for f in ing["profile_flags"].split(",") if f.strip()]
                    if flags:
                        flag_icons = {"children": "👶", "pregnant": "🤰", "elderly": "👴", "allergen": "⚠️"}
                        flag_strs = [f"{flag_icons.get(f, '•')} {f.capitalize()}" for f in flags]
                        st.markdown(f"**Warnings for:** {', '.join(flag_strs)}")

col_prev, col_info, col_next = st.columns([1, 3, 1])
with col_prev:
    if st.button("← Previous", disabled=st.session_state.db_page == 0):
        st.session_state.db_page -= 1
        st.rerun()
with col_next:
    if st.button("Next →", disabled=st.session_state.db_page >= total_pages - 1):
        st.session_state.db_page += 1
        st.rerun()
