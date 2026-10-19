from services.inventory.database import session
from services.inventory.models import InventoryRecord
class InventoryRepository:
    def save(self, reference: str, amount: float) -> dict:
        with session() as db:
            record = InventoryRecord(reference=reference, amount=amount)
            db.add(record)
            db.commit()
            db.refresh(record)
            return {'id': record.id, 'reference': record.reference, 'status': record.status}
