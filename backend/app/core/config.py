"""Application settings and environment configuration."""

import os
from pathlib import Path


class Settings:
    """Centralized configuration loaded from environment variables."""

    APP_ENV: str = os.getenv("APP_ENV", "development")
    DATA_BACKEND: str = os.getenv("DATA_BACKEND", "csv_fallback")

    HDFS_URL: str = os.getenv("HDFS_URL", "hdfs://namenode:8020")
    HDFS_ROOT: str = os.getenv("HDFS_ROOT", "/project/product-return")

    HBASE_HOST: str = os.getenv("HBASE_HOST", "localhost")
    HBASE_PORT: int = int(os.getenv("HBASE_PORT", "9090"))
    HBASE_ORDERS_TABLE: str = os.getenv("HBASE_ORDERS_TABLE", "pr_orders")
    HBASE_MODEL_TABLE: str = os.getenv("HBASE_MODEL_TABLE", "pr_model_registry")
    HBASE_STATS_TABLE: str = os.getenv("HBASE_STATS_TABLE", "pr_stats")
    HBASE_PREDICTIONS_TABLE: str = os.getenv("HBASE_PREDICTIONS_TABLE", "pr_predictions")

    MODEL_NAME: str = os.getenv("MODEL_NAME", "decision-tree")
    MODEL_VERSION: str = os.getenv("MODEL_VERSION", "dt-20260910-001")

    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    DATA_DIR: Path = Path(os.getenv("DATA_DIR", str(BASE_DIR / "data")))
    CSV_ORDERS: Path = DATA_DIR / "mock_orders.csv"
    MODEL_METRICS: Path = DATA_DIR / "mock_model_metrics.json"
    MODEL_FEATURES: Path = DATA_DIR / "mock_model_features.json"
    MODEL_RULES: Path = DATA_DIR / "mock_model_rules.json"
    MODEL_PREDICTIONS: Path = DATA_DIR / "mock_model_predictions.json"
    STATS_OVERVIEW: Path = DATA_DIR / "mock_stats_overview.json"
    STATS_CATEGORY: Path = DATA_DIR / "mock_stats_category.json"
    STATS_PROMOTION: Path = DATA_DIR / "mock_stats_promotion.json"
    STATS_PRICE: Path = DATA_DIR / "mock_stats_price.json"

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    @property
    def is_csv_fallback(self) -> bool:
        return self.DATA_BACKEND == "csv_fallback"

    @property
    def degraded(self) -> bool:
        return self.is_csv_fallback


settings = Settings()
