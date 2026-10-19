from services.reports.database import session
from services.reports.models import ReportRecord
class ReportRepository:
    def save(self, reference: str, amount: float) -> dict:
        with session() as db:
            record = ReportRecord(reference=reference, amount=amount)
            db.add(record)
            db.commit()
            db.refresh(record)
            return {'id': record.id, 'reference': record.reference, 'status': record.status}
