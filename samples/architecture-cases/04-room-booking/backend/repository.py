import sqlite3
from contextlib import closing

from backend.database import BookingDatabase


class RoomRepository:
    def __init__(self, database: BookingDatabase):
        self.database = database

    def list_rooms(self):
        with closing(self.database.connect()) as connection, connection:
            return [dict(row) for row in connection.execute("SELECT id, name, seats FROM rooms ORDER BY id")]

    def find(self, room_id: int):
        with closing(self.database.connect()) as connection, connection:
            row = connection.execute("SELECT id, name, seats FROM rooms WHERE id = ?", (room_id,)).fetchone()
            return dict(row) if row else None


class BookingRepository:
    def __init__(self, database: BookingDatabase):
        self.database = database

    def list_bookings(self):
        with closing(self.database.connect()) as connection, connection:
            return [dict(row) for row in connection.execute("SELECT id, room_id, booker, slot FROM bookings ORDER BY id DESC")]

    def save(self, room_id: int, booker: str, slot: str):
        try:
            with closing(self.database.connect()) as connection, connection:
                cursor = connection.execute("INSERT INTO bookings (room_id, booker, slot) VALUES (?, ?, ?)", (room_id, booker, slot))
                return {"id": cursor.lastrowid, "room_id": room_id, "booker": booker, "slot": slot}
        except sqlite3.IntegrityError as error:
            raise ValueError("会议室在该时段已被预约") from error
