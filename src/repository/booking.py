import uuid
from datetime import date

from fastapi import Depends
from sqlalchemy import UUID, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models import Booking, User
from src.models.payments import PaymentStatus
from src.schemas.user import UserProfileSchema, UserResponseSchema
from src.services.auth import auth_service
from src.repository import user as repo_user
from src.repository import cart as repo_cart
from src.repository import car as repo_car
from src.repository import payment as repo_payment
from src.models.bookings import BookingStatus, BookingHistory


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
        payment_id: UUID,
        user_id: UUID,
        car_id: UUID,
        redis,
):
    cart = await repo_cart.get_cart(redis, user_id)

    booking_creation_json = {
        'user_id': str(user_id),
        'car_id': str(car_id),
        'payment': str(payment_id),
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
        redis):
    stmt = (
        select(Booking)
        .join(User)
        .where(User.id == user_id)
    )
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        return None

    unc_booking = await get_unconfirmed_booking(user_id, redis)

    is_payed = await repo_payment.get_payment_by_id(unc_booking[0]["payment"], db)
    if not is_payed.status == PaymentStatus.success:
        return is_payed.status

    booking = Booking(
        status=BookingStatus.confirmed,
        car_id=unc_booking[0]["car_id"],
        user_id=unc_booking[0]["user_id"],
        start_date=date.fromisoformat(unc_booking[0]["start_time"]),
        end_date = date.fromisoformat(unc_booking[0]["end_time"]),
        delivery_address=unc_booking[0]["delivery_address"],
        total_price=unc_booking[0]["total_price"],
        payment_id=unc_booking[0]["payment"]
    )

    db.add(booking)
    await db.commit()
    return booking


async def delete_booking_by_id(booking_id : UUID, db: AsyncSession):
    stmt = select(Booking).where(Booking.id == booking_id)
    result = await db.execute(stmt)
    booking = result.scalar_one_or_none()
    if booking is None:
        return None
    await db.delete(booking)
    await db.commit()
    return True


async def add_booking_to_history(booking_price: int,booking_id: UUID, user_id: UUID, car_id: UUID, payment_id: UUID, db: AsyncSession):
    booking_history = BookingHistory(booking_id=booking_id, user_id=user_id, car_id=car_id, status=BookingStatus.done, payment_id=payment_id, booking_price=booking_price)
    db.add(booking_history)
    await db.commit()
    await db.refresh(booking_history)
    return booking_history
