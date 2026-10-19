from services.reports.repository import ReportRepository
from services.reports.service import ReportService
def get_reports_service() -> ReportService:
    return ReportService(ReportRepository())
