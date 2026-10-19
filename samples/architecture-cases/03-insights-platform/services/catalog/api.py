from fastapi import APIRouter, Depends
from pydantic import BaseModel
from services.catalog.dependencies import get_catalog_service
from services.catalog.service import CatalogService
router = APIRouter()
class RequestPayload(BaseModel):
    reference: str
    amount: float
@router.post('/catalog/query')
def execute(payload: RequestPayload, service: CatalogService = Depends(get_catalog_service)):
    return service.execute(payload.reference, payload.amount)
