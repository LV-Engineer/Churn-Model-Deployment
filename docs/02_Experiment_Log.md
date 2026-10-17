Experiment Log

Log checks, measurements and decisions for deployment and monitoring.

| # | Check | Setup | Result | Notes |
| --- | --- | --- | --- | --- |
| 1 | Drift check without a shift | `POST /monitoring/drift`: reference from the database against the same data exported as CSV; alert rule: drifted share >= 0.3 or drift in `tenure_months`, `monthly_charges`, `contract` | 0 of 18 columns drifted (share 0), `alert: false` | Checks that the rule does not raise an alert on unchanged data. Same data against itself, so zero drift is expected; it is not a test on a separate sample |
| 2 | Drift check with a simulated shift | `app/monitoring/simulate.py`, strength 1.0: monthly charges +30%, tenure -40%, 30% of customers moved to month-to-month, 20% to fiber optic; then `POST /monitoring/drift` | 3 of 18 columns drifted (share 0.167): `tenure_months`, `contract`, `monthly_charges`; `alert: true` | The alert comes from the key-feature rule, the share is below the 0.3 threshold. `internet_service` was shifted on purpose but not flagged: this shift is too small for the test Evidently uses for that column. Simulated shift on one dataset, not real production drift |
| 3 | Latency of `POST /predict` | `uv run python -m app.monitoring.latency --requests 200 --delay 1.1`: 5 warm-up and 200 measured sequential requests from the host to the Docker Compose stack, model already cached in Redis, rate limiter enabled | mean 29.26 ms, p50 27.32 ms, p95 40.67 ms, p99 59.93 ms, max 78.43 ms | An earlier run of 50 requests gave mean 26.79 ms and p95 37.12 ms. Includes the HTTP call over localhost, validation, reading the model from Redis and unpickling it; one client, one machine, not a load test. Not compared with a run without the Redis cache |
| 4 | | | | |
| 5 | | | | |
| 6 | | | | |
| 7 | | | | |
| 8 | | | | |

# Conclusions

**What worked**
- The same logistic regression as in Project 1 reaches ROC-AUC 0.848 when trained inside the service on data from PostgreSQL.
- The drift rule did not alert on unchanged data and alerted on the simulated shift through the key features (rows 1 and 2).

**What broke, and how it was found**
- The rate limiter decorators were added without the `request` argument that `slowapi` needs, so the application did not start; the first test run caught it.
- `clean()` crashed on a numeric `Total Charges` (for example from parquet); a test for numeric input caught it.
- MLflow logging failed silently because the sklearn flavor needs `skops`, which the lightweight client does not include; the `try/except` around the logging hid it until the logged run was checked in a test.

**What to improve**
- Compare the latency with and without the Redis model cache (only the cached case was measured, row 3).
- Check the drift rule on a separate sample instead of the same data, and find the shift strength where the alert starts.
- Add authentication, migrations and a retraining trigger on drift.
