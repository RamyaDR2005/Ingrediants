import streamlit as st
import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from database import get_history, get_scan_by_id, delete_scan, init_db

init_db()

st.set_page_config(page_title="Scan History — SafeScan", page_icon="📋", layout="wide")

st.title("📋 Scan History")
st.markdown("Review your past ingredient scans.")

GRADE_COLORS = {"A": "🟢", "B": "🟡", "C": "🟠", "D": "🔴", "F": "⛔"}
RISK_COLORS = {"low": "🟢", "medium": "🟡", "high": "🔴", "unknown": "⚪"}
RISK_LABELS = {"low": "Low", "medium": "Medium", "high": "High", "unknown": "Unknown"}

history = get_history(limit=100)

if not history:
    st.info("No scans yet. Go to the Scanner page to analyze your first product!")
else:
    st.markdown(f"**{len(history)}** scan(s) saved")

    for scan in history:
        grade = scan["grade"]
        icon = GRADE_COLORS.get(grade, "")
        score = scan["risk_score"]
        name = scan["product_name"]
        profile = scan.get("profile", "general") or "general"
        created = scan["created_at"][:16].replace("T", " ")

        with st.expander(f"{icon} **{name}** — Grade {grade} ({score}/100)  ·  {created}  ·  Profile: {profile.capitalize()}"):
            result = None
            if scan.get("result_json"):
                try:
                    result = json.loads(scan["result_json"])
                except Exception:
                    pass

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Grade", f"{icon} {grade}")
            with col2:
                st.metric("Risk Score", f"{score}/100")
            with col3:
                if result:
                    counts = result.get("counts", {})
                    st.metric("High Risk Items", counts.get("high", 0))
            with col4:
                if result:
                    st.metric("Total Ingredients", result.get("total", 0))

            if result and result.get("ingredients"):
                st.markdown("**Ingredients:**")
                for item in result["ingredients"]:
                    rl = item.get("risk_level", "unknown")
                    risk_icon = RISK_COLORS.get(rl, "⚪")
                    label = RISK_LABELS.get(rl, "Unknown")
                    name_disp = item.get("name") or item.get("raw", "")
                    code_str = f" (`{item['code']}`)" if item.get("code") else ""
                    st.markdown(f"  {risk_icon} {name_disp}{code_str} — {label}")

            if scan.get("raw_text"):
                st.markdown("**Raw Text:**")
                st.code(scan["raw_text"][:500] + ("..." if len(scan["raw_text"]) > 500 else ""), language=None)

            if st.button(f"🗑️ Delete this scan", key=f"del_{scan['id']}"):
                delete_scan(scan["id"])
                st.success("Scan deleted.")
                st.rerun()
