Project 3: Churn Model Deployment and Monitoring

Repo: https://github.com/LV-Engineer/Churn-Model-Deployment
Based on: Project 1 (https://github.com/LV-Engineer/Churn-Prediction)

# Business problem

* Who uses the model: the retention team of a telecom operator, or a CRM system calling the API
* Why a notebook is not enough: predictions must be available on demand, the model must be reproducible and versioned, and the data must be checked for drift over time
* Decision supported: scoring customers (who gets a retention offer, threshold 0.05 from Project 1) and flagging data drift

# Data

* Input: the preprocessing and logistic regression pipeline from Project 1, retrained inside the service on data stored in PostgreSQL
* Request schema: 18 customer features (16 categorical, 2 numeric), validated with Pydantic
* Monitoring data: the training data as the reference set against a simulated shifted copy (`app/monitoring/simulate.py`)
* Data issues: blank or numeric `Total Charges`, duplicate customers, missing columns in uploaded files, drift

# Tech stack

| Area | Tools |
| --- | --- |
| API | FastAPI, Pydantic (input validation, response schema) |
| Packaging | Docker (Dockerfile, docker run / compose) |
| Database | PostgreSQL in docker compose (cleaned training data) |
| Data formats | CSV and parquet (pyarrow) for upload and export |
| Testing | pytest (API tests, input validation, model smoke test) |
| Code quality | mypy, type hints |
| CI | GitHub Actions: tests + mypy on each push |
| Drift monitoring | Evidently (data drift report: reference vs new data) |
| Version control | Git, GitHub |
| Experiment tracking | MLflow (log each training run and model; PostgreSQL backend) |
| Data/model versioning | `model_runs` table and versioned model files (DVC is not used: the data lives in PostgreSQL) |
| Cache | Redis (cache of the loaded model) |
| Dashboard | Prometheus metrics and a provisioned Grafana dashboard |

# Approach

* Export model and pipeline from Project 1 (joblib / torch.save) with fixed versions
* Endpoints: `/health`, `/predict` (single customer), `/train`, `POST /data/load` (CSV or parquet, raw Kaggle format, cleaned and stored in the database), `GET /data/export` (CSV or parquet), `DELETE /data/clear` (clear the training data), `POST /monitoring/drift` and `/monitoring/drift/report` (drift check and HTML report), `GET /metrics`
* Training reads the cleaned data from the database; the exported data is the reference set for drift
* Pydantic schemas with validation errors for bad input
* Dockerfile: small image, pinned requirements
* PostgreSQL in docker compose: store the cleaned training data
* pytest: valid input, invalid input, edge cases, prediction range
* CI: run pytest and mypy on every push
* Drift: simulate shifted data, build an Evidently report, define alert rule
* Document how to run: docker commands in README

# Results

* Latency: TODO, measure with `uv run python -m app.monitoring.latency` and write the mean and p95 here
* Tests: 83 tests, 99% line coverage of `app`, `mypy --strict` clean
* Drift detected on simulated shift: yes, 3 of 18 columns (`tenure_months`, `contract`, `monthly_charges`); the alert comes from the key-feature rule; no alert on unchanged data
* Limitations: local deployment only, simulated drift on one dataset, no authentication (only rate limiting), no migrations, metrics reset on restart

# Takeaway

* What makes the model usable beyond a notebook: validated input, versioned and traceable model runs, predictions on demand, tests and type checks, and a drift check
* Next step: cloud deployment, authentication, migrations, retraining trigger on drift
