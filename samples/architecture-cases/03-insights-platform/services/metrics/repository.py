from services.metrics.database import session
from services.metrics.models import MetricsRecord
class MetricsRepository:
    def save(self, reference: str, amount: float) -> dict:
        with session() as db:
            record = MetricsRecord(reference=reference, amount=amount)
            db.add(record)
            db.commit()
            db.refresh(record)
            return {'id': record.id, 'reference': record.reference, 'status': record.status}
