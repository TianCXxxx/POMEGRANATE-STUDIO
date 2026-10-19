from fastapi import APIRouter, Depends
from pydantic import BaseModel
from services.fulfillment.dependencies import get_fulfillment_service
from services.fulfillment.service import FulfillmentService
router = APIRouter()
class RequestPayload(BaseModel):
    reference: str
    amount: float
@router.post('/fulfillment')
def execute(payload: RequestPayload, service: FulfillmentService = Depends(get_fulfillment_service)):
    return service.execute(payload.reference, payload.amount)
