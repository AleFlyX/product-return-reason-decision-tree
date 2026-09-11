"""FastAPI application entry point with dependency injection."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.errors import (
    ServiceUnavailableError,
    ModelNotLoadedError,
    service_unavailable_handler,
    model_not_loaded_handler,
)
from app.core.logging import logger

# --- repository singleton ---
_repo = None
_model_service = None
_order_service = None
_stats_service = None
_prediction_service = None


def _build_repo():
    global _repo
    if _repo is not None:
        return _repo
    if settings.is_csv_fallback:
        from app.repositories.csv_fallback_repository import CSVFallbackRepository
        _repo = CSVFallbackRepository()
        logger.info("Using CSV fallback repository (local dev mode)")
    else:
        from app.repositories.hbase_repository import HBaseRepository
        _repo = HBaseRepository()
        logger.info("Using HBase repository (production mode)")
    return _repo


def get_order_service():
    global _order_service
    if _order_service is None:
        from app.services.order_service import OrderService
        _order_service = OrderService(_build_repo())
    return _order_service


def get_stats_service():
    global _stats_service
    if _stats_service is None:
        from app.services.statistics_service import StatisticsService
        _stats_service = StatisticsService(_build_repo())
    return _stats_service


def get_model_service():
    global _model_service
    if _model_service is None:
        from app.services.model_service import ModelService
        _model_service = ModelService(_build_repo())
        _model_service.load_model()
    return _model_service


def get_prediction_service():
    global _prediction_service
    if _prediction_service is None:
        from app.services.prediction_service import PredictionService
        _prediction_service = PredictionService(_build_repo(), get_model_service())
    return _prediction_service


# --- app ---

app = FastAPI(
    title="商品退货原因分析 API",
    description="Product Return Reason Analysis - Decision Tree Backend",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(ServiceUnavailableError, service_unavailable_handler)
app.add_exception_handler(ModelNotLoadedError, model_not_loaded_handler)

# --- register routers ---
from app.routers import health, stats, orders, model

api_prefix = "/api"
app.include_router(health.router, prefix=api_prefix)
app.include_router(stats.router, prefix=api_prefix)
app.include_router(orders.router, prefix=api_prefix)
app.include_router(model.router, prefix=api_prefix)


@app.get("/")
def root():
    return {"service": "product-return-analysis-api", "docs": "/docs"}


@app.on_event("startup")
def startup():
    logger.info(f"Starting app | env={settings.APP_ENV} | backend={settings.DATA_BACKEND}")
    _build_repo()
    get_model_service()
    logger.info(f"Model loaded: {get_model_service().is_loaded}")
