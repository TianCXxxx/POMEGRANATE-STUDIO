from services.notifications.repository import NotificationRepository
class NotificationService:
    def __init__(self, repository: NotificationRepository):
        self.repository = repository
    def execute(self, reference: str, amount: float) -> dict:
        # Local validation belongs to this service.
        result = self.repository.save(reference, amount)
        return result
