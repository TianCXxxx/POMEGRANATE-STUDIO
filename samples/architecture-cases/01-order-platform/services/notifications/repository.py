from services.notifications.database import session
from services.notifications.models import NotificationRecord
class NotificationRepository:
    def save(self, reference: str, amount: float) -> dict:
        with session() as db:
            record = NotificationRecord(reference=reference, amount=amount)
            db.add(record)
            db.commit()
            db.refresh(record)
            return {'id': record.id, 'reference': record.reference, 'status': record.status}
