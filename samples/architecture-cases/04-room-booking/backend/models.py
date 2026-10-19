from pydantic import BaseModel, Field


class BookingRequest(BaseModel):
    room_id: int
    booker: str = Field(min_length=1, max_length=80)
    slot: str = Field(min_length=1, max_length=80)
