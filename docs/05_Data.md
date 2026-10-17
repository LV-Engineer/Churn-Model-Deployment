# Data

The data files are **not committed** and are not stored in the repository. The raw file is uploaded to the running API, which cleans it and stores it in PostgreSQL.

## Source

- Dataset: IBM Telco Customer Churn (extended version)
- Download: https://www.kaggle.com/datasets/yeanzc/telco-customer-churn-ibm-dataset
- License: not explicitly specified. Kaggle lists "Other (specified in description)", but the description
  gives no license text, only the origin: IBM Community sample datasets (Cognos Analytics). Used here
  for educational and portfolio purposes only; the raw data is not redistributed in this repository.
- Origin (per the Kaggle description): IBM Community, [Telco Customer Churn](https://community.ibm.com/community/user/businessanalytics/blogs/steven-macko/2019/07/11/telco-customer-churn-1113), part of the IBM Cognos Analytics sample datasets
- Original file: `Telco_customer_churn.xlsx` (sheet `Telco_Churn`)

## How to load the data

1. Download the dataset from the link above (a Kaggle login is required).
2. Convert the sheet to CSV (or parquet). Example for CSV:

```bash
uvx --with openpyxl --with pandas python -I -c "import pandas as pd; pd.read_excel('Telco_customer_churn.xlsx').to_csv('Telco_customer_churn.csv', index=False)"
```

3. Start the services with `docker compose up --build` and upload the file with `POST /data/load` (for example in `/docs`). The file can be anywhere on your computer. The raw Kaggle format (33 columns) is the only accepted input.

The raw file is never edited by hand. All cleaning is done in code (`clean()` in `app/core/data.py`) on every upload, and only the cleaned rows are stored in the `customers` table. Rows whose `customer_id` already exists are skipped.

## Where the data lives

- **PostgreSQL** (`customers` table, Docker volume `pgdata`): cleaned training data.
- **`GET /data/export?format=csv|parquet`**: download the stored data.
- **`DELETE /data/clear`**: remove all stored data.

## Facts about the raw file

Checked by reading the file:

- 7043 rows x 33 columns, one row per customer.
- Target class balance: `Churn Label` No 73.5%, Yes 26.5%. A model that always predicts "No" would reach about 73% accuracy, so accuracy alone is not a useful metric.
- Missing values: only `Churn Reason` (5174 missing, filled only for customers who left).
- `Total Charges` is read as text (`object`), so it contains non-numeric values and needs cleaning.

## Target

- `Churn Value`: 1 = the customer left (positive class), 0 = stayed.
- `Churn Label` is the same information as Yes/No text and is dropped after the target is built.

## Column roles

| Role | Columns |
| --- | --- |
| Target | `Churn Value` |
| Leakage, excluded from features | `Churn Label`, `Churn Score`, `Churn Reason` |
| Identifiers and constants, excluded | `CustomerID`, `Count`, `Country`, `State`, `Lat Long` |
| Business use, not a feature (to decide) | `CLTV` |
| Candidate features | demographics (`Gender`, `Senior Citizen`, `Partner`, `Dependents`), services (`Phone Service`, `Multiple Lines`, `Internet Service`, `Online Security`, `Online Backup`, `Device Protection`, `Tech Support`, `Streaming TV`, `Streaming Movies`), account (`Tenure Months`, `Contract`, `Paperless Billing`, `Payment Method`, `Monthly Charges`, `Total Charges`) |
| To decide in EDA | `City`, `Zip Code`, `Latitude`, `Longitude` (high cardinality, little value for a business decision) |

Why these decisions:

- `Churn Score` is, per the dataset description, computed by a predictive tool (IBM SPSS Modeler) and `Churn Reason` explains why a customer left, so using them as features would leak the target.
- `CLTV` is a predicted customer lifetime value computed with corporate formulas. Its use as a feature or in the business cost calculation is still an open decision, to be recorded in the experiment log.

The roles above are a plan based on column names and the checks listed in "Facts". They will be confirmed or changed in EDA.
