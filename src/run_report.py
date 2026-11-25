import os
import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats

RAW_DIR = "data/raw"
OUT_DIR = "outputs"
SQL_DIR = "sql"
DB_PATH = "olist.db"

os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(SQL_DIR, exist_ok=True)

# 1. Load CSVs into SQLite
tables = {
    "orders": "olist_orders_dataset.csv",
    "customers": "olist_customers_dataset.csv",
    "items": "olist_order_items_dataset.csv",
    "payments": "olist_order_payments_dataset.csv",
    "reviews": "olist_order_reviews_dataset.csv",
    "products": "olist_products_dataset.csv",
    "sellers": "olist_sellers_dataset.csv",
    "translation": "product_category_name_translation.csv",
}

conn = sqlite3.connect(DB_PATH)
for name, fname in tables.items():
    df = pd.read_csv(os.path.join(RAW_DIR, fname))
    df.to_sql(name, conn, if_exists="replace", index=False)
print("Loaded all CSVs into SQLite.")

# 2. SQL Queries (CTEs + Window Functions + Safe Pre-Aggregation)
sql_queries = {
    "01_delivery_impact.sql": """
    -- Q3: Compare review scores for On-Time vs Late deliveries (delivered orders only)
    WITH order_reviews_dedup AS (
        SELECT
            order_id,
            AVG(review_score) AS review_score
        FROM reviews
        GROUP BY order_id
    ),
    delivery_status AS (
        SELECT
            o.order_id,
            CASE
                WHEN JULIANDAY(o.order_delivered_customer_date) > JULIANDAY(o.order_estimated_delivery_date)
                THEN 'Late'
                ELSE 'On-Time'
            END AS delivery_flag,
            ROUND(JULIANDAY(o.order_delivered_customer_date) - JULIANDAY(o.order_estimated_delivery_date), 1) AS days_diff,
            r.review_score
        FROM orders o
        JOIN order_reviews_dedup r ON o.order_id = r.order_id
        WHERE o.order_status = 'delivered'
          AND o.order_delivered_customer_date IS NOT NULL
          AND o.order_estimated_delivery_date IS NOT NULL
    )
    SELECT
        delivery_flag,
        COUNT(*) AS order_count,
        ROUND(AVG(review_score), 3) AS avg_review_score,
        ROUND(AVG(days_diff), 2) AS avg_days_vs_estimate
    FROM delivery_status
    GROUP BY delivery_flag;
    """,

    "02_category_revenue_delivery.sql": """
    -- Q4: Top product categories by revenue and average delivery time
    WITH item_orders AS (
        SELECT
            i.order_id,
            COALESCE(t.product_category_name_english, p.product_category_name, 'uncategorized') AS category,
            i.price + i.freight_value AS item_total,
            JULIANDAY(o.order_delivered_customer_date) - JULIANDAY(o.order_purchase_timestamp) AS delivery_days,
            CASE
                WHEN JULIANDAY(o.order_delivered_customer_date) > JULIANDAY(o.order_estimated_delivery_date) THEN 1.0
                ELSE 0.0
            END AS is_late
        FROM items i
        JOIN orders o ON i.order_id = o.order_id
        LEFT JOIN products p ON i.product_id = p.product_id
        LEFT JOIN translation t ON p.product_category_name = t.product_category_name
        WHERE o.order_status = 'delivered'
          AND o.order_delivered_customer_date IS NOT NULL
    )
    SELECT
        category,
        COUNT(DISTINCT order_id) AS orders,
        ROUND(SUM(item_total), 2) AS total_revenue,
        ROUND(AVG(delivery_days), 1) AS avg_delivery_days,
        ROUND(AVG(is_late) * 100, 1) AS late_pct
    FROM item_orders
    GROUP BY category
    HAVING orders >= 100
    ORDER BY total_revenue DESC
    LIMIT 15;
    """,

    "03_high_sales_poor_sellers.sql": """
    -- Q5: High-volume sellers ranked by worst review scores using window functions
    WITH seller_metrics AS (
        SELECT
            i.seller_id,
            s.seller_state,
            COUNT(DISTINCT i.order_id) AS total_orders,
            ROUND(SUM(i.price), 2) AS gross_sales,
            ROUND(AVG(r.review_score), 2) AS avg_review
        FROM items i
        JOIN sellers s ON i.seller_id = s.seller_id
        JOIN reviews r ON i.order_id = r.order_id
        GROUP BY i.seller_id, s.seller_state
        HAVING total_orders >= 50
    )
    SELECT
        seller_id,
        seller_state,
        total_orders,
        gross_sales,
        avg_review,
        ROW_NUMBER() OVER (ORDER BY avg_review ASC, gross_sales DESC) AS risk_rank
    FROM seller_metrics
    LIMIT 15;
    """
}

