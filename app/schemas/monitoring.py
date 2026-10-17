from pydantic import BaseModel

class DriftResponse(BaseModel):
    drift_share: float
    drifted_features: list[str]
    alert: bool