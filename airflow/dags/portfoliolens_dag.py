from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator

default_args = {
    "owner": "portfoliolens",
    "depends_on_past": False,
    "start_date": datetime(2024, 1, 1),
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "email_on_failure": False,
}

with DAG(
    dag_id="portfoliolens_daily",
    default_args=default_args,
    description="Fetch prices -> simulate positions -> load Snowflake -> run dbt",
    schedule_interval="0 18 * * 1-5",  # 18:00 UTC Mon-Fri (after US market close)
    catchup=False,
    tags=["portfoliolens", "finance"],
) as dag:

    def task_fetch_prices():
        import sys
        sys.path.insert(0, "/opt/airflow")
        from ingestion.fetch_prices import fetch_prices, ASSETS, BENCHMARKS
        import os

        tickers = {**ASSETS, **{k: v for k, v in BENCHMARKS.items() if k not in ASSETS}}
        df = fetch_prices(tickers, years=2)
        os.makedirs("data", exist_ok=True)
        df.to_csv("data/raw_prices.csv", index=False)

    def task_generate_positions():
        import sys
        sys.path.insert(0, "/opt/airflow")
        from simulation.generate_portfolios import generate_positions, generate_dim_portfolio
        import pandas as pd

        prices_df = pd.read_csv("data/raw_prices.csv")
        generate_positions(prices_df).to_csv("data/raw_positions.csv", index=False)
        generate_dim_portfolio().to_csv("data/dim_portfolios.csv", index=False)

    def task_load_snowflake():
        import sys
        sys.path.insert(0, "/opt/airflow")
        from ingestion.snowflake_loader import run_load
        run_load()

    t1 = PythonOperator(task_id="fetch_prices",       python_callable=task_fetch_prices)
    t2 = PythonOperator(task_id="generate_positions", python_callable=task_generate_positions)
    t3 = PythonOperator(task_id="load_to_snowflake",  python_callable=task_load_snowflake)
    t4 = BashOperator(
        task_id="run_dbt",
        bash_command="cd /opt/airflow/portfoliolens_dbt && dbt run --profiles-dir .",
    )

    t1 >> t2 >> t3 >> t4
