import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

YesNo = Literal["Yes", "No"]
YesNoNoInternet = Literal["Yes", "No", "No internet service"]

class PredictionRequest(BaseModel):
    gender: Literal["Female", "Male"] = Field(serialization_alias="Gender")
    senior_citizen: YesNo = Field(serialization_alias="Senior Citizen")
    partner: YesNo = Field(serialization_alias="Partner")
    dependents: YesNo = Field(serialization_alias="Dependents")
    tenure_months: int = Field(ge=0, le=120, serialization_alias="Tenure Months")
    phone_service: YesNo = Field(serialization_alias="Phone Service")
    multiple_lines: Literal["Yes", "No", "No phone service"] = Field(serialization_alias="Multiple Lines")
    internet_service: Literal["DSL", "Fiber optic", "No"] = Field(serialization_alias="Internet Service")
    online_security: YesNoNoInternet = Field(serialization_alias="Online Security")
    online_backup: YesNoNoInternet = Field(serialization_alias="Online Backup")
    device_protection: YesNoNoInternet = Field(serialization_alias="Device Protection")
    tech_support: YesNoNoInternet = Field(serialization_alias="Tech Support")
    streaming_tv: YesNoNoInternet = Field(serialization_alias="Streaming TV")
    streaming_movies: YesNoNoInternet = Field(serialization_alias="Streaming Movies")
    contract: Literal["Month-to-month", "One year", "Two year"] = Field(serialization_alias="Contract")
    paperless_billing: YesNo = Field(serialization_alias="Paperless Billing")
    payment_method: Literal[
        "Bank transfer (automatic)", "Credit card (automatic)", "Electronic check", "Mailed check"
    ] = Field(serialization_alias="Payment Method")
    monthly_charges: float = Field(ge=0, serialization_alias="Monthly Charges")

class PredictionResponse(BaseModel):
    churn_probability: float = Field(ge=0, le=1)
    contact: bool

class TrainResponse(BaseModel):
    run_id: uuid.UUID
    trained_at: datetime
    n_rows: int
    roc_auc: float