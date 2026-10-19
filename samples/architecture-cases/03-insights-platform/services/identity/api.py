from fastapi import APIRouter, Depends
from pydantic import BaseModel
from services.identity.dependencies import get_identity_service
from services.identity.service import IdentityService
router = APIRouter()
class RequestPayload(BaseModel):
    reference: str
    amount: float
@router.post('/identity/verify')
def execute(payload: RequestPayload, service: IdentityService = Depends(get_identity_service)):
    return service.execute(payload.reference, payload.amount)
