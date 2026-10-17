# Work Plan and Checklist

- [x] 1. Finish Project 1 and export model and pipeline
- [x] 2. App skeleton: stubs for routers, services, repositories, models and schemas
- [x] 3. Dockerfile and docker compose with PostgreSQL, build and run locally
- [x] 4. Implement the stubs: /health, /predict, POST /data (CSV or parquet, cleaned), GET /data/export, DELETE /data, POST /train (each run saves a versioned model file and a row in the database)
- [x] 5. Redis in docker compose: cache the loaded model, rate limiter
- [x] 6. Write pytest tests (valid, invalid, edge cases)
- [x] 7. Add type hints and run mypy
- [ ] 8. GitHub Actions: pytest + mypy on push
- [ ] 9. Simulate drifted data, Evidently report, alert rule
- [ ] 10. MLflow tracking, DVC for data/model
- [ ] 11. Grafana dashboard
- [ ] 12. README with structure and run instructions
