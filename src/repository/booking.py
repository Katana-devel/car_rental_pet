from datetime import date

from fastapi import Depends
from sqlalchemy import UUID, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models import Booking, User
from src.schemas.user import UserProfileSchema, UserResponseSchema
from src.services.auth import auth_service
from src.repository import user as repo_user
from src.repository import cart as repo_cart
from src.repository import car as repo_car
from src.models.bookings import BookingStatus


async def get_unconfirmed_booking(
        user_id: UUID ,
        redis
):
    user_id = str(user_id)
    if await redis.json().get(f"booking_by_user_id:{user_id}", "$.car_id"):
        return await redis.json().get(f"booking_by_user_id:{user_id}", "$")
    return None


async def create_unconfirmed_booking(
        address: str,
        user_id: UUID,
        car_id: UUID,
        redis,
):
    cart = await repo_cart.get_cart(redis, user_id)

    booking_creation_json = {
        'user_id': str(user_id),
        'car_id': str(car_id),
        'delivery_address' : address,
        'total_price': cart[0]["total_price"],
        'start_time': cart[0]["start_time"],
        'end_time': cart[0]["end_time"]
    }
    await redis.json().set(f"booking_by_user_id:{user_id}", "$", booking_creation_json)
    await redis.expire(f"booking_by_user_id:{user_id}", 15 * 60)

    return await redis.json().get(f"booking_by_user_id:{user_id}", "$")


async def get_booking_by_user_id(user_id: UUID, db: AsyncSession):
    stmt = (
        select(Booking)
        .join(User)
        .where(User.id == user_id)
    )
    result = await db.execute(stmt)

    return result.scalar_one_or_none()

async def create_booking(
        user_id: UUID ,
        db: AsyncSession,
        redis
):
    unc_booking = await get_unconfirmed_booking(user_id, redis)

    booking = Booking(
        status=BookingStatus.confirmed,
        car_id=unc_booking[0]["car_id"],
        user_id=unc_booking[0]["user_id"],
        start_date=date.fromisoformat(unc_booking[0]["start_time"]),
        end_date = date.fromisoformat(unc_booking[0]["end_time"]),
        delivery_address=unc_booking[0]["delivery_address"],
        total_price=unc_booking[0]["total_price"]
    )

    db.add(booking)
    await db.commit()
    return await get_booking_by_user_id(user_id, db)

