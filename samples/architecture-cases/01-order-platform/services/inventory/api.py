from fastapi import APIRouter, Depends
from pydantic import BaseModel
from services.inventory.dependencies import get_inventory_service
from services.inventory.service import InventoryService
router = APIRouter()
class RequestPayload(BaseModel):
    reference: str
    amount: float
@router.post('/inventory/reserve')
def execute(payload: RequestPayload, service: InventoryService = Depends(get_inventory_service)):
    return service.execute(payload.reference, payload.amount)
