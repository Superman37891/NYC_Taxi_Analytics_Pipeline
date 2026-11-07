import os
import pandas as pd
from pyathena import connect
from src.etl.process_taxi_data import write_parquet_to_s3
import src.analytics.queries as queries
from src.utils.s3_client import get_s3_client
import src.config as config

s3 = get_s3_client()
BUCKET = config.YELLOW_TAXI_BUCKET_NAME

YELLOW_TAXI_DASHBOARD_BASE_DIR = config.YELLOW_TAXI_DASHBOARD_BASE_DIR

def get_athena_connection():
    return connect(
        s3_staging_dir=os.environ["YELLOW_TAXI_S3_STAGING_DIR"],
        region_name=os.environ["YELLOW_TAXI_AWS_REGION"],
        schema_name = os.environ["YELLOW_TAXI_DATABASE"]
    )

def run_and_save(query: str, s3_path: str, connection):
    df = pd.read_sql(query, connection)
    # normalize column names
    df.columns = df.columns.str.lower()
    write_parquet_to_s3(df, s3_path)
    print(f"Wrote {len(df)} rows → {s3_path}")

def precompute_dashboard_metrics():
    db = os.environ.get("YELLOW_TAXI_DATABASE")
    print(f"YELLOW_TAXI_DATABASE: '{db}'")
    print(f"Length: {len(db) if db else 0}")
    conn = get_athena_connection()

    # 1. Available years
    run_and_save(queries.AVAILABLE_YEARS_QUERY, f"{YELLOW_TAXI_DASHBOARD_BASE_DIR}/available_years.parquet", conn)

    # 2. Overall monthly summary
    run_and_save(queries.KPI_OVERALL_MONTHLY_SUMMARY_QUERY, f"{YELLOW_TAXI_DASHBOARD_BASE_DIR}/monthly_summary_overall.parquet", conn)

    # 3. Overall payment + hourly
    run_and_save(queries.KPI_OVERALL_PAYMENT_TYPE_SUMMARY_QUERY, f"{YELLOW_TAXI_DASHBOARD_BASE_DIR}/payment_summary_overall.parquet", conn)
    run_and_save(queries.OVERALL_HOURLY_TRIPS_QUERY, f"{YELLOW_TAXI_DASHBOARD_BASE_DIR}/hourly_summary_overall.parquet", conn)

    print("Dashboard pre-compute finished")