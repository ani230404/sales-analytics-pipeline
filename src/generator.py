"""
Synthesizes seed master dimensions and transactional raw CSV data with realistic edge cases.
"""
import os
import random
from datetime import datetime, timedelta
import pandas as pd
from config import DATA_DIR

def generate_mock_data():
    # 1. Dimensions
    territories = pd.DataFrame([
        {"territory_id": "T01", "region_name": "North America", "country": "USA", "tier": "Tier-1"},
        {"territory_id": "T02", "region_name": "North America", "country": "Canada", "tier": "Tier-2"},
        {"territory_id": "T03", "region_name": "Europe", "country": "UK", "tier": "Tier-1"},
        {"territory_id": "T04", "region_name": "Europe", "country": "Germany", "tier": "Tier-1"},
        {"territory_id": "T05", "region_name": "Asia-Pacific", "country": "India", "tier": "Tier-1"},
        {"territory_id": "T06", "region_name": "Asia-Pacific", "country": "Singapore", "tier": "Tier-2"},
    ])
    territories.to_csv(os.path.join(DATA_DIR, "dim_territory.csv"), index=False)

    reps = pd.DataFrame([
        {"rep_id": "R01", "rep_name": "Sarah Connor", "territory_id": "T01", "hire_date": "2023-01-15"},
        {"rep_id": "R02", "rep_name": "John Miller", "territory_id": "T02", "hire_date": "2023-03-20"},
        {"rep_id": "R03", "rep_name": "Elena Rostova", "territory_id": "T03", "hire_date": "2022-11-01"},
        {"rep_id": "R04", "rep_name": "Lucas Weber", "territory_id": "T04", "hire_date": "2023-05-10"},
        {"rep_id": "R05", "rep_name": "Aarav Sharma", "territory_id": "T05", "hire_date": "2022-08-15"},
        {"rep_id": "R06", "rep_name": "Mei Lin", "territory_id": "T06", "hire_date": "2023-02-01"},
    ])
    reps.to_csv(os.path.join(DATA_DIR, "dim_rep.csv"), index=False)

    products = pd.DataFrame([
        {"product_id": "P01", "product_name": "Enterprise Analytics Suite", "category": "Software", "unit_cost": 250.0, "list_price": 1000.0},
        {"product_id": "P02", "product_name": "Cloud Storage Node", "category": "Infrastructure", "unit_cost": 80.0, "list_price": 320.0},
        {"product_id": "P03", "product_name": "Edge Gateway Pro", "category": "Hardware", "unit_cost": 400.0, "list_price": 1200.0},
        {"product_id": "P04", "product_name": "24/7 Premium Support", "category": "Services", "unit_cost": 50.0, "list_price": 250.0},
    ])
    products.to_csv(os.path.join(DATA_DIR, "dim_product.csv"), index=False)

    quotas = pd.DataFrame([
        {"quota_id": f"Q_{t}_{y}_Q{q}", "territory_id": t, "year": y, "quarter": q, "target_revenue": random.randint(75000, 150000)}
        for t in territories["territory_id"]
        for y in [2025, 2026]
        for q in [1, 2, 3, 4]
    ])
    quotas.to_csv(os.path.join(DATA_DIR, "fact_quotas.csv"), index=False)

    # 2. Date Dimension (2025-01-01 to 2026-12-31)
    date_list = []
    curr = datetime(2025, 1, 1)
    end = datetime(2026, 12, 31)
    while curr <= end:
        date_list.append({
            "date_id": int(curr.strftime("%Y%m%d")),
            "calendar_date": curr.strftime("%Y-%m-%d"),
            "year": curr.year,
            "quarter": (curr.month - 1) // 3 + 1,
            "month": curr.month,
            "month_name": curr.strftime("%b")
        })
        curr += timedelta(days=1)
    pd.DataFrame(date_list).to_csv(os.path.join(DATA_DIR, "dim_date.csv"), index=False)

    # 3. Raw Sales Transactions (with intentionally bad records for validator demonstration)
    transactions = []
    start_date = datetime(2025, 1, 1)
    for i in range(1, 1500):
        sale_dt = start_date + timedelta(days=random.randint(0, 650))
        prod = products.sample(1).iloc[0]
        rep = reps.sample(1).iloc[0]

        sale_record = {
            "sale_id": f"TXN-{10000 + i}",
            "date": sale_dt.strftime("%Y-%m-%d"),
            "rep_id": rep["rep_id"],
            "territory_id": rep["territory_id"],
            "product_id": prod["product_id"],
            "quantity_sold": random.randint(1, 20),
            "unit_sale_price": float(prod["list_price"]),
            "discount_pct": round(random.choice([0.0, 0.05, 0.10, 0.15]), 2)
        }

        # Inject anomalies to test pipeline validation resilience
        if i == 50:
            sale_record["quantity_sold"] = -5  # Negative quantity
        elif i == 120:
            sale_record["unit_sale_price"] = 0.0 # Zero price anomaly
        elif i == 200:
            sale_record["discount_pct"] = 1.85 # Impossible > 100% discount

        transactions.append(sale_record)

    pd.DataFrame(transactions).to_csv(os.path.join(DATA_DIR, "raw_sales_stream.csv"), index=False)
    print(f"Data generation complete: {len(transactions)} transactions created in '{DATA_DIR}'.")

if __name__ == "__main__":
    generate_mock_data()