"""Main Streamlit application for Ingredient Scanner."""
import streamlit as st
import sys
import os
import json
from datetime import datetime, timedelta
from pathlib import Path
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

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

# Initialize session state
if 'db' not in st.session_state:
    st.session_state.db = SessionLocal()

db = st.session_state.db


def get_grade_color(grade: str) -> str:
    """Get color for grade."""
    colors = {
        "A": "🟢",
        "B": "🟡",
        "C": "🟠",
        "D": "🔴",
        "F": "⚫"
    }
    return colors.get(grade, "⚪")


def save_scan_result(product_name: str, raw_text: str, grade: str, risk_score: float, profile: str, result_json: str):
    """Save scan result to database."""
    try:
        scan_history = models.ScanHistory(
            product_name=product_name,
            raw_text=raw_text,
            grade=grade,
            risk_score=risk_score,
            profile=profile,
            result_json=result_json
        )
        db.add(scan_history)
        db.commit()
        return True
    except Exception as e:
        st.error(f"Error saving scan: {str(e)}")
        return False


# Sidebar Navigation
st.sidebar.title("📋 Navigation")
page = st.sidebar.radio(
    "Select Page",
    ["🏠 Home", "📸 Scan Product", "📊 Dashboard", "📚 Database", "📋 History"]
)

st.sidebar.divider()

# Profile Selection
profile = st.sidebar.selectbox(
    "Select Profile",
    ["General", "Children", "Pregnant", "Elderly", "Allergen Sensitive"]
)

# Main Content
if page == "🏠 Home":
    st.title("🔬 SafeScan - AI Ingredient Scanner")
    st.markdown("""
    Welcome to SafeScan, your AI-powered ingredient scanner. Scan product labels to analyze ingredients
    and get safety assessments based on health profiles.
    
    ### Features:
    - 📸 **Image Scanning**: Upload product images for automatic ingredient extraction
    - 🧪 **Risk Analysis**: Get risk scores and safety grades
    - 👥 **Profile-Specific Analysis**: Customize results for children, pregnant women, elderly, or allergen-sensitive individuals
    - 📊 **Dashboard**: View statistics and trends
    - 📚 **Database**: Browse our comprehensive ingredient database
    - 📋 **History**: Review past scans
    
    ### Tech Stack:
    - **Frontend**: Streamlit
    - **Backend**: Python (FastAPI)
    - **OCR**: PaddleOCR
    - **Database**: SQLite
    - **Visualization**: Plotly
    - **Image Processing**: PIL
    """)

