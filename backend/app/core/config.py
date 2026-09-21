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
    MODEL_VERSION: str = os.getenv("MODEL_VERSION", "")  # 读取自 model_metadata.json

    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    PROJECT_ROOT: Path = BASE_DIR.parent

    MODEL_DIR: Path = PROJECT_ROOT / "model" / "saved"
    MODEL_FILE: Path = MODEL_DIR / "return_decision_tree.joblib"
    MODEL_METRICS: Path = MODEL_DIR / "metrics.json"
    MODEL_FEATURES: Path = MODEL_DIR / "feature_importance.json"
    MODEL_RULES: Path = MODEL_DIR / "rules.json"
    MODEL_METADATA: Path = MODEL_DIR / "model_metadata.json"
    COMPARISON_REPORT: Path = MODEL_DIR / "comparison_report.json"

    CSV_ORDERS: Path = PROJECT_ROOT / "data" / "clean" / "return_model.csv"
    FEATURE_SCHEMA: Path = PROJECT_ROOT / "data" / "reports" / "feature_schema.json"

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
