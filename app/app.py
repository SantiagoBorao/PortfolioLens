import streamlit as st
import snowflake.connector
import pandas as pd
import plotly.express as px
from dotenv import load_dotenv
import os

load_dotenv()

st.set_page_config(page_title="PortfolioLens", page_icon="📊", layout="wide")


@st.cache_resource
def get_connection():
    return snowflake.connector.connect(
        user=os.getenv("SNOWFLAKE_USER"),
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE", "PORTFOLIOLENS_WH"),
        database="PORTFOLIOLENS_DBT",
        schema="MART",
    )


@st.cache_data(ttl=3600)
def load_data():
    conn = get_connection()
    metrics = pd.read_sql("SELECT * FROM METRICS_PORTFOLIO_PERFORMANCE", conn)
    returns = pd.read_sql(
        """
        SELECT PRICE_DATE, PORTFOLIO_ID, TOTAL_PORTFOLIO_VALUE, CUMULATIVE_RETURN
        FROM FACT_PORTFOLIO_POSITIONS
        GROUP BY PRICE_DATE, PORTFOLIO_ID, TOTAL_PORTFOLIO_VALUE, CUMULATIVE_RETURN
        ORDER BY PORTFOLIO_ID, PRICE_DATE
        """,
        conn,
    )
    allocation = pd.read_sql(
        """
        SELECT PORTFOLIO_ID, ASSET_ID, AVG(WEIGHT_PCT) AS WEIGHT_PCT
        FROM FACT_PORTFOLIO_POSITIONS
        WHERE PRICE_DATE = (SELECT MAX(PRICE_DATE) FROM FACT_PORTFOLIO_POSITIONS)
        GROUP BY PORTFOLIO_ID, ASSET_ID
        """,
        conn,
    )
    return metrics, returns, allocation


st.title("📊 PortfolioLens")
st.caption("Snowflake · dbt · Airflow · Streamlit")

try:
    metrics, returns, allocation = load_data()
except Exception as e:
    st.error(f"Snowflake connection error: {e}")
    st.stop()

# ── KPI cards ────────────────────────────────────────────────
st.subheader("Portfolio Overview")
cols = st.columns(len(metrics))

for i, (_, row) in enumerate(metrics.iterrows()):
    with cols[i]:
        ret_pct = round(float(row["TOTAL_RETURN"]) * 100, 2)
        sharpe  = round(float(row["SHARPE_RATIO"]), 2) if pd.notna(row["SHARPE_RATIO"]) else "N/A"
        vol     = round(float(row["ANNUAL_VOLATILITY"]) * 100, 2)
        st.metric(
            label=row["PORTFOLIO_NAME"],
            value=f"${float(row['CURRENT_VALUE']):,.0f}",
            delta=f"{ret_pct:+.2f}% total return",
        )
        st.caption(f"Sharpe {sharpe}  ·  Volatility {vol}%  ·  vs {row['BENCHMARK_TICKER']}")

st.divider()

# ── Cumulative return chart ───────────────────────────────────
st.subheader("Cumulative Returns")
returns["CUMULATIVE_RETURN_PCT"] = returns["CUMULATIVE_RETURN"] * 100

fig = px.line(
    returns,
    x="PRICE_DATE",
    y="CUMULATIVE_RETURN_PCT",
    color="PORTFOLIO_ID",
    labels={
        "CUMULATIVE_RETURN_PCT": "Return (%)",
        "PRICE_DATE": "Date",
        "PORTFOLIO_ID": "Portfolio",
    },
    color_discrete_map={
        "conservative": "#2196F3",
        "moderate":     "#4CAF50",
        "aggressive":   "#F44336",
    },
)
fig.update_layout(hovermode="x unified", legend_title_text="Portfolio")
st.plotly_chart(fig, use_container_width=True)

st.divider()

# ── Allocation + risk/return ──────────────────────────────────
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Current Allocation")
    selected = st.selectbox("Portfolio", metrics["PORTFOLIO_ID"].str.lower().tolist())
    alloc = allocation[allocation["PORTFOLIO_ID"].str.lower() == selected.lower()]
    fig2 = px.pie(alloc, names="ASSET_ID", values="WEIGHT_PCT", hole=0.4)
    st.plotly_chart(fig2, use_container_width=True)

with col_right:
    st.subheader("Risk vs Return")
    scatter = metrics.copy()
    scatter["VOL_PCT"]    = scatter["ANNUAL_VOLATILITY"] * 100
    scatter["RETURN_PCT"] = scatter["TOTAL_RETURN"] * 100
    fig3 = px.scatter(
        scatter,
        x="VOL_PCT",
        y="RETURN_PCT",
        text="RISK_PROFILE",
        labels={"VOL_PCT": "Annual Volatility (%)", "RETURN_PCT": "Total Return (%)"},
    )
    fig3.update_traces(textposition="top center", marker_size=16)
    st.plotly_chart(fig3, use_container_width=True)

# ── Detailed metrics table ────────────────────────────────────
st.subheader("Detailed Metrics")
disp = metrics[["PORTFOLIO_NAME", "RISK_PROFILE", "TOTAL_RETURN",
                "SHARPE_RATIO", "ANNUAL_VOLATILITY", "START_DATE", "END_DATE"]].copy()
disp["TOTAL_RETURN"]      = disp["TOTAL_RETURN"].map(lambda x: f"{float(x)*100:.2f}%")
disp["ANNUAL_VOLATILITY"] = disp["ANNUAL_VOLATILITY"].map(lambda x: f"{float(x)*100:.2f}%")
disp["SHARPE_RATIO"]      = disp["SHARPE_RATIO"].map(
    lambda x: f"{float(x):.2f}" if pd.notna(x) else "N/A"
)
st.dataframe(disp, use_container_width=True, hide_index=True)
