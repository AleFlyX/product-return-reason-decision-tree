"""Health check logic."""

from datetime import datetime, timezone

from app.core.config import settings


def check_health(model_loaded: bool, model_version: str = None) -> dict:
    """Return the health payload required by GET /api/health."""

    version = model_version or settings.MODEL_VERSION

    if settings.is_csv_fallback:
        return {
            "status": "degraded",
            "service": "product-return-analysis-api",
            "model_loaded": model_loaded,
            "model_version": version,
            "dependencies": {
                "hdfs": {"status": "skipped", "root": settings.HDFS_ROOT},
                "hbase": {
                    "status": "skipped",
                    "tables": [
                        settings.HBASE_ORDERS_TABLE,
                        settings.HBASE_MODEL_TABLE,
                        settings.HBASE_STATS_TABLE,
                        settings.HBASE_PREDICTIONS_TABLE,
                    ],
                },
            },
            "degraded": True,
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }

    return {
        "status": "ok",
        "service": "product-return-analysis-api",
        "model_loaded": model_loaded,
        "model_version": version,
        "dependencies": {
            "hdfs": {"status": "ok", "root": settings.HDFS_ROOT},
            "hbase": {
                "status": "ok",
                "tables": [
                    settings.HBASE_ORDERS_TABLE,
                    settings.HBASE_MODEL_TABLE,
                    settings.HBASE_STATS_TABLE,
                    settings.HBASE_PREDICTIONS_TABLE,
                ],
            },
        },
        "degraded": False,
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }
