from sqlalchemy.orm import Session

from app.models.data import Customer

class DataRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add_many(self, customers: list[Customer]) -> int:
        """Insert rows, return how many were added."""
        ...

    def get_all(self) -> list[Customer]:
        """Return every training row."""
        ...

    def count(self) -> int:
        ...

    def delete_all(self) -> int:
        """Remove every row, return how many were deleted."""
        ...