from fastapi import FastAPI

from app.routers import data, health, model

app = FastAPI(title="Churn Prediction API")

app.include_router(health.router)
app.include_router(data.router)
app.include_router(model.router)