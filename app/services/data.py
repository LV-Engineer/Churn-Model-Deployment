from typing import Literal, Any, cast
from pathlib import Path
from io import BytesIO

import pandas as pd
from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.constants import FEATURE_TO_DB
from app.core.data import clean
from app.models.data import Customer
from app.schemas.data import UploadResponse, DeleteResponse
from app.repositories.data import DataRepository

class DataService:
    def __init__(self, db: Session) -> None:
        self._repo = DataRepository(db)

    def upload(self, file: UploadFile) -> UploadResponse:
        df = clean(self._read(file))
        df = df[~df.index.duplicated()]
        df = df[list(FEATURE_TO_DB)].rename(columns=FEATURE_TO_DB)

        existing = self._repo.existing_customer_ids(df.index.tolist())
        new = df[~df.index.isin(existing)]

        records = cast(list[dict[str, Any]], new.to_dict("records"))
        customers = [
            Customer(customer_id=cid, **row)
            for cid, row in zip(new.index, records)
        ]
        added = self._repo.add_many(customers)
        return UploadResponse(rows_added=added, rows_skipped=len(df) - added)

    @staticmethod
    def _read(file: UploadFile) -> pd.DataFrame:
        match Path(file.filename or "").suffix.lower():
            case ".csv":
                return pd.read_csv(file.file)
            case ".parquet":
                return pd.read_parquet(file.file)
            case _:
                raise ValueError("Unsupported file type, use .csv or .parquet")

    def export(self, fmt: Literal["csv", "parquet"]) -> bytes:
        columns = [c.name for c in Customer.__table__.columns if c.name != "id"]
        rows = self._repo.get_all()
        df = pd.DataFrame(
            [{c: getattr(r, c) for c in columns} for r in rows], columns=columns
        )
        match fmt:
            case "csv":
                return df.to_csv(index=False).encode()
            case "parquet":
                buffer = BytesIO()
                df.to_parquet(buffer, index=False)
                return buffer.getvalue()
            case _:
                raise ValueError(f"Unsupported format: {fmt}")

    def clear(self) -> DeleteResponse:
        return DeleteResponse(rows_deleted=self._repo.delete_all())