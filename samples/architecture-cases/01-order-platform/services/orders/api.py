from fastapi import APIRouter, Depends
from pydantic import BaseModel
from services.orders.dependencies import get_orders_service
from services.orders.service import OrderService
router = APIRouter()
class RequestPayload(BaseModel):
    reference: str
    amount: float
@router.post('/orders')
def execute(payload: RequestPayload, service: OrderService = Depends(get_orders_service)):
    return service.execute(payload.reference, payload.amount)
