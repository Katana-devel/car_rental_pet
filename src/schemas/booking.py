from typing import Annotated, Optional, List
from uuid import UUID
from datetime import date, datetime
from pydantic import BaseModel, Field

from src.models.bookings import Booking


class BookingResponseSchema(BaseModel):
    id: UUID
    status: str
    created_at: datetime
    start_time: date
    end_time: date
    delivery_address: str
    total_price: int
    car_id: UUID
    user_id: UUID
    payment_id: Optional[UUID] = None