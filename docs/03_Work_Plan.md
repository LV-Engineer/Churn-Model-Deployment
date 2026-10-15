# Work Plan and Checklist

- [x] 1. Finish Project 1 and export model and pipeline
- [x] 2. App skeleton: stubs for routers, services, repositories, models and schemas
- [ ] 3. Dockerfile and docker compose with PostgreSQL, build and run locally
- [ ] 4. Implement the stubs: /health, /predict, POST /data (CSV or parquet, cleaned), GET /data/export, DELETE /data, POST /train; measure latency
- [ ] 5. Write pytest tests (valid, invalid, edge cases)
- [ ] 6. Add type hints and run mypy
- [ ] 7. GitHub Actions: pytest + mypy on push
- [ ] 8. Simulate drifted data, Evidently report, alert rule
- [ ] 9. Optional: MLflow tracking, DVC for data/model
- [ ] 10. Optional: Redis cache, Grafana dashboard
- [ ] 11. README with structure and run instructions
