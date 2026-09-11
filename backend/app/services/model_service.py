"""Model service: loads model artifacts and returns metrics/features/rules."""

from app.core.config import settings


class ModelService:
    def __init__(self, repo):
        self.repo = repo
        self._loaded = False
        self._model = None

    def load_model(self):
        """Attempt to load the model file. In CSV fallback, model is always 'loaded'."""
        if settings.is_csv_fallback:
            self._loaded = True
            return True
        try:
            import pickle
            model_path = settings.DATA_DIR / "model.pkl"
            if model_path.exists():
                with open(model_path, "rb") as f:
                    self._model = pickle.load(f)
                self._loaded = True
            else:
                self._loaded = False
        except Exception:
            self._loaded = False
        return self._loaded

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    def get_metrics(self) -> dict:
        return self.repo.get_model_metrics()

    def get_features(self) -> dict:
        return self.repo.get_model_features()

    def get_rules(self, limit: int = 20) -> dict:
        return self.repo.get_model_rules(limit)

    def get_predictions(self, limit: int = 200) -> dict:
        return self.repo.get_model_predictions(limit)
