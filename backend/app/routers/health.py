"""Health check router."""

from fastapi import APIRouter

from app.core.health import check_health

router = APIRouter()


@router.get("/health")
def health():
    from app.main import get_model_service
    ms = get_model_service()
    return check_health(ms.is_loaded, ms.model_version)
