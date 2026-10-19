from fastapi import APIRouter, Depends
from pydantic import BaseModel
from services.metrics.dependencies import get_metrics_service
from services.metrics.service import MetricsService
router = APIRouter()
class RequestPayload(BaseModel):
    reference: str
    amount: float
@router.post('/metrics')
def execute(payload: RequestPayload, service: MetricsService = Depends(get_metrics_service)):
    return service.execute(payload.reference, payload.amount)
