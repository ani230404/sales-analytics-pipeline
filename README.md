# Automated Commercial Sales Analytics Pipeline

An end-to-end analytical data engineering pipeline and reporting application built with Python, DuckDB, Pydantic, and Streamlit. The project extracts multi-source sales and territory operations data, enforces strict contract validation, models records into a Star Schema warehouse, runs advanced analytical SQL window functions, and delivers visual KPIs.

## System Architecture

1. **Ingestion & Contract Validation:** Ingests raw sales streams and verifies fields against schema rules using Pydantic. Malformed records are isolated into an audit quarantine table (`rejected_records`).
2. **Analytical Star Schema:** Modeled in DuckDB with optimized Dimension tables (`dim_territory`, `dim_rep`, `dim_product`, `dim_date`) and Fact tables (`fact_sales`, `fact_quotas`).
3. **Advanced SQL Transformations:** Computes territory attainment, Dense Ranking across regions, 3-month rolling averages, and MoM sales growth.
4. **Interactive BI Dashboard:** Streamlit UI displaying financial velocity, margins, and quota pacing charts.

---

## Quickstart

### 1. Clone repository & install dependencies
```bash
git clone [https://github.com/](https://github.com/)<your-username>/sales-analytics-pipeline.git
cd sales-analytics-pipeline
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt