"""
End-to-End Orchestrator: Validates incoming raw streams, transforms records,
and loads data into DuckDB warehouse tables.
"""
import os
import duckdb
import pandas as pd
from config import DB_PATH, DATA_DIR, BASE_DIR
from src.validator import validate_and_partition
from src.generator import generate_mock_data

def run_pipeline():
    print(">>> 1. Checking data source...")
    raw_sales_path = os.path.join(DATA_DIR, "raw_sales_stream.csv")
    if not os.path.exists(raw_sales_path):
        print("Raw files missing. Initializing generator...")
        generate_mock_data()

    con = duckdb.connect(DB_PATH)

    print(">>> 2. Initializing warehouse schema...")
    with open(os.path.join(BASE_DIR, "sql", "01_schema.sql"), "r") as f:
        con.execute(f.read())

    print(">>> 3. Cleaning existing records (preserving foreign key constraints)...")
    # Delete child tables first, then parent tables to avoid FK constraint errors
    con.execute("DELETE FROM fact_sales")
    con.execute("DELETE FROM fact_quotas")
    con.execute("DELETE FROM dim_rep")
    con.execute("DELETE FROM dim_territory")
    con.execute("DELETE FROM dim_product")
    con.execute("DELETE FROM dim_date")

    print(">>> 4. Populating Dimension Tables...")
    for dim_name in ["dim_territory", "dim_rep", "dim_product", "dim_date", "fact_quotas"]:
        csv_file = os.path.join(DATA_DIR, f"{dim_name}.csv")
        df_dim = pd.read_csv(csv_file)
        
        con.register("temp_df", df_dim)
        con.execute(f"INSERT INTO {dim_name} SELECT * FROM temp_df")
        con.unregister("temp_df")
        print(f"  Loaded {len(df_dim)} rows into {dim_name}.")

    print(">>> 5. Ingesting & Validating Raw Sales Stream...")
    raw_df = pd.read_csv(raw_sales_path)
    valid_df, rejected_df = validate_and_partition(raw_df)

    print(f"  Valid records: {len(valid_df)} | Rejected anomalies: {len(rejected_df)}")

    # Log rejections into audit table
    if not rejected_df.empty:
        con.register("temp_rejected", rejected_df)
        con.execute("INSERT INTO rejected_records(record_id, raw_payload, rejection_reason) SELECT record_id, raw_payload, rejection_reason FROM temp_rejected")
        con.unregister("temp_rejected")

    # Transform fact sales
    print(">>> 6. Transforming & Calculating Financial Metrics...")
    valid_df["date_id"] = pd.to_datetime(valid_df["date"]).dt.strftime("%Y%m%d").astype(int)

    products_cost = con.execute("SELECT product_id, unit_cost FROM dim_product").fetchdf()
    merged = valid_df.merge(products_cost, on="product_id", how="left")

    merged["gross_revenue"] = merged["quantity_sold"] * merged["unit_sale_price"]
    merged["net_revenue"] = merged["gross_revenue"] * (1.0 - merged["discount_pct"])
    merged["total_cost"] = merged["quantity_sold"] * merged["unit_cost"]
    merged["net_margin"] = merged["net_revenue"] - merged["total_cost"]

    fact_sales_df = merged[[
        "sale_id", "date_id", "rep_id", "territory_id", "product_id",
        "quantity_sold", "unit_sale_price", "gross_revenue", "discount_pct",
        "net_revenue", "total_cost", "net_margin"
    ]]

    con.register("temp_fact_sales", fact_sales_df)
    con.execute("INSERT INTO fact_sales SELECT * FROM temp_fact_sales")
    con.unregister("temp_fact_sales")

    total_sales = con.execute("SELECT COUNT(*) FROM fact_sales").fetchone()[0]
    total_rejections = con.execute("SELECT COUNT(*) FROM rejected_records").fetchone()[0]
    print(f"\nETL Pipeline Execution Succeeded!")
    print(f"Warehouse State: {total_sales} transactions loaded, {total_rejections} flagged records in quarantine.")
    con.close()

if __name__ == "__main__":
    run_pipeline()