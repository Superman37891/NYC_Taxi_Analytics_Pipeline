import os
import pandas as pd
from pyathena import connect
import awswrangler as wr
import src.analytics.queries as queries

def get_athena_connection():
    return connect(
        s3_staging_dir=os.environ["YELLOW_TAXI_S3_STAGING_DIR"],
        region_name=os.environ["YELLOW_TAXI_AWS_REGION"],
    )

def run_and_save(query: str, s3_path: str, connection):
    df = pd.read_sql(query, connection)
    # normalize column names
    df.columns = df.columns.str.lower()
    wr.s3.to_parquet(df, s3_path, index=False, dataset=False)
    print(f"Wrote {len(df)} rows → {s3_path}")

def precompute_dashboard_metrics():
    conn = get_athena_connection()
    bucket = os.environ["YELLOW_TAXI_BUCKET_NAME"]
    dashboard_base_dir = os.environ["YELLOW_TAXI_DASHBOARD_BASE_DIR"]

    # 1. Available years
    run_and_save(queries.AVAILABLE_YEARS_QUERY, f"{dashboard_base_dir}/available_years.parquet", conn)

    # 2. Overall monthly summary
    run_and_save(queries.KPI_OVERALL_MONTHLY_SUMMARY_QUERY, f"{dashboard_base_dir}/monthly_summary_overall.parquet", conn)

    # 3. Overall payment + hourly
    run_and_save(queries.KPI_OVERALL_PAYMENT_TYPE_SUMMARY_QUERY, f"{dashboard_base_dir}/payment_summary_overall.parquet", conn)
    run_and_save(queries.OVERALL_HOURLY_TRIPS_QUERY, f"{dashboard_base_dir}/hourly_summary_overall.parquet", conn)

    print("Dashboard pre-compute finished")