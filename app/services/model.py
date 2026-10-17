import uuid
from datetime import UTC, datetime
from io import BytesIO

import joblib
import pandas as pd
from sklearn.pipeline import Pipeline
from sqlalchemy.orm import Session

from app.core.constants import (
    FEATURE_TO_DB,
    MIN_TRAIN_ROWS,
    MODEL_CACHE_TTL,
    MODELS_DIR,
    TARGET,
    THRESHOLD,
)
from app.schemas.model import PredictionRequest, PredictionResponse, TrainResponse
from app.repositories.data import DataRepository
from app.repositories.model import ModelRepository
from app.core.train import fit_model
from app.models.model import ModelRun
from app.core.redis import redis_client

class ModelService:
    def __init__(self, db: Session) -> None:
        self._data_repo = DataRepository(db)
        self._model_repo = ModelRepository(db)

    def train(self) -> TrainResponse:
        n_rows = self._data_repo.count()
        if n_rows < MIN_TRAIN_ROWS:
            raise ValueError(f"Not enough data: {n_rows} rows, need at least {MIN_TRAIN_ROWS}")

        df = self._to_frame()
        if df[TARGET].nunique() < 2:
            raise ValueError("Training data must contain both churned and retained customers")

        pipeline, auc = fit_model(df)

        run_id = uuid.uuid4()
        filename = f"churn_model_{run_id}.joblib"
        MODELS_DIR.mkdir(exist_ok=True)
        joblib.dump(pipeline, MODELS_DIR / filename)

        run = self._model_repo.add(ModelRun(
            id=run_id,
            trained_at=datetime.now(UTC),
            n_rows=n_rows,
            roc_auc=auc,
            model_path=filename,
        ))
        return TrainResponse(
            run_id=run.id, trained_at=run.trained_at, n_rows=run.n_rows, roc_auc=run.roc_auc
        )

    def predict(self, request: PredictionRequest) -> PredictionResponse:
        run = self._model_repo.get_latest()
        if run is None:
            raise LookupError("Model is not trained yet, call POST /train first")

        pipeline = self._load(run)
        row = pd.DataFrame([request.model_dump(by_alias=True)])
        proba = float(pipeline.predict_proba(row)[0, 1])
        return PredictionResponse(churn_probability=proba, contact=proba >= THRESHOLD)

    @staticmethod
    def _load(run: ModelRun) -> Pipeline:
        key = f"model:{run.id}"
        cached = redis_client.get(key)
        if isinstance(cached, bytes):
            return joblib.load(BytesIO(cached))

        data = (MODELS_DIR / run.model_path).read_bytes()
        redis_client.set(key, data, ex=MODEL_CACHE_TTL)
        return joblib.load(BytesIO(data))

    def _to_frame(self) -> pd.DataFrame:
        rows = [
            {col: getattr(c, col) for col in FEATURE_TO_DB.values()}
            for c in self._data_repo.get_all()
        ]
        inverse = {db_name: raw_name for raw_name, db_name in FEATURE_TO_DB.items()}
        return pd.DataFrame(rows).rename(columns=inverse)