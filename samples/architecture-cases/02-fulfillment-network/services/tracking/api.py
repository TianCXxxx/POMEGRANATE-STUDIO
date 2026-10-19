from fastapi import APIRouter, Depends
from pydantic import BaseModel
from services.tracking.dependencies import get_tracking_service
from services.tracking.service import TrackingService
router = APIRouter()
class RequestPayload(BaseModel):
    reference: str
    amount: float
@router.post('/tracking')
def execute(payload: RequestPayload, service: TrackingService = Depends(get_tracking_service)):
    return service.execute(payload.reference, payload.amount)
