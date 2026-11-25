\# E-Commerce Customer \& Delivery Performance Analysis (Olist)



End-to-end relational SQL and Python analysis of \~100,000 Brazilian e-commerce orders from the Olist public dataset (CC BY-NC-SA 4.0), evaluating customer RFM value segments, seller quality risks, and the relationship between late deliveries and customer review scores.



\## Key Findings \& Recommendations



\- \*\*Late Delivery Penalty:\*\* Orders delivered past their estimated delivery date averaged \*\*2.57 review stars\*\* versus \*\*4.29 stars\*\* for on-time orders — a \*\*1.73-point drop\*\*. A Welch's t-test indicates a statistically significant difference (\*\*p < 0.001\*\*).  

&#x20; \*Recommendation:\* Trigger proactive delay notifications and carrier escalations when orders cross 80% of their estimated transit window.



\- \*\*One-Time Buyer Concentration:\*\* \*\*96.88% of unique customers\*\* purchased only once, highlighting a major retention opportunity. One-time buyers generated approximately \*\*R$15.06M in payment value\*\* across the dataset.  

&#x20; \*Recommendation:\* Target recent one-time purchasers with a post-delivery replenishment or second-purchase incentive.



\- \*\*High-Revenue Seller Risk:\*\* Ranked sellers with at least \*\*50 orders\*\* by average review score using SQL window functions such as `ROW\_NUMBER()` to identify high-volume sellers requiring marketplace quality intervention.



\## Methodology \& Data Integrity



\- \*\*Preventing Join Fan-Out:\*\* Payments and order items were pre-aggregated at the `order\_id` level inside SQLite CTEs before joining to orders and reviews, preventing revenue double-counting.



\- \*\*Customer Grain:\*\* Customer-level analysis uses `customer\_unique\_id` rather than `customer\_id` because multiple customer records can belong to the same unique customer.



\- \*\*Late Definition:\*\*  

&#x20; `order\_delivered\_customer\_date > order\_estimated\_delivery\_date`  

&#x20; evaluated strictly on delivered orders with valid delivery and estimated-delivery timestamps.



\- \*\*Review Analysis:\*\* Reviews were aggregated to the order level before joining to delivery data to avoid duplicate review rows affecting results.



\- \*\*Limitations:\*\* The dataset covers historical orders from 2016–2018, lacks product COGS/margin data, and demonstrates a strong statistical association between delivery performance and reviews rather than causal proof.



\## Dataset Overview



\- \*\*99,441 orders\*\*

\- \*\*96,096 unique customers\*\*

\- \*\*96,478 delivered orders\*\*

\- \*\*7,826 late delivered orders\*\*

\- \*\*8.11% late-delivery rate among delivered orders\*\*

\- \*\*8 relational source tables\*\* used in the SQLite analytical database



\## Technical Skills Demonstrated



\- \*\*SQL:\*\* JOINs, CTEs, `GROUP BY`, `HAVING`, aggregations, date calculations, window functions

\- \*\*Python:\*\* pandas, NumPy, SciPy

\- \*\*Statistics:\*\* hypothesis testing and significance testing

\- \*\*Data Quality:\*\* grain validation, duplicate checks, join fan-out prevention

\- \*\*Visualization:\*\* customer, delivery, revenue, and seller performance analysis

\- \*\*Reporting:\*\* automated Excel output and reproducible analysis pipeline



\## How to Reproduce



1\. Download the \[Olist Brazilian E-Commerce dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) into `data/raw/`.



2\. Install dependencies:



```bash

pip install pandas openpyxl matplotlib scipy

```



3\. Run the full pipeline:



```bash

python src/run\_report.py

```



4\. Review generated outputs in:



```text

outputs/

```



\## Project Structure



```text

olist-customer-delivery-analysis/

│

├── data/

│   └── raw/              # Download dataset here; raw data is not committed

│

├── outputs/              # Generated reports and analysis outputs

│

├── sql/                  # SQL analysis queries

│

├── src/

│   └── run\_report.py     # Reproducible analysis/report pipeline

│

├── .gitignore

├── README.md

└── olist.db              # Local SQLite analytical database

```



\## Business Questions



1\. Which customers represent the highest-value RFM segments?

2\. How concentrated is the customer base among one-time versus repeat buyers?

3\. How strongly are late deliveries associated with lower review scores?

4\. Which product categories and states drive revenue?

5\. Which high-volume sellers combine strong sales with poor customer reviews?

6\. What operational actions could improve retention and customer satisfaction?

