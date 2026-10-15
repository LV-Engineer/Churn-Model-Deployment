from sqlalchemy.orm import Session

from app.models.model import ModelRun

class ModelRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, run: ModelRun) -> ModelRun:
        """Save a record about a finished training run."""
        ...

    def get_latest(self) -> ModelRun | None:
        """Return the most recent run, or None if the model was never trained."""
        ...