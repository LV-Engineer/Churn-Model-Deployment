from fastapi import APIRouter

router = APIRouter(prefix="/data", tags=["data"])

@router.post("load")
def load_data():
    pass

@router.get("export")
def export_data():
    pass

@router.delete("clear")
def clear_data():
    pass