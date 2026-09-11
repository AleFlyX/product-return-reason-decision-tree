"""Prediction service: runs model inference or falls back to rule-based."""

from app.core.config import settings
from app.core.errors import ModelNotLoadedError


class PredictionService:
    def __init__(self, repo, model_service):
        self.repo = repo
        self.model_service = model_service

    def predict(self, payload: dict) -> dict:
        if not self.model_service.is_loaded:
            raise ModelNotLoadedError("Model is not loaded; prediction is unavailable")
        return self.repo.predict(payload)
