from services.payments.repository import PaymentRepository
class PaymentService:
    def __init__(self, repository: PaymentRepository):
        self.repository = repository
    def execute(self, reference: str, amount: float) -> dict:
        # Local validation belongs to this service.
        result = self.repository.save(reference, amount)
        return result
