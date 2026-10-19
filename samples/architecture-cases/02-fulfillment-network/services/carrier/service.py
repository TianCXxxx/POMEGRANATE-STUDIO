from services.carrier.repository import CarrierRepository
class CarrierService:
    def __init__(self, repository: CarrierRepository):
        self.repository = repository
    def execute(self, reference: str, amount: float) -> dict:
        # Local validation belongs to this service.
        result = self.repository.save(reference, amount)
        return result
