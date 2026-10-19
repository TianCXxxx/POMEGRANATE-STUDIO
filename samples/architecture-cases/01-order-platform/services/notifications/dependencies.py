from services.notifications.repository import NotificationRepository
from services.notifications.service import NotificationService
def get_notifications_service() -> NotificationService:
    return NotificationService(NotificationRepository())
