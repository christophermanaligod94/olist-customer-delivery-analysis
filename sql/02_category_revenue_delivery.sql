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
