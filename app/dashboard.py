"""
Streamlit Executive Dashboard: Real-time visual consumption of warehouse analytics.
Run with: streamlit run app/dashboard.py
"""
import os
import sys
import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Configure layout
st.set_page_config(page_title="Commercial Sales Analytics", layout="wide")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "warehouse.duckdb")

if not os.path.exists(DB_PATH):
    st.error("Warehouse database not detected. Run `python -m src.etl_pipeline` first!")
    st.stop()

@st.cache_data(ttl=60)
def load_data():
    con = duckdb.connect(DB_PATH, read_only=True)
    
    kpis = con.execute("""
        SELECT 
            ROUND(SUM(net_revenue), 2) AS total_revenue,
            ROUND(SUM(net_margin), 2) AS total_margin,
            ROUND(AVG(net_revenue), 2) AS avg_deal_size,
            COUNT(sale_id) AS total_deals
        FROM fact_sales
    """).df().iloc[0]

    monthly = con.execute("""
        SELECT 
            d.year, d.month, d.month_name,
            ROUND(SUM(f.net_revenue), 2) AS revenue,
            ROUND(SUM(f.net_margin), 2) AS margin,
            ROUND(AVG(SUM(f.net_revenue)) OVER (
                ORDER BY d.year, d.month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
            ), 2) AS rolling_3mo_avg
        FROM fact_sales f
        JOIN dim_date d ON f.date_id = d.date_id
        GROUP BY d.year, d.month, d.month_name
        ORDER BY d.year, d.month
    """).df()

    attainment = con.execute("""
        WITH perf AS (
            SELECT 
                t.region_name, t.territory_id, d.year, d.quarter,
                SUM(f.net_revenue) AS actual
            FROM fact_sales f
            JOIN dim_territory t ON f.territory_id = t.territory_id
            JOIN dim_date d ON f.date_id = d.date_id
            GROUP BY t.region_name, t.territory_id, d.year, d.quarter
        )
        SELECT 
            p.region_name, p.territory_id, p.year, p.quarter,
            p.actual, q.target_revenue,
            ROUND((p.actual / NULLIF(q.target_revenue, 0)) * 100, 2) AS attainment_pct
        FROM perf p
        LEFT JOIN fact_quotas q 
            ON p.territory_id = q.territory_id AND p.year = q.year AND p.quarter = q.quarter
    """).df()

    con.close()
    return kpis, monthly, attainment

kpis, monthly_df, attainment_df = load_data()

# Header
st.title("Commercial Sales Intelligence & Territory Performance")
st.caption("Automated DuckDB Analytical Pipeline - Executive View")

# Metric KPI Cards
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Net Revenue", f"${kpis['total_revenue']:,.2f}")
c2.metric("Total Net Margin", f"${kpis['total_margin']:,.2f}")
c3.metric("Profit Margin %", f"{round((kpis['total_margin']/kpis['total_revenue'])*100, 2)}%")
c4.metric("Avg Deal Size", f"${kpis['avg_deal_size']:,.2f}")

st.markdown("---")

col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Monthly Revenue Velocity vs. 3-Month Moving Average")
    monthly_df["Period"] = monthly_df["year"].astype(str) + " - " + monthly_df["month_name"]
    fig_rev = go.Figure()
    fig_rev.add_trace(go.Bar(x=monthly_df["Period"], y=monthly_df["revenue"], name="Net Revenue", marker_color="#2563eb"))
    fig_rev.add_trace(go.Scatter(x=monthly_df["Period"], y=monthly_df["rolling_3mo_avg"], name="3-Mo Rolling Avg", line=dict(color="#dc2626", width=3)))
    fig_rev.update_layout(xaxis_tickangle=-45, legend=dict(orientation="h", y=1.1))
    st.plotly_chart(fig_rev, use_container_width=True)

with col_right:
    st.subheader("Territory Target Attainment %")
    selected_year = st.selectbox("Select Year", options=sorted(attainment_df["year"].unique(), reverse=True))
    filtered_att = attainment_df[attainment_df["year"] == selected_year]
    
    fig_att = px.bar(
        filtered_att, 
        x="territory_id", 
        y="attainment_pct", 
        color="region_name", 
        barmode="group",
        hover_data=["actual", "target_revenue"],
        labels={"attainment_pct": "Attainment %", "territory_id": "Territory"}
    )
    fig_att.add_hline(y=100.0, line_dash="dash", line_color="green", annotation_text="100% Target Met")
    st.plotly_chart(fig_att, use_container_width=True)