\# E-Commerce Customer \& Delivery Performance Analysis (Olist)



End-to-end relational SQL and Python analysis of \~100,000 real Brazilian e-commerce orders (Olist public dataset, CC BY-NC-SA 4.0) evaluating customer RFM value segments, seller quality risks, and the impact of late deliveries on customer review scores.



\## Key Findings \& Recommendations

\- \*\*Late Delivery Penalty:\*\* Orders delivered past their estimated date averaged \*\*\[X.XX]\*\* review stars vs. \*\*\[X.XX]\*\* for on-time orders (a \*\*\[X.XX]\*\*-point drop, $p < 0.001$). \*Recommendation:\* Trigger proactive delay notifications and carrier escalations when orders cross 80% of their estimated transit window.

\- \*\*One-Time Buyer Concentration:\*\* \*\*\[XX]%\*\* of unique customers purchased only once, with \*\*\[Top Segment]\*\* driving \*\*\[X.XXM BRL]\*\* in revenue. \*Recommendation:\* Target `Recent High-Spenders (1x)` with a 30-day post-delivery replenishment incentive.

\- \*\*High-Revenue Seller Risk:\*\* Ranked high-volume sellers (`>= 50` orders) with the lowest average review scores using SQL window functions (`ROW\_NUMBER`) for marketplace quality intervention.



\## Methodology \& Data Integrity

\- \*\*Preventing Join Fan-Out:\*\* Payments and order items were pre-aggregated at the `order\_id` level inside SQLite CTEs before joining to orders and reviews, preventing revenue double-counting.

\- \*\*Late Definition:\*\* `order\_delivered\_customer\_date > order\_estimated\_delivery\_date` (evaluated strictly on `delivered` orders).

\- \*\*Limitations:\*\* Dataset covers 2016–2018 historical orders, lacks product COGS/margin data, and demonstrates strong statistical association rather than causal proof.



\## How to Reproduce

1\. Download the \[Olist Brazilian E-Commerce dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) into `data/raw/`.

2\. Install dependencies: `pip install pandas openpyxl matplotlib scipy`

3\. Run the full pipeline: `python src/run\_report.py`

