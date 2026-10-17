from dataclasses import asdict

import pandas as pd
from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.monitoring.drift import MONITORED_COLUMNS, detect_drift, drift_report_html
from app.repositories.data import DataRepository
from app.schemas.monitoring import DriftResponse

class MonitoringService:
    def __init__(self, db: Session) -> None:
        self._data_repo = DataRepository(db)

    def check_drift(self, file: UploadFile) -> DriftResponse:
        result = detect_drift(self._reference_frame(), self._read(file))
        return DriftResponse(**asdict(result))

    def drift_report(self, file: UploadFile) -> str:
        return drift_report_html(self._reference_frame(), self._read(file))

    @staticmethod
    def _read(file: UploadFile) -> pd.DataFrame:
        return pd.read_csv(file.file)

    def _reference_frame(self) -> pd.DataFrame:
        rows = self._data_repo.get_all()
        if not rows:
            raise ValueError("No reference data: load the training data first")
        return pd.DataFrame([{c: getattr(r, c) for c in MONITORED_COLUMNS} for r in rows])