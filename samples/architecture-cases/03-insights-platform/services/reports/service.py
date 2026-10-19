from services.reports.repository import ReportRepository
class ReportService:
    def __init__(self, repository: ReportRepository):
        self.repository = repository
    def execute(self, reference: str, amount: float) -> dict:
        # Local validation belongs to this service.
        result = self.repository.save(reference, amount)
        return result
