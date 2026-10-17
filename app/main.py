from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from app.core.db import engine
from app.models import data as _data, model as _model  # noqa: F401
from app.models.base import Base
from app.routers import data, health, model, monitoring
from app.core.limiter import limiter

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    Base.metadata.create_all(engine)
    yield

async def rate_limit_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=429, content={"detail": "Too many requests"})

app = FastAPI(title="Churn Prediction API", lifespan=lifespan)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_handler)

app.include_router(health.router)
app.include_router(data.router)
app.include_router(model.router)
app.include_router(monitoring.router)