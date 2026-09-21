"""Order service: delegates to the active repository."""

from app.core.config import settings


class OrderService:
    def __init__(self, repo):
        self.repo = repo

    def list_orders(self, page=1, page_size=20, category=None, returned=None):
        page_size = min(page_size, 100)
        return self.repo.get_orders(page, page_size, category, returned)
