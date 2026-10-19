from backend.notifications import NotificationService
from backend.repository import BookingRepository, RoomRepository


class RoomService:
    def __init__(self, rooms: RoomRepository):
        self.rooms = rooms

    def list_rooms(self):
        return self.rooms.list_rooms()


class BookingService:
    def __init__(self, bookings: BookingRepository, rooms: RoomRepository, notifier: NotificationService):
        self.bookings = bookings
        self.rooms = rooms
        self.notifier = notifier

    def reserve(self, room_id: int, booker: str, slot: str):
        room = self.rooms.find(room_id)
        if not room:
            raise ValueError("会议室不存在")
        booking = self.bookings.save(room_id, booker, slot)
        self.notifier.send_confirmation(booking, room)
        return booking

    def list_bookings(self):
        return self.bookings.list_bookings()
