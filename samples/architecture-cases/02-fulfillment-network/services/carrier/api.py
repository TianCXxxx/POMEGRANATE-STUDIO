from fastapi import APIRouter, Depends
from pydantic import BaseModel
from services.carrier.dependencies import get_carrier_service
from services.carrier.service import CarrierService
router = APIRouter()
class RequestPayload(BaseModel):
    reference: str
    amount: float
@router.post('/carrier/book')
def execute(payload: RequestPayload, service: CarrierService = Depends(get_carrier_service)):
    return service.execute(payload.reference, payload.amount)
