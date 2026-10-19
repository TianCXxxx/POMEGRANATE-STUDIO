import sqlite3
from contextlib import closing


class BookingDatabase:
    def __init__(self, filename: str):
        self.filename = filename

    def connect(self):
        connection = sqlite3.connect(self.filename)
        connection.row_factory = sqlite3.Row
        return connection

    def initialize(self):
        with closing(self.connect()) as connection, connection:
            connection.executescript("""
                CREATE TABLE IF NOT EXISTS rooms (id INTEGER PRIMARY KEY, name TEXT NOT NULL, seats INTEGER NOT NULL);
                CREATE TABLE IF NOT EXISTS bookings (
                    id INTEGER PRIMARY KEY, room_id INTEGER NOT NULL, booker TEXT NOT NULL, slot TEXT NOT NULL,
                    UNIQUE(room_id, slot)
                );
                INSERT OR IGNORE INTO rooms VALUES (1, '石榴会议室', 8), (2, '橙子会议室', 12), (3, '青柠会议室', 4);
            """)
