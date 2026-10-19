from services.catalog.repository import CatalogRepository
class CatalogService:
    def __init__(self, repository: CatalogRepository):
        self.repository = repository
    def execute(self, reference: str, amount: float) -> dict:
        # Local validation belongs to this service.
        result = self.repository.save(reference, amount)
        return result
