from services.carrier.database import session
from services.carrier.models import CarrierRecord
class CarrierRepository:
    def save(self, reference: str, amount: float) -> dict:
        with session() as db:
            record = CarrierRecord(reference=reference, amount=amount)
            db.add(record)
            db.commit()
            db.refresh(record)
            return {'id': record.id, 'reference': record.reference, 'status': record.status}
