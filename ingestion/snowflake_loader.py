import snowflake.connector
from snowflake.connector.pandas_tools import write_pandas
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()


def get_connection(database=None, schema=None):
    return snowflake.connector.connect(
        user=os.getenv("SNOWFLAKE_USER"),
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE", "PORTFOLIOLENS_WH"),
        database=database or os.getenv("SNOWFLAKE_DATABASE", "PORTFOLIOLENS_RAW"),
        schema=schema or os.getenv("SNOWFLAKE_SCHEMA", "PUBLIC"),
    )


def setup_snowflake():
    conn = snowflake.connector.connect(
        user=os.getenv("SNOWFLAKE_USER"),
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
    )
    cur = conn.cursor()
    statements = [
        "CREATE WAREHOUSE IF NOT EXISTS PORTFOLIOLENS_WH WITH WAREHOUSE_SIZE = 'XSMALL' AUTO_SUSPEND = 300 AUTO_RESUME = TRUE",
        "CREATE DATABASE IF NOT EXISTS PORTFOLIOLENS_RAW",
        "CREATE SCHEMA IF NOT EXISTS PORTFOLIOLENS_RAW.PUBLIC",
        "CREATE DATABASE IF NOT EXISTS PORTFOLIOLENS_DBT",
        "CREATE SCHEMA IF NOT EXISTS PORTFOLIOLENS_DBT.STAGING",
        "CREATE SCHEMA IF NOT EXISTS PORTFOLIOLENS_DBT.MART",
    ]
    for stmt in statements:
        cur.execute(stmt)
        print(f"  OK: {stmt[:70]}...")
    cur.close()
    conn.close()
    print("Snowflake setup complete")


def load_df(df, table, conn):
    df = df.copy()
    df.columns = [c.upper() for c in df.columns]
    success, _, num_rows, _ = write_pandas(
        conn=conn,
        df=df,
        table_name=table.upper(),
        auto_create_table=True,
        overwrite=True,
    )
    status = "OK" if success else "FAILED"
    print(f"  [{status}] {table}: {num_rows} rows")


def run_load():
    print("Setting up Snowflake infrastructure...")
    setup_snowflake()

    conn = get_connection()

    print("Loading prices...")
    load_df(pd.read_csv("data/raw_prices.csv"), "RAW_PRICES", conn)

    print("Loading positions...")
    load_df(pd.read_csv("data/raw_positions.csv"), "RAW_POSITIONS", conn)

    print("Loading portfolio metadata...")
    load_df(pd.read_csv("data/dim_portfolios.csv"), "RAW_PORTFOLIOS", conn)

    conn.close()
    print("All done.")


if __name__ == "__main__":
    run_load()
