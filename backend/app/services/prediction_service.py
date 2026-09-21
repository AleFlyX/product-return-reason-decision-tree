"""Prediction service: runs model inference via the active repository."""

from app.core.config import settings
from app.core.errors import ModelNotLoadedError


class PredictionService:
    def __init__(self, repo, model_service):
        self.repo = repo
        self.model_service = model_service

    def predict(self, payload: dict) -> dict:
        if not self.model_service.is_loaded:
            raise ModelNotLoadedError("Model is not loaded; prediction is unavailable")
        result = self.repo.predict(payload)
        result["model_version"] = self.model_service.model_version
        return result
