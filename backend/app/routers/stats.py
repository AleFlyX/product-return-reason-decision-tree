"""Statistics router."""

from fastapi import APIRouter

from app.schemas import (
    OverviewStats,
    CategoryStatItem,
    PromotionStatItem,
    PriceRangeStatItem,
)

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/overview")
def overview():
    from app.main import get_stats_service
    svc = get_stats_service()
    return svc.overview()


@router.get("/by-category")
def by_category():
    from app.main import get_stats_service
    svc = get_stats_service()
    return svc.by_category()


@router.get("/by-promotion")
def by_promotion():
    from app.main import get_stats_service
    svc = get_stats_service()
    return svc.by_promotion()


@router.get("/by-price-range")
def by_price_range():
    from app.main import get_stats_service
    svc = get_stats_service()
    return svc.by_price_range()
