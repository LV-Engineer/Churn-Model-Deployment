import uuid

from sqlalchemy import Uuid, Float, String, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base

class Customer(Base):
    __tablename__ = "customers"
    
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    customer_id: Mapped[str] = mapped_column(String, unique=True)

    gender: Mapped[str] = mapped_column(String)
    senior_citizen: Mapped[str] = mapped_column(String)
    partner: Mapped[str] = mapped_column(String)
    dependents: Mapped[str] = mapped_column(String)
    tenure_months: Mapped[int] = mapped_column(Integer)
    phone_service: Mapped[str] = mapped_column(String)
    multiple_lines: Mapped[str] = mapped_column(String)
    internet_service: Mapped[str] = mapped_column(String)
    online_security: Mapped[str] = mapped_column(String)
    online_backup: Mapped[str] = mapped_column(String)
    device_protection: Mapped[str] = mapped_column(String)
    tech_support: Mapped[str] = mapped_column(String)
    streaming_tv: Mapped[str] = mapped_column(String)
    streaming_movies: Mapped[str] = mapped_column(String)
    contract: Mapped[str] = mapped_column(String)
    paperless_billing: Mapped[str] = mapped_column(String)
    payment_method: Mapped[str] = mapped_column(String)
    monthly_charges: Mapped[float] = mapped_column(Float)

    churn_value: Mapped[int] = mapped_column(Integer)