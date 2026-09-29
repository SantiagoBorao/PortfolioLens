# PortfolioLens

Portfolio analytics Data Warehouse — Snowflake · dbt · Airflow · Streamlit

Simulates three investment portfolios (conservative, moderate, aggressive) using real
market data from Yahoo Finance, models them in a star schema on Snowflake, and exposes
key performance metrics through an interactive dashboard.

**[Live Demo](#)** · [FinTrack — previous project](https://github.com/SantiagoBorao/fintrack-daas)

---

## What it does

- Downloads daily prices for 14 assets (equities, ETFs, crypto) via Yahoo Finance
- Simulates buy-and-hold positions for 3 portfolios with different risk profiles
- Loads raw data to Snowflake and transforms it with dbt (star schema)
- Calculates: total return, Sharpe Ratio, annual volatility
- Orchestrates the full pipeline with Airflow (runs Mon-Fri after US market close)
- Visualises results in a Streamlit dashboard with Plotly charts

## Architecture

```
Yahoo Finance
     |
     v
ingestion/fetch_prices.py          raw prices for 14 assets
simulation/generate_portfolios.py  buy-and-hold position simulation
     |
     v
Snowflake RAW  (PORTFOLIOLENS_RAW)
  +-- RAW_PRICES
  +-- RAW_POSITIONS
  +-- RAW_PORTFOLIOS
     |
     v  dbt
Snowflake STAGING  (PORTFOLIOLENS_DBT.STAGING)
  +-- stg_prices
  +-- stg_portfolio_positions
     |
     v  dbt
Snowflake MART  (PORTFOLIOLENS_DBT.MART)
  +-- dim_date
  +-- dim_asset
  +-- dim_portfolio
  +-- fact_prices
  +-- fact_portfolio_positions
  +-- metrics_portfolio_performance
     |
     v
airflow/dags/portfoliolens_dag.py  daily orchestration
     |
     v
app/app.py  Streamlit dashboard
```

## Stack

| Layer          | Technology                       |
|----------------|----------------------------------|
| Ingestion      | Python, yfinance                 |
| Warehouse      | Snowflake (XS virtual warehouse) |
| Transformation | dbt                              |
| Orchestration  | Apache Airflow                   |
| Dashboard      | Streamlit, Plotly                |

## Portfolios

| Portfolio    | Risk   | Benchmark | Main assets                        |
|--------------|--------|-----------|------------------------------------|
| Conservative | Low    | AGG       | 50% bonds, 20% SPY, 30% JPM+JNJ   |
| Moderate     | Medium | SPY       | 30% SPY, 30% AAPL+MSFT, 20% AGG   |
| Aggressive   | High   | QQQ       | 40% tech stocks, 25% crypto        |

## Metrics

- **Total Return** — cumulative portfolio return from inception
- **Sharpe Ratio** — (annualised return - 4% risk-free rate) / annual volatility
- **Annual Volatility** — annualised standard deviation of daily returns
- **Asset Allocation** — current weight per position

## Setup

```bash
git clone https://github.com/SantiagoBorao/portfoliolens
cd portfoliolens
python -m venv venv
venv\Scripts\activate      # Windows
pip install -r requirements.txt
cp .env.example .env         # fill in Snowflake credentials
```

### Run manually

```bash
python ingestion/fetch_prices.py
python simulation/generate_portfolios.py
python ingestion/snowflake_loader.py
cd portfoliolens_dbt && dbt run --profiles-dir .
streamlit run app/app.py
```

## Project structure

```
portfoliolens/
+-- ingestion/
|   +-- fetch_prices.py          Yahoo Finance ingestion
|   +-- snowflake_loader.py      Snowflake bulk loader
+-- simulation/
|   +-- generate_portfolios.py   Buy-and-hold position simulation
+-- portfoliolens_dbt/
|   +-- models/
|   |   +-- staging/             Raw -> clean views
|   |   +-- mart/                Star schema + metrics
|   +-- dbt_project.yml
+-- airflow/
|   +-- dags/
|       +-- portfoliolens_dag.py Daily pipeline DAG
+-- app/
|   +-- app.py                   Streamlit dashboard
+-- .env.example
+-- requirements.txt
+-- README.md
```
