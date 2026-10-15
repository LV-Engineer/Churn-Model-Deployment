from typing import Literal

from fastapi import UploadFile

from app.schemas.data import UploadResponse, DeleteResponse

class DataService:
    def upload(self, file: UploadFile) -> UploadResponse:
        """Parse CSV or parquet, clean it, store the rows in the database."""
        ...

    def export(self, fmt: Literal["csv", "parquet"]) -> bytes:
        """Return all training data in the requested format."""
        ...

    def clear(self) -> DeleteResponse:
        """Delete all training data."""
        ...