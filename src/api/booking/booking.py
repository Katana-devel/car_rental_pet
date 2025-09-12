import traceback
from typing import List, Optional, Annotated
from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends, status, Query
from redis import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi_limiter.depends import RateLimiter

from src.core.logger.logger import logger
from src.db.database import get_db
from src.db.redis import get_redis
from src.models.users import Role
from src.repository.booking import get_unconfirmed_booking
from src.schemas.booking import BookingResponseSchema
from src.services.auth import auth_service
from src.services.roles import RoleAccessService
from src.repository import cart as repo_cart
from src.repository import car as repo_car
from src.repository import user as repo_user
from src.repository import booking as repo_booking
from src.services.booking_servis import unconfirmed_booking_exp



only_admin_access = RoleAccessService([Role.admin])

booking_router = APIRouter(prefix='/booking', tags=['booking'])


@booking_router.get("/", dependencies=[Depends(RateLimiter(times=10, seconds=20))])
async def get_unconfirmed_booking(
        redis: Redis = Depends(get_redis),
        user_id: UUID = Depends(auth_service.get_current_user)
):

    booking = await repo_booking.get_unconfirmed_booking(user_id, redis)
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

    return booking


@booking_router.post("/", dependencies=[Depends(RateLimiter(times=10, seconds=20))])
async def create_unconfirmed_booking(
        address: str,
        redis: Redis = Depends(get_redis),
        user_id: UUID = Depends(auth_service.get_current_user),
        db: AsyncSession = Depends(get_db)
):
    cart = await repo_cart.get_cart(redis, user_id) # If cart empty catch exception
    if not cart:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart is empty")
    car_id = cart[0]["car_id"]
    car = await repo_car.get_car(car_id, db)

    if not car.is_active:
        raise HTTPException(status_code=status.HTTP_306_RESERVED, detail="The car is occupied by another user")

    await unconfirmed_booking_exp(redis, user_id, car_id)

    booking = await repo_booking.create_unconfirmed_booking(address, user_id=user_id, car_id=car_id, redis=redis)
    if not booking:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Can't create booking")

    await repo_cart.delete_cart(redis, user_id)

    return await get_unconfirmed_booking(redis, user_id)


@booking_router.get("/{user_id}", response_model=BookingResponseSchema,
                  dependencies=[Depends(RateLimiter(times=10, seconds=20))])
async def get_booking_by_user_id(
        user_id: UUID = Depends(auth_service.get_current_user),
        db: AsyncSession = Depends(get_db)
):
    booking = await repo_booking.get_booking_by_user_id(user_id, db)
    if booking is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="booking is not found db")
    return BookingResponseSchema(
        id=booking.id,
        status=booking.status,
        created_at=booking.created_at,
        start_time=booking.start_date,
        end_time=booking.end_date,
        delivery_address=booking.delivery_address,
        total_price=booking.total_price,
        car_id=booking.car_id,
        user_id=booking.user_id,
        payment_id=booking.payment_id
    )



@booking_router.post("/{user_id}", response_model=BookingResponseSchema,
                  dependencies=[Depends(RateLimiter(times=10, seconds=20))])
async def create_booking(
        user_id: UUID = Depends(auth_service.get_current_user),
        db: AsyncSession = Depends(get_db),
        redis: Redis = Depends(get_redis)
):
    if await get_booking_by_user_id(user_id, db):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already has active booking")

    booking =  await repo_booking.create_booking(user_id, db, redis)
    if not booking:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Can't create booking")

    return await get_booking_by_user_id(user_id, db)


@booking_router.delete("/{user_id}",dependencies=[Depends(RateLimiter(times=10, seconds=20))])
async def delete_booking(
        user_id: UUID = Depends(auth_service.get_current_user),
        db: AsyncSession = Depends(get_db)
):
    booking_delete = await repo_booking.delete_booking(user_id, db)
    if booking_delete is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    return "Booking successfully deleted"

# TODO:
#  -> booking history with using APScheduler