"""CSV-based fallback repository for local development without HDFS/HBase."""

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.core.config import settings


class CSVFallbackRepository:
    """Reads mock data from local files when HDFS/HBase are unavailable."""

    def __init__(self) -> None:
        self.data_dir = settings.DATA_DIR
        self.data_dir.mkdir(parents=True, exist_ok=True)

    # --- helpers ---

    @staticmethod
    def _read_json(path: Path) -> Any:
        if not path.exists():
            return {}
        with open(path, encoding="utf-8-sig") as f:
            return json.load(f)

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # --- orders ---

    def get_orders(
        self,
        page: int = 1,
        page_size: int = 20,
        category: str | None = None,
        returned: int | None = None,
    ) -> dict:
        path = settings.CSV_ORDERS
        if not path.exists():
            return {"items": [], "page": page, "page_size": page_size, "total": 0}

        rows: list[dict] = []
        with open(path, encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for r in reader:
                r["price"] = float(r["price"])
                r["is_promotion"] = int(r["is_promotion"])
                r["freight"] = float(r["freight"])
                r["returned"] = int(r["returned"])
                if category and r["category"] != category:
                    continue
                if returned is not None and r["returned"] != returned:
                    continue
                rows.append(r)

        total = len(rows)
        start = (page - 1) * page_size
        end = start + page_size
        return {
            "items": rows[start:end],
            "page": page,
            "page_size": page_size,
            "total": total,
        }

    # --- stats ---

    def get_overview(self) -> dict:
        data = self._read_json(settings.STATS_OVERVIEW)
        if not data:
            return {
                "sample_count": 0,
                "returned_count": 0,
                "return_rate": 0.0,
                "category_count": 0,
                "average_price": 0.0,
                "average_freight": 0.0,
                "updated_at": self._now(),
            }
        return data

    def get_by_category(self) -> dict:
        data = self._read_json(settings.STATS_CATEGORY)
        if not data:
            return {"items": []}
        return data

    def get_by_promotion(self) -> dict:
        data = self._read_json(settings.STATS_PROMOTION)
        if not data:
            return {"items": []}
        return data

    def get_by_price_range(self) -> dict:
        data = self._read_json(settings.STATS_PRICE)
        if not data:
            return {"items": []}
        return data

    # --- model files ---

    def get_model_metrics(self) -> dict:
        return self._read_json(settings.MODEL_METRICS)

    def get_model_features(self) -> dict:
        return self._read_json(settings.MODEL_FEATURES)

    def get_model_rules(self, limit: int = 20) -> dict:
        data = self._read_json(settings.MODEL_RULES)
        if not data:
            return {"items": []}
        items = data.get("items", [])[:limit]
        return {"items": items}

    def get_model_predictions(self, limit: int = 200) -> dict:
        data = self._read_json(settings.MODEL_PREDICTIONS)
        if not data:
            return {"items": []}
        items = data.get("items", [])[:limit]
        return {"items": items}

    # --- prediction (mock) ---

    def predict(self, payload: dict) -> dict:
        """Simple rule-based mock prediction for local development."""
        is_promo = payload.get("is_promotion", 0)
        price = payload.get("price", 200)
        prob = 0.15
        if is_promo:
            prob += 0.25
        if price < 100:
            prob += 0.20
        prob = min(prob, 0.95)
        predicted = 1 if prob >= 0.5 else 0
        return {
            "predicted_returned": predicted,
            "return_probability": round(prob, 4),
            "class_probabilities": {
                "not_returned": round(1 - prob, 4),
                "returned": round(prob, 4),
            },
            "model": settings.MODEL_NAME,
            "model_version": settings.MODEL_VERSION,
        }
