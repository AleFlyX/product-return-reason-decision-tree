"""Model service: loads model artifacts and returns metrics/features/rules."""

import json

from app.core.config import settings


class ModelService:
    def __init__(self, repo):
        self.repo = repo
        self._loaded = False
        self._model = None
        self._version = settings.MODEL_VERSION

    def load_model(self):
        """Load the .joblib model file. In CSV fallback, delegate to repo."""
        if settings.is_csv_fallback:
            self._loaded = self.repo.load_model()
            meta_path = settings.MODEL_METADATA
            if meta_path.exists():
                with open(meta_path, encoding="utf-8-sig") as f:
                    meta = json.load(f)
                self._version = meta.get("model_version", settings.MODEL_VERSION)
            return self._loaded
        try:
            import joblib
            model_path = settings.MODEL_FILE
            if model_path.exists():
                self._model = joblib.load(str(model_path))
                self._loaded = True
            else:
                self._loaded = False
        except Exception:
            self._loaded = False
        return self._loaded

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    @property
    def model_version(self) -> str:
        return self._version

    def get_metrics(self) -> dict:
        return self.repo.get_model_metrics()

    def get_features(self) -> dict:
        return self.repo.get_model_features()

    def get_rules(self, limit: int = 20) -> dict:
        return self.repo.get_model_rules(limit)

    def get_predictions(self, limit: int = 200) -> dict:
        return self.repo.get_model_predictions(limit)
