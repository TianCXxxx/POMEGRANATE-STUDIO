from fastapi import APIRouter, Depends, HTTPException

from backend.dependencies import get_booking_service, get_room_service
from backend.models import BookingRequest
from backend.services import BookingService, RoomService

router = APIRouter()


@router.get("/api/rooms")
def list_rooms(service: RoomService = Depends(get_room_service)):
    return service.list_rooms()


@router.get("/api/bookings")
def list_bookings(service: BookingService = Depends(get_booking_service)):
    return service.list_bookings()


@router.post("/api/bookings")
def book_room(request: BookingRequest, service: BookingService = Depends(get_booking_service)):
    try:
        return service.reserve(request.room_id, request.booker, request.slot)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
