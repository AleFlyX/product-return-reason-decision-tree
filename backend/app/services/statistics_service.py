"""Statistics service: delegates to the active repository."""

class StatisticsService:
    def __init__(self, repo):
        self.repo = repo

    def overview(self):
        return self.repo.get_overview()

    def by_category(self):
        return self.repo.get_by_category()

    def by_promotion(self):
        return self.repo.get_by_promotion()

    def by_price_range(self):
        return self.repo.get_by_price_range()
