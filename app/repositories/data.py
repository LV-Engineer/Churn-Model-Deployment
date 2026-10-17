from typing import Any, cast

from sqlalchemy import delete, func, select
from sqlalchemy.engine import CursorResult
from sqlalchemy.orm import Session

from app.models.data import Customer

class DataRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add_many(self, customers: list[Customer]) -> int:
        self._session.add_all(customers)
        self._session.commit()
        return len(customers)

    def get_all(self) -> list[Customer]:
        return list(self._session.scalars(select(Customer)).all())

    def count(self) -> int:
        return self._session.scalar(select(func.count()).select_from(Customer)) or 0

    def delete_all(self) -> int:
        result = cast(CursorResult[Any], self._session.execute(delete(Customer)))
        self._session.commit()
        return result.rowcount

    def existing_customer_ids(self, ids: list[str]) -> set[str]:
        stmt = select(Customer.customer_id).where(Customer.customer_id.in_(ids))
        return set(self._session.scalars(stmt).all())