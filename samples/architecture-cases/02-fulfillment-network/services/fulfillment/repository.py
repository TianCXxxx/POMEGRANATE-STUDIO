from services.fulfillment.database import session
from services.fulfillment.models import FulfillmentRecord
class FulfillmentRepository:
    def save(self, reference: str, amount: float) -> dict:
        with session() as db:
            record = FulfillmentRecord(reference=reference, amount=amount)
            db.add(record)
            db.commit()
            db.refresh(record)
            return {'id': record.id, 'reference': record.reference, 'status': record.status}
