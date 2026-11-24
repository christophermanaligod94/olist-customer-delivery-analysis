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
