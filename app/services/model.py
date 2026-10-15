from pathlib import Path

import joblib
from sklearn.pipeline import Pipeline

from app.core.config import MODEL_PATH
from app.schemas.model import PredictionRequest, PredictionResponse, TrainResponse

class ModelService:
    def __init__(self, model_path: Path = MODEL_PATH) -> None:
        self._model_path = model_path
        self._pipeline: Pipeline | None = None

    def load(self) -> None:
        """Read the trained pipeline from disk into memory."""
        self._pipeline = joblib.load(self._model_path)

    def predict(self, request_data: PredictionRequest) -> PredictionResponse:
        ...

    def train(self) -> TrainResponse:
        ...