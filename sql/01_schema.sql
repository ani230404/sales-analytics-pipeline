-- Star Schema Definition for Commercial Sales Warehouse

CREATE TABLE IF NOT EXISTS dim_territory (
    territory_id VARCHAR PRIMARY KEY,
    region_name VARCHAR NOT NULL,
    country VARCHAR NOT NULL,
    tier VARCHAR NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_rep (
    rep_id VARCHAR PRIMARY KEY,
    rep_name VARCHAR NOT NULL,
    territory_id VARCHAR REFERENCES dim_territory(territory_id),
    hire_date DATE NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_product (
    product_id VARCHAR PRIMARY KEY,
    product_name VARCHAR NOT NULL,
    category VARCHAR NOT NULL,
    unit_cost DOUBLE NOT NULL,
    list_price DOUBLE NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_date (
    date_id INT PRIMARY KEY,
    calendar_date DATE UNIQUE NOT NULL,
    year INT NOT NULL,
    quarter INT NOT NULL,
    month INT NOT NULL,
    month_name VARCHAR NOT NULL
);

CREATE TABLE IF NOT EXISTS fact_quotas (
    quota_id VARCHAR PRIMARY KEY,
    territory_id VARCHAR REFERENCES dim_territory(territory_id),
    year INT NOT NULL,
    quarter INT NOT NULL,
    target_revenue DOUBLE NOT NULL
);

CREATE TABLE IF NOT EXISTS fact_sales (
    sale_id VARCHAR PRIMARY KEY,
    date_id INT REFERENCES dim_date(date_id),
    rep_id VARCHAR REFERENCES dim_rep(rep_id),
    territory_id VARCHAR REFERENCES dim_territory(territory_id),
    product_id VARCHAR REFERENCES dim_product(product_id),
    quantity_sold INT NOT NULL,
    unit_sale_price DOUBLE NOT NULL,
    gross_revenue DOUBLE NOT NULL,
    discount_pct DOUBLE NOT NULL,
    net_revenue DOUBLE NOT NULL,
    total_cost DOUBLE NOT NULL,
    net_margin DOUBLE NOT NULL
);

CREATE TABLE IF NOT EXISTS rejected_records (
    record_id VARCHAR,
    raw_payload VARCHAR,
    rejection_reason VARCHAR,
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);