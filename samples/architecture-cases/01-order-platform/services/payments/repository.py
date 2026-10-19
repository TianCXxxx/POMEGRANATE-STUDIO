from services.payments.database import session
from services.payments.models import PaymentRecord
class PaymentRepository:
    def save(self, reference: str, amount: float) -> dict:
        with session() as db:
            record = PaymentRecord(reference=reference, amount=amount)
            db.add(record)
            db.commit()
            db.refresh(record)
            return {'id': record.id, 'reference': record.reference, 'status': record.status}
