import io
import os
import tempfile
from collections.abc import Generator
from pathlib import Path

os.environ.setdefault("POSTGRES_USER", "placeholder")
os.environ.setdefault("POSTGRES_PASSWORD", "placeholder")
os.environ.setdefault("POSTGRES_DB", "placeholder")
os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://placeholder:placeholder@localhost:5432/placeholder")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("MLFLOW_TRACKING_URI", "file:" + tempfile.mkdtemp())
os.environ.setdefault("MLFLOW_ALLOW_FILE_STORE", "true")

import fakeredis
import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session
from testcontainers.postgres import PostgresContainer

from app.core.constants import FEATURE_TO_DB
from app.core.data import clean
from app.core.db import get_db
from app.core.limiter import limiter
from app.core.settings import settings
from app.main import app
from app.models.base import Base

VALID_CUSTOMER = {
    "gender": "Male",
    "senior_citizen": "No",
    "partner": "No",
    "dependents": "No",
    "tenure_months": 2,
    "phone_service": "Yes",
    "multiple_lines": "No",
    "internet_service": "Fiber optic",
    "online_security": "No",
    "online_backup": "No",
    "device_protection": "No",
    "tech_support": "No",
    "streaming_tv": "No",
    "streaming_movies": "No",
    "contract": "Month-to-month",
    "paperless_billing": "Yes",
    "payment_method": "Electronic check",
    "monthly_charges": 90.0,
}


def make_raw_customers(n: int = 300, seed: int = 0) -> pd.DataFrame:
    """Synthetic data in the raw Kaggle format (33 columns), churn depends on contract and tenure."""
    rng = np.random.default_rng(seed)
    yes_no = ["Yes", "No"]
    extra = ["Yes", "No", "No internet service"]

    tenure = rng.integers(0, 73, n)
    tenure[0] = 0
    monthly = rng.uniform(18.0, 119.0, n).round(2)
    contract = rng.choice(["Month-to-month", "One year", "Two year"], n)

    p_churn = 0.1 + 0.5 * (contract == "Month-to-month") - 0.003 * tenure
    churn = (rng.random(n) < np.clip(p_churn, 0.02, 0.95)).astype(int)

    total = (tenure * monthly).round(2).astype(str)
    total[0] = " "  # the real dataset has blank Total Charges for new customers

    return pd.DataFrame({
        "CustomerID": [f"CUST-{i:05d}" for i in range(n)],
        "Count": 1,
        "Country": "United States",
        "State": "California",
        "City": "Los Angeles",
        "Zip Code": 90001,
        "Lat Long": "33.9, -118.2",
        "Latitude": 33.9,
        "Longitude": -118.2,
        "Gender": rng.choice(["Female", "Male"], n),
        "Senior Citizen": rng.choice(yes_no, n),
        "Partner": rng.choice(yes_no, n),
        "Dependents": rng.choice(yes_no, n),
        "Tenure Months": tenure,
        "Phone Service": rng.choice(yes_no, n),
        "Multiple Lines": rng.choice(["Yes", "No", "No phone service"], n),
        "Internet Service": rng.choice(["DSL", "Fiber optic", "No"], n),
        "Online Security": rng.choice(extra, n),
        "Online Backup": rng.choice(extra, n),
        "Device Protection": rng.choice(extra, n),
        "Tech Support": rng.choice(extra, n),
        "Streaming TV": rng.choice(extra, n),
        "Streaming Movies": rng.choice(extra, n),
        "Contract": contract,
        "Paperless Billing": rng.choice(yes_no, n),
        "Payment Method": rng.choice(
            ["Bank transfer (automatic)", "Credit card (automatic)", "Electronic check", "Mailed check"], n
        ),
        "Monthly Charges": monthly,
        "Total Charges": total,
        "Churn Label": np.where(churn == 1, "Yes", "No"),
        "Churn Value": churn,
        "Churn Score": 50,
        "CLTV": 4000,
        "Churn Reason": "unknown",
    })


def csv_file(df: pd.DataFrame, name: str = "customers.csv") -> dict:
    return {"file": (name, df.to_csv(index=False).encode(), "text/csv")}


def parquet_file(df: pd.DataFrame, name: str = "customers.parquet") -> dict:
    buffer = io.BytesIO()
    df.to_parquet(buffer, index=False)
    return {"file": (name, buffer.getvalue(), "application/octet-stream")}


@pytest.fixture(scope="session")
def postgres_url() -> Generator[str, None, None]:
    with PostgresContainer("postgres:17", username="test", password="test", dbname="test") as container:
        url = (
            f"postgresql+psycopg://{container.username}:{container.password}"
            f"@{container.get_container_host_ip()}:{container.get_exposed_port(5432)}/{container.dbname}"
        )
        engine = create_engine(url)
        Base.metadata.create_all(engine)
        engine.dispose()
        yield url


@pytest.fixture(scope="session")
def engine(postgres_url: str) -> Generator[Engine, None, None]:
    eng = create_engine(postgres_url)
    yield eng
    eng.dispose()


@pytest.fixture
def db_session(engine: Engine) -> Generator[Session, None, None]:
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def _disable_rate_limit() -> Generator[None, None, None]:
    limiter.enabled = False
    yield
    limiter.enabled = True


@pytest.fixture(autouse=True)
def fake_redis(monkeypatch: pytest.MonkeyPatch) -> fakeredis.FakeRedis:
    redis = fakeredis.FakeRedis()
    redis.flushall()
    monkeypatch.setattr("app.services.model.redis_client", redis)
    return redis


@pytest.fixture(autouse=True)
def models_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setattr("app.services.model.MODELS_DIR", tmp_path)
    return tmp_path


@pytest.fixture(autouse=True)
def mlflow_store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Every test logs to its own empty MLflow store."""
    monkeypatch.setattr(settings, "mlflow_tracking_uri", f"file:{tmp_path / 'mlruns'}")


@pytest.fixture
def valid_customer() -> dict:
    return dict(VALID_CUSTOMER)


@pytest.fixture
def raw_customers() -> pd.DataFrame:
    return make_raw_customers()


@pytest.fixture
def exported_customers(raw_customers: pd.DataFrame) -> pd.DataFrame:
    """The same data in the shape GET /data/export returns."""
    cleaned = clean(raw_customers)
    return cleaned[list(FEATURE_TO_DB)].rename(columns=FEATURE_TO_DB).reset_index(names="customer_id")


@pytest.fixture
def loaded_client(client: TestClient, raw_customers: pd.DataFrame) -> TestClient:
    """A client whose database already holds the synthetic customers."""
    response = client.post("/data/load", files=csv_file(raw_customers))
    assert response.status_code == 200
    return client
