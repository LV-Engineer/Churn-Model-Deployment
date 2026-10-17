from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.schemas.model import TrainResponse, PredictionResponse, PredictionRequest
from app.services.model import ModelService
from app.core.db import get_db
from app.core.limiter import limiter

router = APIRouter(tags=["model"])

@router.post("/train", response_model=TrainResponse)
@limiter.limit("5/minute")
def train_model(request: Request, db: Session = Depends(get_db)) -> TrainResponse:
    try:
        return ModelService(db).train()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/predict", response_model=PredictionResponse)
@limiter.limit("60/minute")
def make_prediction(
    request: Request, payload: PredictionRequest, db: Session = Depends(get_db)
) -> PredictionResponse:
    try:
        return ModelService(db).predict(payload)
    except LookupError as e:
        raise HTTPException(status_code=503, detail=str(e))