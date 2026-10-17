import uuid
from datetime import datetime

from sqlalchemy import Uuid, DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base

class ModelRun(Base):
    __tablename__ = "model_runs"
    
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    trained_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    n_rows: Mapped[int] = mapped_column(Integer)
    roc_auc: Mapped[float] = mapped_column(Float)
    model_path: Mapped[str] = mapped_column(String)