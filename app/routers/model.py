from fastapi import APIRouter

router = APIRouter(tags=["model"])

@router.post("/train")
def train_model():
    pass

@router.post("/predict")
def make_prediction():
    pass