from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, Query, Response
from sqlalchemy.orm import Session

from app.schemas.data import UploadResponse, DeleteResponse
from app.services.data import DataService
from app.core.db import get_db
from app.core.limiter import limiter

router = APIRouter(prefix="/data", tags=["data"])

@router.post("/load", response_model=UploadResponse)
@limiter.limit("60/minute")
def load_data(request: Request, file: UploadFile, db: Session = Depends(get_db)) -> UploadResponse:
    try:
        return DataService(db).upload(file)
    except (ValueError, KeyError) as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/export")
@limiter.limit("60/minute")
def export_data(
    request: Request,
    fmt: Literal["csv", "parquet"] = Query("csv", alias="format"),
    db: Session = Depends(get_db),
) -> Response:
    content = DataService(db).export(fmt)
    media_type = "text/csv" if fmt == "csv" else "application/octet-stream"
    return Response(
        content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="customers.{fmt}"'},
    )

@router.delete("/clear", response_model=DeleteResponse)
@limiter.limit("60/minute")
def clear_data(request: Request, db: Session = Depends(get_db)) -> DeleteResponse:
    return DataService(db).clear()