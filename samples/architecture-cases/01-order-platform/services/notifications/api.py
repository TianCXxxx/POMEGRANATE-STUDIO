from fastapi import APIRouter, Depends
from pydantic import BaseModel
from services.notifications.dependencies import get_notifications_service
from services.notifications.service import NotificationService
router = APIRouter()
class RequestPayload(BaseModel):
    reference: str
    amount: float
@router.post('/notifications')
def execute(payload: RequestPayload, service: NotificationService = Depends(get_notifications_service)):
    return service.execute(payload.reference, payload.amount)
