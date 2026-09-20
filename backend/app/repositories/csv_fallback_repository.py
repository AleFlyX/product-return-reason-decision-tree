"""CSV-based fallback repository reading real model artifacts and order data."""

import csv
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.core.config import settings


class CSVFallbackRepository:
    """Reads real data from local files when HDFS/HBase are unavailable."""

    def __init__(self) -> None:
        self._model = None
        self._model_loaded = False
        self._encoded_features = None
        self._category_values = None
        self._season_values = None

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

    def _read_orders_csv(self) -> list[dict]:
        """Read the real orders CSV and return a list of dicts with typed fields."""
        path = settings.CSV_ORDERS
        if not path.exists():
            return []
        rows: list[dict] = []
        with open(path, encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for i, r in enumerate(reader, start=1):
                rows.append({
                    "order_id": str(i),
                    "category": r["category"],
                    "price": float(r["price"]),
                    "is_promotion": int(r["is_promotion"]),
                    "season": r["season"],
                    "freight": float(r["freight"]),
                    "returned": int(r["returned"]),
                })
        return rows

    # --- orders ---

    def get_orders(
        self,
        page: int = 1,
        page_size: int = 20,
        category: str | None = None,
        returned: int | None = None,
    ) -> dict:
        rows = self._read_orders_csv()
        if category:
            rows = [r for r in rows if r["category"] == category]
        if returned is not None:
            rows = [r for r in rows if r["returned"] == returned]
        total = len(rows)
        start = (page - 1) * page_size
        end = start + page_size
        return {
            "items": rows[start:end],
            "page": page,
            "page_size": page_size,
            "total": total,
        }

    # --- stats (calculated dynamically from CSV) ---

    def get_overview(self) -> dict:
        rows = self._read_orders_csv()
        if not rows:
            return {
                "sample_count": 0,
                "returned_count": 0,
                "return_rate": 0.0,
                "category_count": 0,
                "average_price": 0.0,
                "average_freight": 0.0,
                "updated_at": self._now(),
            }
        total = len(rows)
        returned = sum(1 for r in rows if r["returned"] == 1)
        categories = {r["category"] for r in rows}
        avg_price = sum(r["price"] for r in rows) / total
        avg_freight = sum(r["freight"] for r in rows) / total
        return {
            "sample_count": total,
            "returned_count": returned,
            "return_rate": round(returned / total, 4),
            "category_count": len(categories),
            "average_price": round(avg_price, 2),
            "average_freight": round(avg_freight, 2),
            "updated_at": self._now(),
        }

    def get_by_category(self) -> dict:
        rows = self._read_orders_csv()
        groups: dict[str, list] = {}
        for r in rows:
            groups.setdefault(r["category"], []).append(r)
        items = []
        for cat in sorted(groups):
            items_list = groups[cat]
            cnt = len(items_list)
            ret = sum(1 for r in items_list if r["returned"] == 1)
            items.append({
                "category": cat,
                "sample_count": cnt,
                "returned_count": ret,
                "return_rate": round(ret / cnt, 4) if cnt else 0.0,
            })
        return {"items": items}

    def get_by_promotion(self) -> dict:
        rows = self._read_orders_csv()
        groups: dict[int, list] = {0: [], 1: []}
        for r in rows:
            groups.setdefault(r["is_promotion"], []).append(r)
        items = []
        for promo in sorted(groups):
            items_list = groups[promo]
            cnt = len(items_list)
            ret = sum(1 for r in items_list if r["returned"] == 1)
            items.append({
                "is_promotion": promo,
                "sample_count": cnt,
                "returned_count": ret,
                "return_rate": round(ret / cnt, 4) if cnt else 0.0,
            })
        return {"items": items}

    def get_by_price_range(self) -> dict:
        rows = self._read_orders_csv()
        ranges = [
            ("0-50", 0, 50),
            ("50-100", 50, 100),
            ("100-200", 100, 200),
            ("200+", 200, float("inf")),
        ]
        items = []
        for label, lo, hi in ranges:
            subset = [r for r in rows if lo <= r["price"] < hi]
            cnt = len(subset)
            ret = sum(1 for r in subset if r["returned"] == 1)
            items.append({
                "price_range": label,
                "sample_count": cnt,
                "returned_count": ret,
                "return_rate": round(ret / cnt, 4) if cnt else 0.0,
            })
        return {"items": items}

    # --- model files ---

    def get_model_metrics(self) -> dict:
        data = self._read_json(settings.MODEL_METRICS)
        if not data:
            return {}
        meta = self._read_json(settings.MODEL_METADATA)
        return {
            "model": settings.MODEL_NAME,
            "model_version": meta.get("model_version", settings.MODEL_VERSION),
            "accuracy": data.get("test_accuracy", 0.0),
            "precision": data.get("test_precision", 0.0),
            "recall": data.get("test_recall", 0.0),
            "f1": data.get("test_f1", 0.0),
            "confusion_matrix": data.get("confusion_matrix", []),
            "train_samples": data.get("train_samples", 0),
            "test_samples": data.get("test_samples", 0),
            "returned_rate_test": data.get("returned_rate_test", 0.0),
        }

    def get_model_features(self) -> dict:
        data = self._read_json(settings.MODEL_FEATURES)
        if isinstance(data, list):
            items = [{"feature": d["feature"], "importance": d["importance"]} for d in data]
            return {"items": items}
        return data if data else {"items": []}

    def get_model_rules(self, limit: int = 20) -> dict:
        data = self._read_json(settings.MODEL_RULES)
        if isinstance(data, list):
            return {"items": data[:limit]}
        if isinstance(data, dict) and "items" in data:
            return {"items": data["items"][:limit]}
        return {"items": []}

    def get_model_predictions(self, limit: int = 200) -> dict:
        return {"items": []}

    # --- model loading and prediction ---

    def load_model(self) -> bool:
        """Load the .joblib model and feature schema for encoding."""
        model_path = settings.MODEL_FILE
        if not model_path.exists():
            self._model_loaded = False
            return False
        try:
            import warnings
            warnings.filterwarnings("ignore")
            import joblib
            self._model = joblib.load(str(model_path))
            self._model_loaded = True
            self._load_feature_schema()
        except Exception:
            self._model_loaded = False
        return self._model_loaded

    def _load_feature_schema(self):
        """Load feature schema to know the encoding for prediction."""
        schema = self._read_json(settings.FEATURE_SCHEMA)
        self._encoded_features = schema.get("encoded_feature_names", [])
        cat_vals = schema.get("category_values", {})
        self._category_values = cat_vals.get("category", [])
        self._season_values = cat_vals.get("season", [])

    @property
    def is_model_loaded(self) -> bool:
        return self._model_loaded

    def _is_pipeline(self) -> bool:
        """Check if the loaded model is a sklearn Pipeline."""
        return hasattr(self._model, "named_steps") or (
            hasattr(self._model, "steps") and hasattr(self._model, "transform")
        )

    def _encode_input_pipeline(self, payload: dict):
        """Encode input for a Pipeline (feeds raw data, pipeline handles encoding)."""
        import pandas as pd
        return pd.DataFrame([{
            "category": payload["category"],
            "price": payload["price"],
            "is_promotion": payload["is_promotion"],
            "season": payload["season"],
            "freight": payload["freight"],
        }])

    def _encode_input_manual(self, payload: dict):
        """Manually One-Hot encode input for a bare DecisionTreeClassifier."""
        import numpy as np
        features = self._encoded_features
        if not features:
            return None
        vec = [0.0] * len(features)
        for i, fname in enumerate(features):
            if fname.startswith("categorical__category_"):
                cat = fname.replace("categorical__category_", "")
                if payload["category"] == cat:
                    vec[i] = 1.0
            elif fname.startswith("categorical__season_"):
                season = fname.replace("categorical__season_", "")
                if payload["season"] == season:
                    vec[i] = 1.0
            elif fname == "numeric__price":
                vec[i] = float(payload["price"])
            elif fname == "numeric__is_promotion":
                vec[i] = float(payload["is_promotion"])
            elif fname == "numeric__freight":
                vec[i] = float(payload["freight"])
        return np.array([vec])

    def predict(self, payload: dict) -> dict:
        """Run real model prediction using the loaded .joblib model."""
        if not self._model_loaded or self._model is None:
            return self._mock_predict(payload)
        try:
            if self._is_pipeline():
                X = self._encode_input_pipeline(payload)
            else:
                X = self._encode_input_manual(payload)
                if X is None:
                    return self._mock_predict(payload)
            pred = int(self._model.predict(X)[0])
            proba = self._model.predict_proba(X)[0]
            if len(proba) == 2:
                prob_returned = round(float(proba[1]), 4)
                prob_not = round(float(proba[0]), 4)
            else:
                prob_returned = round(float(proba[pred]), 4)
                prob_not = round(1.0 - prob_returned, 4)
            return {
                "predicted_returned": pred,
                "return_probability": prob_returned,
                "class_probabilities": {
                    "not_returned": prob_not,
                    "returned": prob_returned,
                },
                "model": settings.MODEL_NAME,
                "model_version": settings.MODEL_VERSION,
            }
        except Exception:
            return self._mock_predict(payload)

    def _mock_predict(self, payload: dict) -> dict:
        """Rule-based fallback when model cannot be loaded."""
        prob = 0.15
        if payload.get("is_promotion"):
            prob += 0.25
        if payload.get("price", 200) < 100:
            prob += 0.20
        prob = min(prob, 0.95)
        return {
            "predicted_returned": 1 if prob >= 0.5 else 0,
            "return_probability": round(prob, 4),
            "class_probabilities": {
                "not_returned": round(1 - prob, 4),
                "returned": round(prob, 4),
            },
            "model": settings.MODEL_NAME,
            "model_version": settings.MODEL_VERSION,
        }
