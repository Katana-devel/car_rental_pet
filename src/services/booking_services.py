import json
from datetime import date

from fastapi import Depends, HTTPException, status
from redis import Redis
from sqlalchemy import UUID, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import get_db, sessionmanager
from src.models import Booking
from src.models.bookings import BookingStatus
from src.repository.booking import delete_booking_by_id, add_booking_to_history


async def unconfirmed_booking_exp(redis, user_id: UUID, car_id: UUID):

    lock_key = f"car_locked:{car_id}"
    lock_value = json.dumps({"user_id": str(user_id), "car_id": str(car_id)})

    redis_lock = await redis.set(lock_key, lock_value, ex=15*60, nx=True)
    if not redis_lock:
        raise HTTPException(status_code=status.HTTP_306_RESERVED, detail="Car locked")

    return json.loads(lock_value)



async def booking_history():
    async with sessionmanager.session() as db:
        stmt = select(Booking).where(Booking.status == BookingStatus.confirmed)
        result = await db.execute(stmt)
        bookings = result.scalars().all()

        bookings_list = []
        for booking in bookings:
            if date.today() > booking.end_date > booking.start_date:
                booking_done = await add_booking_to_history(
                    booking_id=booking.id,
                    user_id=booking.user_id,
                    car_id=booking.car_id,
                    db=db,
                )
                if booking_done:
                    await delete_booking_by_id(booking.id, db)
                    bookings_list.append(booking_done)

        return bookings_list
