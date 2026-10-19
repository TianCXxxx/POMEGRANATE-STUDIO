from fastapi import APIRouter, Depends
from pydantic import BaseModel
from services.warehouse.dependencies import get_warehouse_service
from services.warehouse.service import WarehouseService
router = APIRouter()
class RequestPayload(BaseModel):
    reference: str
    amount: float
@router.post('/warehouse/allocate')
def execute(payload: RequestPayload, service: WarehouseService = Depends(get_warehouse_service)):
    return service.execute(payload.reference, payload.amount)