elif page == "📸 Scan Product":
    st.title("📸 Scan Product")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Upload Image")
        uploaded_file = st.file_uploader("Choose a product image", type=["jpg", "jpeg", "png", "gif"])
        
        if uploaded_file:
            st.image(uploaded_file, caption="Uploaded Image", use_column_width=True)
            
            if st.button("🔍 Analyze Product", use_container_width=True):
                with st.spinner("Analyzing image..."):
                    # Save uploaded file temporarily
                    temp_path = f"/tmp/{uploaded_file.name}"
                    with open(temp_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    # Analyze
                    result = analyze_ingredients_from_image(temp_path, profile.lower())
                    
                    # Save to database
                    save_scan_result(
                        product_name=uploaded_file.name,
                        raw_text=result.get("raw_text", ""),
                        grade=result.get("grade", "F"),
                        risk_score=result.get("risk_score", 0.0),
                        profile=profile,
                        result_json=json.dumps(result)
                    )
                    
                    st.success("Analysis complete!")
                    st.session_state.last_result = result
    
    with col2:
        if 'last_result' in st.session_state:
            result = st.session_state.last_result
            st.subheader("📊 Results")
            
            # Grade display
            grade = result.get("grade", "F")
            risk_score = result.get("risk_score", 0.0)
            
            col1a, col1b = st.columns(2)
            with col1a:
                st.metric("Safety Grade", f"{get_grade_color(grade)} {grade}", f"Risk: {risk_score:.1f}/10")
            
            # Matched ingredients
            st.subheader("🧪 Detected Ingredients")
            matched = result.get("matched_ingredients", {})
            
            if matched.get("high_risk"):
                st.error("🚫 **High Risk Ingredients**")
                for ing in matched["high_risk"]:
                    st.write(f"- {ing.get('name', 'Unknown')} (Code: {ing.get('code', 'N/A')})")
            
            if matched.get("medium_risk"):
                st.warning("⚠️ **Medium Risk Ingredients**")
                for ing in matched["medium_risk"]:
                    st.write(f"- {ing.get('name', 'Unknown')} (Code: {ing.get('code', 'N/A')})")
            
            if matched.get("low_risk"):
                st.success("✅ **Low Risk Ingredients**")
                for ing in matched["low_risk"]:
                    st.write(f"- {ing.get('name', 'Unknown')} (Code: {ing.get('code', 'N/A')})")
            
            # Raw text
            with st.expander("📝 Extracted Text"):
                st.text_area("Extracted from image:", result.get("raw_text", ""), height=100)

elif page == "📊 Dashboard":
    st.title("📊 Dashboard")
    
    # Get statistics
    ingredient_count = db.query(models.Ingredient).count()
    scan_count = db.query(models.ScanHistory).count()
    avg_risk = db.query(models.ScanHistory).avg(models.ScanHistory.risk_score)
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Ingredients", ingredient_count)
    with col2:
        st.metric("Total Scans", scan_count)
    with col3:
        st.metric("Avg Risk Score", f"{avg_risk or 0:.1f}")
    with col4:
        high_risk_count = db.query(models.ScanHistory).filter(
            models.ScanHistory.grade.in_(["D", "F"])
        ).count()
        st.metric("High Risk Scans", high_risk_count)
    
    st.divider()
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Grade Distribution")
        grades = db.query(models.ScanHistory.grade, models.ScanHistory.grade).all()
        if grades:
            grade_counts = {}
            for grade, _ in grades:
                grade_counts[grade] = grade_counts.get(grade, 0) + 1
            
            fig = go.Figure(data=[
                go.Pie(labels=list(grade_counts.keys()), values=list(grade_counts.values()),
                       marker=dict(colors=["green", "yellow", "orange", "red", "black"]))
            ])
            fig.update_layout(title="Safety Grades Distribution")
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Risk Score Trend")
        scans = db.query(models.ScanHistory).order_by(models.ScanHistory.created_at).limit(30).all()
        if scans:
            df = pd.DataFrame([
                {"date": s.created_at, "risk_score": s.risk_score}
                for s in scans
            ])
            fig = px.line(df, x="date", y="risk_score", 
                         title="Risk Score Trend (Last 30 scans)",
                         markers=True)
            st.plotly_chart(fig, use_container_width=True)

elif page == "📚 Database":
    st.title("📚 Ingredient Database")
    
    ingredient_db = get_ingredient_database()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("✅ Low Risk")
        low_risk = ingredient_db.get("low_risk", [])
        for ing in low_risk:
            st.write(f"**{ing['name']}** - {ing['code']}")
    
    with col2:
        st.subheader("⚠️ Medium Risk")
        med_risk = ingredient_db.get("medium_risk", [])
        for ing in med_risk:
            st.write(f"**{ing['name']}** - {ing['code']}")
    
    with col3:
        st.subheader("🚫 High Risk")
        high_risk = ingredient_db.get("high_risk", [])
        for ing in high_risk:
            st.write(f"**{ing['name']}** - {ing['code']}")

elif page == "📋 History":
    st.title("📋 Scan History")
    
    # Get recent scans
    scans = db.query(models.ScanHistory).order_by(models.ScanHistory.created_at.desc()).limit(50).all()
    
    if scans:
        # Create dataframe
        data = []
        for scan in scans:
            data.append({
                "Product": scan.product_name,
                "Grade": f"{get_grade_color(scan.grade)} {scan.grade}",
                "Risk Score": f"{scan.risk_score:.1f}",
                "Profile": scan.profile,
                "Date": scan.created_at
            })
        
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True)
        
        # Export option
        if st.button("📥 Export as CSV"):
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"scan_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    else:
        st.info("No scan history yet. Start by scanning a product!")

st.sidebar.divider()
st.sidebar.markdown("---")
st.sidebar.markdown("**SafeScan v1.0**  \n*AI-Powered Ingredient Scanner*")
