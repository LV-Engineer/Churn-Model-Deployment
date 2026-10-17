# Churn Model Deployment and Monitoring

A service around the customer churn model from [Project 1](https://github.com/LV-Engineer/Churn-Prediction): a FastAPI application that trains the model on data stored in PostgreSQL, scores customers on demand, and watches for data drift. Everything runs with one `docker compose up`.

**Result in one line:** the model from a notebook is now an API with validated input, versioned model files, a Redis model cache, rate limiting, MLflow run tracking, an Evidently drift check and a Grafana dashboard; 83 tests (99% line coverage) and strict `mypy` run on every push.

## Business problem

- **Who uses the model:** the retention team of a telecom operator, or a CRM system that calls the API.
- **Why a notebook is not enough:** predictions must be available on demand, the model must be reproducible and versioned, and someone has to notice when new customers stop looking like the ones the model was trained on.
- **Decision supported:** which customers get a retention offer (the model and the decision threshold 0.05 come from Project 1, where the threshold was chosen by expected profit under simulated cost assumptions), plus a signal when the data drifts and the model may need retraining.

## Data

- **Source:** IBM Telco Customer Churn (extended version), the same data as in Project 1. Details and license note: [docs/05_Data.md](docs/05_Data.md). The data is not stored in the repository: the raw file is uploaded to the API, cleaned and kept in PostgreSQL.
- **Request schema:** 18 customer features (16 categorical, 2 numeric) validated with Pydantic. Invalid values (unknown category, negative tenure) are rejected with `422`.
- **Training data:** the cleaned rows in the `customers` table; the same `clean()` function as in Project 1 runs on every upload. Rows whose `customer_id` already exists are skipped.
- **Monitoring data:** the reference set is the training data (`GET /data/export`); "new data" is a copy with a simulated shift (`app/monitoring/simulate.py`). There is no real production traffic in this project.
- **Data issues handled:** blank `Total Charges` for new customers, files with a numeric `Total Charges` (for example parquet), duplicate customers inside a file or against the database, missing columns (`400`).

## Approach

- **Model:** logistic regression with the Project 1 preprocessing (`StandardScaler` on two numeric features, one-hot encoding on the categorical ones) in one scikit-learn `Pipeline`, fixed seed 42, stratified 80/20 split. Training reads the cleaned data from PostgreSQL.
- **Versioning:** every `POST /train` saves `churn_model_<run_id>.joblib` in a Docker volume and a row in `model_runs` (time, rows, ROC-AUC). `POST /predict` always uses the latest run. The run is also logged to MLflow (parameters, ROC-AUC, model) on the same PostgreSQL server. DVC is not used: the data lives in the database, not in files.
- **Serving:** FastAPI with a layered structure (routers → services → repositories → models). The loaded model is cached in Redis (key `model:<run_id>`, 24 hours); rate limits are kept in Redis too.
- **Drift monitoring:** Evidently compares the reference data with a new CSV on the 18 features. Alert rule: at least 30% of the columns drifted, **or** drift in `tenure_months`, `monthly_charges` or `contract` (the strongest churn drivers in Project 1). The thresholds are assumptions, not tuned values.
- **Observability:** the API exposes Prometheus metrics (requests, latency, predictions, probability histogram, last ROC-AUC, last drift share and alert); a provisioned Grafana dashboard shows them.
- **Quality:** pytest against a real PostgreSQL (`testcontainers`), `mypy --strict`, GitHub Actions on every pull request and push to `main`, and a branch ruleset that requires a pull request and a passing `test` check.

### Endpoints

| Method and path | What it does | Rate limit |
| --- | --- | --- |
| `GET /health` | liveness check | none |
| `POST /data/load` | upload CSV or parquet (raw Kaggle format), clean it, store it | 60/min |
| `GET /data/export?format=csv\|parquet` | download the stored data | 60/min |
| `DELETE /data/clear` | delete all stored training data | 60/min |
| `POST /train` | train on the stored data, save a new model version | 5/min |
| `POST /predict` | churn probability and the contact decision for one customer | 60/min |
| `POST /monitoring/drift` | drift check of a CSV against the training data (JSON) | 10/min |
| `POST /monitoring/drift/report` | the same check as a downloadable Evidently HTML report | 10/min |
| `GET /metrics` | Prometheus metrics | none |

## Results

- **Model:** ROC-AUC 0.848 on a held-out 20% split of the stored Telco data (shown by the dashboard after training; Project 1 reported 0.847 on its own test set, so the service reproduces the notebook result). The model is the same as in Project 1: simple and explainable, not a new modelling result.
- **Latency of `POST /predict`:** TODO: run `uv run python -m app.monitoring.latency` against the running stack and write the mean and p95 here.
- **Tests:** 83 tests, 99% line coverage of `app` (`uv run pytest --cov=app`), `mypy --strict` clean on 37 source files.
- **Drift on a simulated shift** ([experiment log](docs/02_Experiment_Log.md)):

| Data | Drifted columns | Alert |
| --- | --- | --- |
| the training data against itself | 0 of 18 | no |
| simulated shift (monthly charges +30%, tenure -40%, 30% moved to month-to-month, 20% to fiber optic) | 3 of 18: `tenure_months`, `contract`, `monthly_charges` | yes (key features; the share 0.167 is below 0.3) |

The `internet_service` shift was not flagged: it is too small for the test Evidently uses for that column.

**Limitations**
- The deployment is local (`docker compose`); nothing is deployed to a cloud.
- The drift is simulated on one dataset; there is no real production traffic, and the "no drift" check compares the data with itself.
- The endpoints have rate limiting but no authentication; anyone who can reach the API can train a model or delete the data.
- Tables are created with `create_all`, without migrations, so changing a model needs a manual table change.
- Prometheus metrics live in the memory of the API process: after a restart the model and drift gauges are empty until the next training or drift check.
- The cost assumptions behind the 0.05 threshold are the simulated ones from Project 1; the real save rate can only be measured with an A/B test.

## Takeaway

- A model becomes usable beyond a notebook when its input is validated, every trained version is stored and traceable, predictions are available on demand, tests and type checks guard the code, and a drift check tells you when the data no longer matches the training data.
- Most of the engineering effort went into the parts around the model, not into the model itself, and several real bugs (an app that did not start with the rate limiter, a silent MLflow failure, a crash on numeric `Total Charges`) were found by tests and by running the stack.
- **Next step:** deploy to a cloud, add authentication, replace `create_all` with migrations, and trigger retraining automatically when the drift alert fires.

## How to run

Requires Docker with Compose. Python 3.13 and [uv](https://docs.astral.sh/uv/) are needed only to run the tests and the scripts.

1. Create the environment file and change the passwords (`POSTGRES_PASSWORD`, `GRAFANA_PASSWORD`):

```bash
cp .env.example .env
```

2. Start everything (the first build is slow):

```bash
docker compose up --build
```

3. Open the API docs at `http://127.0.0.1:8000/docs` and follow the scenario:
   1. `POST /data/load` with the Telco CSV (see [docs/05_Data.md](docs/05_Data.md) for how to get it).
   2. `POST /train`, then `POST /predict` with a customer.
   3. `GET /data/export` and save the result as `customers.csv`, then create a shifted copy and check the drift:

```bash
uv run python -m app.monitoring.simulate customers.csv drifted.csv
```

   4. `POST /monitoring/drift` (or `/monitoring/drift/report` for the HTML report) with `drifted.csv`.

| Service | Address |
| --- | --- |
| API and docs | `http://127.0.0.1:8000/docs` |
| MLflow | `http://127.0.0.1:5000` |
| Prometheus | `http://127.0.0.1:9090` |
| Grafana (user `admin`, password from `.env`) | `http://127.0.0.1:3000`, dashboard folder "Churn" |

### Tests and checks

The tests start a temporary PostgreSQL container, so Docker must be running.

```bash
uv sync
uv run pytest
uv run pytest --cov=app --cov-report=term-missing
uv run mypy
```

Latency of the running API:

```bash
uv run python -m app.monitoring.latency
```

## Project structure

```
app/
  main.py          # FastAPI app, metrics, routers
  core/            # constants, settings, cleaning, features, training, DB, Redis, rate limiter, metrics
  routers/         # HTTP layer
  services/        # business logic
  repositories/    # database access
  models/          # SQLAlchemy tables (customers, model_runs)
  schemas/         # Pydantic request and response models
  monitoring/      # drift simulation, Evidently drift check, report and latency scripts
tests/             # pytest suite
grafana/           # provisioned data source and dashboard
prometheus/        # scrape configuration
docs/              # project brief, experiment log, work plan, git workflow, data notes
```

Detailed plan and decisions: [docs/01_Project_Brief.md](docs/01_Project_Brief.md). Experiments: [docs/02_Experiment_Log.md](docs/02_Experiment_Log.md). Git rules: [docs/04_Git_Workflow.md](docs/04_Git_Workflow.md).
