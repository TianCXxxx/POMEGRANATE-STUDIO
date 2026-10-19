from services.tracking.repository import TrackingRepository
class TrackingService:
    def __init__(self, repository: TrackingRepository):
        self.repository = repository
    def execute(self, reference: str, amount: float) -> dict:
        # Local validation belongs to this service.
        result = self.repository.save(reference, amount)
        return result
