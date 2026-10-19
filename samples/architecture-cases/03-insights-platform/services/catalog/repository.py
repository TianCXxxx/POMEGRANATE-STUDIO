from services.catalog.database import session
from services.catalog.models import CatalogRecord
class CatalogRepository:
    def save(self, reference: str, amount: float) -> dict:
        with session() as db:
            record = CatalogRecord(reference=reference, amount=amount)
            db.add(record)
            db.commit()
            db.refresh(record)
            return {'id': record.id, 'reference': record.reference, 'status': record.status}
