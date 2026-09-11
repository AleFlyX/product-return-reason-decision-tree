"""Model and prediction router."""

from fastapi import APIRouter, Query

from app.schemas import PredictRequest, PredictResponse

router = APIRouter(tags=["model"])


# --- prediction ---

@router.post("/returns/predict")
def predict(req: PredictRequest):
    from app.main import get_prediction_service
    svc = get_prediction_service()
    return svc.predict(req.model_dump())


# --- model endpoints ---

@router.get("/model/metrics")
def model_metrics():
    from app.main import get_model_service
    svc = get_model_service()
    return svc.get_metrics()


@router.get("/model/features")
def model_features():
    from app.main import get_model_service
    svc = get_model_service()
    return svc.get_features()


@router.get("/model/rules")
def model_rules(limit: int = Query(20, ge=1, le=100)):
    from app.main import get_model_service
    svc = get_model_service()
    return svc.get_rules(limit)


@router.get("/model/predictions")
def model_predictions(limit: int = Query(200, ge=1, le=500)):
    from app.main import get_model_service
    svc = get_model_service()
    return svc.get_predictions(limit)
