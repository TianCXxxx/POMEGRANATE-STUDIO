from fastapi import APIRouter, Depends
from pydantic import BaseModel
from services.reports.dependencies import get_reports_service
from services.reports.service import ReportService
router = APIRouter()
class RequestPayload(BaseModel):
    reference: str
    amount: float
@router.post('/reports')
def execute(payload: RequestPayload, service: ReportService = Depends(get_reports_service)):
    return service.execute(payload.reference, payload.amount)
