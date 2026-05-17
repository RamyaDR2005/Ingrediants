import streamlit as st
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from database import get_dashboard_stats, init_db
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

init_db()

st.set_page_config(page_title="Dashboard — SafeScan", page_icon="📊", layout="wide")

st.title("📊 Safety Dashboard")
st.markdown("Visual overview of ingredient safety data and scan analytics.")

stats = get_dashboard_stats()

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Scans", stats["total_scans"])
with col2:
    risk_dist = stats["risk_dist"]
    st.metric("🔴 High-Risk Ingredients", risk_dist.get("high", 0))
with col3:
    st.metric("🟡 Medium-Risk Ingredients", risk_dist.get("medium", 0))
with col4:
    st.metric("🟢 Low-Risk Ingredients", risk_dist.get("low", 0))

st.markdown("---")

row1_col1, row1_col2 = st.columns(2)

with row1_col1:
    st.subheader("Risk Distribution")
    if stats["risk_dist"]:
        labels = []
        values = []
        colors = {"low": "#22c55e", "medium": "#eab308", "high": "#ef4444", "unknown": "#94a3b8"}
        color_list = []
        for level, count in stats["risk_dist"].items():
            labels.append(level.capitalize())
            values.append(count)
            color_list.append(colors.get(level, "#94a3b8"))
        fig = px.pie(
            names=labels, values=values,
            color=labels,
            color_discrete_map={l: colors.get(l.lower(), "#94a3b8") for l in labels},
            title="Ingredients by Risk Level",
            hole=0.4,
        )
        fig.update_traces(textposition="inside", textinfo="percent+label")
        fig.update_layout(margin=dict(t=40, b=0, l=0, r=0), showlegend=True)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No ingredient data yet.")

with row1_col2:
    st.subheader("Scan Grades")
    if stats["grade_dist"]:
        grade_order = ["A", "B", "C", "D", "F"]
        grade_colors = {"A": "#22c55e", "B": "#84cc16", "C": "#eab308", "D": "#f97316", "F": "#ef4444"}
        grades = [g for g in grade_order if g in stats["grade_dist"]]
        counts = [stats["grade_dist"][g] for g in grades]
        colors_list = [grade_colors.get(g, "#94a3b8") for g in grades]
        fig = go.Figure(data=[
            go.Bar(x=grades, y=counts, marker_color=colors_list, text=counts, textposition="outside")
        ])
        fig.update_layout(
            title="Scans by Grade",
            xaxis_title="Grade",
            yaxis_title="Number of Scans",
            margin=dict(t=40, b=20, l=20, r=20),
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No scan history yet. Run some scans to see grade distribution.")

row2_col1, row2_col2 = st.columns(2)

with row2_col1:
    st.subheader("Top Ingredient Categories")
    if stats["categories"]:
        df_cat = pd.DataFrame(stats["categories"], columns=["Category", "Count"])
        fig = px.bar(
            df_cat, x="Count", y="Category", orientation="h",
            color="Count", color_continuous_scale="RdYlGn_r",
            title="Ingredients per Category",
        )
        fig.update_layout(margin=dict(t=40, b=20, l=20, r=20), coloraxis_showscale=False)
        fig.update_traces(texttemplate="%{x}", textposition="outside")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No category data.")

with row2_col2:
    st.subheader("Most Scanned Ingredients")
    if stats["top_matched"]:
        risk_colors = {"low": "#22c55e", "medium": "#eab308", "high": "#ef4444", "unknown": "#94a3b8"}
        df_top = pd.DataFrame(stats["top_matched"], columns=["Ingredient", "Risk Level", "Match Count"])
        df_top = df_top.sort_values("Match Count", ascending=True)
        colors = [risk_colors.get(rl, "#94a3b8") for rl in df_top["Risk Level"]]
        fig = go.Figure(data=[
            go.Bar(
                x=df_top["Match Count"],
                y=df_top["Ingredient"],
                orientation="h",
                marker_color=colors,
                text=df_top["Match Count"],
                textposition="outside",
            )
        ])
        fig.update_layout(
            title="Top Matched Ingredients",
            xaxis_title="Times Scanned",
            margin=dict(t=40, b=20, l=20, r=20),
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Run some ingredient scans to see what appears most frequently.")

if stats["recent_scores"]:
    st.markdown("---")
    st.subheader("Recent Risk Scores")
    df_scores = pd.DataFrame({
        "Scan": list(range(len(stats["recent_scores"]), 0, -1)),
        "Risk Score": stats["recent_scores"],
    })
    fig = px.line(
        df_scores, x="Scan", y="Risk Score",
        title="Risk Score Trend (Recent Scans)",
        markers=True,
        color_discrete_sequence=["#6366f1"],
    )
    fig.add_hline(y=10, line_dash="dash", line_color="#22c55e", annotation_text="Grade A threshold")
    fig.add_hline(y=25, line_dash="dash", line_color="#eab308", annotation_text="Grade B threshold")
    fig.add_hline(y=45, line_dash="dash", line_color="#f97316", annotation_text="Grade C threshold")
    fig.update_layout(
        xaxis_title="Scan (most recent = 1)",
        yaxis_title="Risk Score (0-100)",
        margin=dict(t=40, b=20, l=20, r=20),
    )
    st.plotly_chart(fig, use_container_width=True)
