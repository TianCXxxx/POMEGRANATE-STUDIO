from services.tracking.database import session
from services.tracking.models import TrackingRecord
class TrackingRepository:
    def save(self, reference: str, amount: float) -> dict:
        with session() as db:
            record = TrackingRecord(reference=reference, amount=amount)
            db.add(record)
            db.commit()
            db.refresh(record)
            return {'id': record.id, 'reference': record.reference, 'status': record.status}
