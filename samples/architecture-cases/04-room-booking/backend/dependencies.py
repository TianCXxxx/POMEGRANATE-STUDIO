from backend.database import BookingDatabase
from backend.notifications import NotificationService
from backend.repository import BookingRepository, RoomRepository
from backend.services import BookingService, RoomService

database = BookingDatabase("meeting_rooms.db")
rooms = RoomRepository(database)
bookings = BookingRepository(database)
notifier = NotificationService()


def get_room_service() -> RoomService:
    return RoomService(rooms)


def get_booking_service() -> BookingService:
    return BookingService(bookings, rooms, notifier)
