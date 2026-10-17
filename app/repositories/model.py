from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.model import ModelRun

class ModelRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, run: ModelRun) -> ModelRun:
        self._session.add(run)
        self._session.commit()
        self._session.refresh(run)
        return run

    def get_latest(self) -> ModelRun | None:
        stmt = select(ModelRun).order_by(ModelRun.trained_at.desc()).limit(1)
        return self._session.scalar(stmt)