from services.identity.database import session
from services.identity.models import IdentityRecord
class IdentityRepository:
    def save(self, reference: str, amount: float) -> dict:
        with session() as db:
            record = IdentityRecord(reference=reference, amount=amount)
            db.add(record)
            db.commit()
            db.refresh(record)
            return {'id': record.id, 'reference': record.reference, 'status': record.status}
