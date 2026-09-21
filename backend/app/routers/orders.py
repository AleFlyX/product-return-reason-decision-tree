"""Orders router."""

from fastapi import APIRouter, Query

from app.schemas import OrderListResponse

router = APIRouter(prefix="/orders", tags=["orders"])


@router.get("")
def list_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: str | None = Query(None),
    returned: int | None = Query(None, ge=0, le=1),
):
    from app.main import get_order_service
    svc = get_order_service()
    return svc.list_orders(page=page, page_size=page_size, category=category, returned=returned)
