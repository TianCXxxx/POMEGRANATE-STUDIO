from services.orders.database import session
from services.orders.models import OrderRecord
class OrderRepository:
    def save(self, reference: str, amount: float) -> dict:
        with session() as db:
            record = OrderRecord(reference=reference, amount=amount)
            db.add(record)
            db.commit()
            db.refresh(record)
            return {'id': record.id, 'reference': record.reference, 'status': record.status}
