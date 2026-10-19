from services.warehouse.repository import WarehouseRepository
class WarehouseService:
    def __init__(self, repository: WarehouseRepository):
        self.repository = repository
    def execute(self, reference: str, amount: float) -> dict:
        # Local validation belongs to this service.
        result = self.repository.save(reference, amount)
        return result
