from services.identity.repository import IdentityRepository
class IdentityService:
    def __init__(self, repository: IdentityRepository):
        self.repository = repository
    def execute(self, reference: str, amount: float) -> dict:
        # Local validation belongs to this service.
        result = self.repository.save(reference, amount)
        return result
