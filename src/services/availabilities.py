from datetime import datetime, timezone, date

from sqlalchemy import UUID, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Booking, User
from src.models.bookings import BookingStatus
from src.repository import booking as repo_booking


async def is_car_booked(car_id: UUID, db: AsyncSession):
    stmt = select(Booking.end_date).where(
        Booking.car_id == car_id,
        Booking.status == BookingStatus.confirmed
    )
    car = await db.execute(stmt)
    car = car.first()

    if car and car.end_date > date.today():
        return True

    return False

