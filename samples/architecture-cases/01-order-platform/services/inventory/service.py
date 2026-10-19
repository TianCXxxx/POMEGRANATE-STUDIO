from services.inventory.repository import InventoryRepository
class InventoryService:
    def __init__(self, repository: InventoryRepository):
        self.repository = repository
    def execute(self, reference: str, amount: float) -> dict:
        # Local validation belongs to this service.
        result = self.repository.save(reference, amount)
        return result
