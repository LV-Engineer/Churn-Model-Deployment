from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, Response
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.limiter import limiter
from app.schemas.monitoring import DriftResponse
from app.services.monitoring import MonitoringService

router = APIRouter(prefix="/monitoring", tags=["monitoring"])

@router.post("/drift", response_model=DriftResponse)
@limiter.limit("10/minute")
def check_drift(
    request: Request, file: UploadFile, db: Session = Depends(get_db)
) -> DriftResponse:
    try:
        return MonitoringService(db).check_drift(file)
    except (ValueError, KeyError) as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/drift/report")
@limiter.limit("10/minute")
def drift_report(
    request: Request, file: UploadFile, db: Session = Depends(get_db)
) -> Response:
    try:
        html = MonitoringService(db).drift_report(file)
    except (ValueError, KeyError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    return Response(
        html,
        media_type="text/html",
        headers={"Content-Disposition": 'attachment; filename="drift_report.html"'},
    )