results = {}
for fname, query in sql_queries.items():
    with open(os.path.join(SQL_DIR, fname), "w") as f:
        f.write(query.strip() + "\n")
    results[fname] = pd.read_sql_query(query, conn)

# 3. RFM Segmentation & Statistical Test in Pandas
rfm_raw = pd.read_sql_query("""
    WITH order_totals AS (
        SELECT order_id, SUM(payment_value) AS order_revenue
        FROM payments
        GROUP BY order_id
    )
    SELECT
        c.customer_unique_id,
        o.order_id,
        o.order_purchase_timestamp,
        ot.order_revenue
    FROM orders o
    JOIN customers c ON o.customer_id = c.customer_id
    JOIN order_totals ot ON o.order_id = ot.order_id
    WHERE o.order_status = 'delivered'
""", conn)

rfm_raw["order_purchase_timestamp"] = pd.to_datetime(rfm_raw["order_purchase_timestamp"])
snapshot_date = rfm_raw["order_purchase_timestamp"].max() + pd.Timedelta(days=1)

rfm = rfm_raw.groupby("customer_unique_id").agg(
    recency=("order_purchase_timestamp", lambda x: (snapshot_date - x.max()).days),
    frequency=("order_id", "nunique"),
    monetary=("order_revenue", "sum"),
).reset_index()

rfm["r_score"] = pd.qcut(rfm["recency"], 4, labels=[4, 3, 2, 1]).astype(int)
rfm["m_score"] = pd.qcut(rfm["monetary"].rank(method="first"), 4, labels=[1, 2, 3, 4]).astype(int)

def segment_customer(row):
    if row["frequency"] >= 2 and row["r_score"] >= 3 and row["m_score"] >= 3:
        return "Champions (Repeat High-Value)"
    elif row["frequency"] >= 2:
        return "Loyal / Repeat Buyers"
    elif row["r_score"] >= 3 and row["m_score"] >= 3:
        return "Recent High-Spenders (1x)"
    elif row["r_score"] <= 2 and row["m_score"] >= 3:
        return "At-Risk High-Spenders (1x)"
    else:
        return "Standard / Dormant (1x)"

rfm["segment"] = rfm.apply(segment_customer, axis=1)
rfm_summary = rfm.groupby("segment").agg(
    customers=("customer_unique_id", "count"),
    avg_recency_days=("recency", "mean"),
    avg_orders=("frequency", "mean"),
    total_revenue=("monetary", "sum"),
).round(2).reset_index().sort_values("total_revenue", ascending=False)

# Statistical test: On-Time vs Late review scores
deliv_df = pd.read_sql_query("""
    SELECT
        CASE WHEN JULIANDAY(o.order_delivered_customer_date) > JULIANDAY(o.order_estimated_delivery_date)
             THEN 'Late' ELSE 'On-Time' END AS status,
        r.review_score
    FROM orders o
    JOIN (SELECT order_id, AVG(review_score) AS review_score FROM reviews GROUP BY order_id) r
      ON o.order_id = r.order_id
    WHERE o.order_status = 'delivered'
      AND o.order_delivered_customer_date IS NOT NULL
      AND o.order_estimated_delivery_date IS NOT NULL
""", conn)

on_time = deliv_df[deliv_df["status"] == "On-Time"]["review_score"]
late = deliv_df[deliv_df["status"] == "Late"]["review_score"]
t_stat, p_val = stats.ttest_ind(on_time, late, equal_var=False)

stats_summary = pd.DataFrame([{
    "on_time_orders": len(on_time),
    "on_time_avg_score": round(on_time.mean(), 3),
    "late_orders": len(late),
    "late_avg_score": round(late.mean(), 3),
    "score_drop": round(on_time.mean() - late.mean(), 3),
    "welch_t_stat": round(t_stat, 2),
    "p_value": f"{p_val:.2e}",
}])

