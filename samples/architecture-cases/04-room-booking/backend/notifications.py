import logging

logger = logging.getLogger(__name__)


class NotificationService:
    def send_confirmation(self, booking: dict, room: dict):
        # Demo only: this does not send email or call any external service.
        logger.info("Booking confirmed: %s in %s", booking["id"], room["name"])
