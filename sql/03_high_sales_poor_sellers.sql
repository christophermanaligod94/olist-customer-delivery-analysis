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
