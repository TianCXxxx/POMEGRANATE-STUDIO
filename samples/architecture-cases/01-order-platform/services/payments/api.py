from fastapi import APIRouter, Depends
from pydantic import BaseModel
from services.payments.dependencies import get_payments_service
from services.payments.service import PaymentService
router = APIRouter()
class RequestPayload(BaseModel):
    reference: str
    amount: float
@router.post('/payments/charge')
def execute(payload: RequestPayload, service: PaymentService = Depends(get_payments_service)):
    return service.execute(payload.reference, payload.amount)
