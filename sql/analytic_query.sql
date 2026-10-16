-- 1. Territory Quota Attainment & Regional Dense Rank
WITH territory_perf AS (
    SELECT 
        t.region_name,
        t.territory_id,
        d.year,
        d.quarter,
        ROUND(SUM(f.net_revenue), 2) AS actual_revenue
    FROM fact_sales f
    JOIN dim_territory t ON f.territory_id = t.territory_id
    JOIN dim_date d ON f.date_id = d.date_id
    GROUP BY t.region_name, t.territory_id, d.year, d.quarter
)
SELECT 
    p.region_name,
    p.territory_id,
    p.year,
    p.quarter,
    p.actual_revenue,
    q.target_revenue,
    ROUND((p.actual_revenue / NULLIF(q.target_revenue, 0)) * 100, 2) AS attainment_pct,
    DENSE_RANK() OVER (
        PARTITION BY p.year, p.quarter, p.region_name 
        ORDER BY (p.actual_revenue / NULLIF(q.target_revenue, 0)) DESC
    ) AS regional_rank
FROM territory_perf p
LEFT JOIN fact_quotas q 
    ON p.territory_id = q.territory_id 
   AND p.year = q.year 
   AND p.quarter = q.quarter
ORDER BY p.year, p.quarter, p.region_name, regional_rank;

-- 2. Monthly Revenue Velocity, MoM Growth % and Rolling 3-Month Average
WITH monthly_metrics AS (
    SELECT 
        d.year,
        d.month,
        d.month_name,
        ROUND(SUM(f.net_revenue), 2) AS monthly_revenue,
        ROUND(SUM(f.net_margin), 2) AS monthly_margin
    FROM fact_sales f
    JOIN dim_date d ON f.date_id = d.date_id
    GROUP BY d.year, d.month, d.month_name
)
SELECT 
    year,
    month,
    month_name,
    monthly_revenue,
    ROUND(AVG(monthly_revenue) OVER (
        ORDER BY year, month 
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ), 2) AS rolling_3mo_avg_revenue,
    ROUND(
        ((monthly_revenue - LAG(monthly_revenue, 1) OVER (ORDER BY year, month)) 
        / NULLIF(LAG(monthly_revenue, 1) OVER (ORDER BY year, month), 0)) * 100, 
        2
    ) AS mom_growth_pct,
    ROUND((monthly_margin / NULLIF(monthly_revenue, 0)) * 100, 2) AS profit_margin_pct
FROM monthly_metrics
ORDER BY year, month;