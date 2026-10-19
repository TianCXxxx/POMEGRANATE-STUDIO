from services.tracking.repository import TrackingRepository
from services.tracking.service import TrackingService
def get_tracking_service() -> TrackingService:
    return TrackingService(TrackingRepository())