# 4. Generate 2 Charts
plt.figure(figsize=(7, 4))
plt.bar(["On-Time", "Late"], [on_time.mean(), late.mean()], color=["#2E7D32", "#C62828"])
plt.ylim(0, 5.2)
plt.ylabel("Average Review Score (1–5)")
plt.title("Impact of Late Delivery on Customer Review Scores")
for idx, val in enumerate([on_time.mean(), late.mean()]):
    plt.text(idx, val + 0.1, f"{val:.2f}", ha="center", fontweight="bold")
plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, "delivery_vs_reviews.png"), dpi=150)
plt.close()

total_rev = rfm_summary["total_revenue"].sum()
count_col = next((c for c in ["customers", "customer_count", "unique_customers",
                              "num_customers", "n_customers"] if c in rfm_summary.columns), None)

plt.figure(figsize=(10, 5))
plt.barh(rfm_summary["segment"], rfm_summary["total_revenue"] / 1e6, color="#1565C0")
for i, (_, row) in enumerate(rfm_summary.reset_index(drop=True).iterrows()):
    rev = row["total_revenue"]
    label = f"R${rev/1e6:.1f}M ({rev/total_rev:.0%})"
    if count_col:
        label += f" | n={int(row[count_col]):,}"
    plt.text(rev / 1e6 + 0.05, i, label, va="center", fontsize=9)
plt.xlim(0, rfm_summary["total_revenue"].max() / 1e6 * 1.5)
plt.xlabel("Total Revenue (Millions BRL)")
plt.title("Revenue Contribution by Customer RFM Segment")
plt.gca().invert_yaxis()
plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, "rfm_segment_revenue.png"), dpi=150)
plt.close()

# 5. Export Multi-Sheet Executive Excel Report
excel_path = os.path.join(OUT_DIR, "Olist_Executive_Report.xlsx")
with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
    stats_summary.to_excel(writer, sheet_name="Delivery_Stat_Test", index=False)
    results["01_delivery_impact.sql"].to_excel(writer, sheet_name="Delivery_Summary", index=False)
    rfm_summary.to_excel(writer, sheet_name="RFM_Segments", index=False)
    results["02_category_revenue_delivery.sql"].to_excel(writer, sheet_name="Top_Categories", index=False)
    results["03_high_sales_poor_sellers.sql"].to_excel(writer, sheet_name="Seller_Risk_Rank", index=False)

    # 6. Delay buckets vs. review score
delay_query = """
WITH order_reviews AS (
    SELECT order_id, AVG(review_score) AS score
    FROM reviews
    GROUP BY order_id
)
SELECT
    o.order_id,
    julianday(o.order_delivered_customer_date) - julianday(o.order_estimated_delivery_date) AS delay_days,
    r.score
FROM orders o
JOIN order_reviews r ON r.order_id = o.order_id
WHERE o.order_status = 'delivered'
  AND o.order_delivered_customer_date IS NOT NULL
  AND o.order_estimated_delivery_date IS NOT NULL
"""
delay_df = pd.read_sql_query(delay_query, conn)
delay_df["bucket"] = pd.cut(
    delay_df["delay_days"],
    bins=[-float("inf"), 0, 3, 7, float("inf")],
    labels=["On time", "0-3 days late", "3-7 days late", "7+ days late"],
)
bucket_summary = (
    delay_df.groupby("bucket", observed=True)["score"]
    .agg(avg_score="mean", orders="count")
    .reset_index()
)
print(bucket_summary)

plt.figure(figsize=(9, 5))
colors = ["#2E7D32", "#F9A825", "#EF6C00", "#C62828"]
bars = plt.bar(bucket_summary["bucket"].astype(str), bucket_summary["avg_score"], color=colors)
for bar, avg, n in zip(bars, bucket_summary["avg_score"], bucket_summary["orders"]):
    plt.text(bar.get_x() + bar.get_width() / 2, avg + 0.06,
             f"{avg:.2f}\n(n={n:,})", ha="center", fontsize=9)
plt.ylim(0, 5.4)
plt.ylabel("Average Review Score (1-5)")
plt.title("Review Scores Drop Sharply as Delivery Delay Grows")
plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, "delay_buckets_vs_reviews.png"), dpi=150)
plt.close()
conn.close()
print("Done! Generated SQL files, charts, and Excel workbook in /outputs.")