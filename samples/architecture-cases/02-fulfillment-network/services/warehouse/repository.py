from services.warehouse.database import session
from services.warehouse.models import WarehouseRecord
class WarehouseRepository:
    def save(self, reference: str, amount: float) -> dict:
        with session() as db:
            record = WarehouseRecord(reference=reference, amount=amount)
            db.add(record)
            db.commit()
            db.refresh(record)
            return {'id': record.id, 'reference': record.reference, 'status': record.status}
