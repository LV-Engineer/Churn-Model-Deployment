Project 3: Churn Model Deployment and Monitoring

Repo: [GitHub link]

# Business problem

* Who uses the model: [retention team / CRM system]
* Why a notebook is not enough: [predictions must be available on demand, reproducible and checked over time]
* Decision supported: [scoring new customers and flagging model degradation]

# Data

* Input: [model and preprocessing pipeline from Project 1]
* Request schema: [customer features, validated with Pydantic]
* Monitoring data: [reference set vs simulated new data with drift]
* Data issues: [schema mismatch, missing values, drift]

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
| Dashboard | Grafana - optional |

# Approach

* Export model and pipeline from Project 1 (joblib / torch.save) with fixed versions
* Endpoints: `/health`, `/predict` (single customer), `/train`, `POST /data` (CSV or parquet, raw Kaggle format, cleaned and stored in the database), `GET /data/export` (CSV or parquet), `DELETE /data` (clear the training data)
* Training reads the cleaned data from the database; the exported data is the reference set for drift
* Pydantic schemas with validation errors for bad input
* Dockerfile: small image, pinned requirements
* PostgreSQL in docker compose: store the cleaned training data
* pytest: valid input, invalid input, edge cases, prediction range
* CI: run pytest and mypy on every push
* Drift: simulate shifted data, build an Evidently report, define alert rule
* Document how to run: docker commands in README

# Results

* Latency: [ms per request]
* Tests: [number, coverage]
* Drift detected on simulated shift: [yes/no, which features]
* Limitations: [local deployment only, simulated drift]

# Takeaway

* What makes the model usable beyond a notebook: [...]
* Next step: [cloud deployment, retraining trigger on drift]
