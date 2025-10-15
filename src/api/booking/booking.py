
from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends, status
from redis import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi_limiter.depends import RateLimiter

from src.db.database import get_db
from src.db.redis import get_redis
from src.models.payments import PaymentStatus
from src.models.users import Role
from src.repository.booking import get_unconfirmed_booking
from src.schemas.booking import BookingResponseSchema
from src.services.auth import auth_service
from src.services.currency.сurrency_decorator import with_currency
from src.services.roles import RoleAccessService
from src.repository import cart as repo_cart
from src.repository import car as repo_car
from src.repository import payment as repo_payment
from src.repository import booking as repo_booking
from src.services.booking_services import unconfirmed_booking_exp



only_admin_access = RoleAccessService([Role.admin])

booking_router = APIRouter(prefix='/booking', tags=['booking'])


@booking_router.get("/", dependencies=[Depends(RateLimiter(times=10, seconds=20)),Depends(only_admin_access)])
@with_currency(["price", "options.options.price", "total_price", "amount"], all_matches=True)
async def get_unconfirmed_booking(
        redis: Redis = Depends(get_redis),
        user_id: UUID = Depends(auth_service.get_current_user),
        db: AsyncSession = Depends(get_db)
):

    booking = await repo_booking.get_unconfirmed_booking(user_id=user_id, redis=redis)
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

    return booking


@booking_router.post("/", dependencies=[Depends(RateLimiter(times=10, seconds=20))])
@with_currency(["price", "options.options.price", "total_price", "amount"], all_matches=True)
async def create_unconfirmed_booking(
        address: str,
        redis: Redis = Depends(get_redis),
        user_id: UUID = Depends(auth_service.get_current_user),
        db: AsyncSession = Depends(get_db)
):
    cart = await repo_cart.get_cart(redis, user_id)
    if not cart:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart is empty")

    car_id = cart[0]["car_id"]
    car = await repo_car.get_car(car_id=car_id, db=db)
    if not car.is_active:
        raise HTTPException(status_code=status.HTTP_306_RESERVED, detail="The car is occupied by another user")

    payment = await repo_payment.create_payment(user_id=user_id, car_id=car_id, amount=cart[0]["total_price"], db=db)
    if not payment:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Can't create a payment")

    await unconfirmed_booking_exp(redis=redis, user_id=user_id, car_id=car_id)

    booking = await repo_booking.create_unconfirmed_booking(address=address, payment_id=payment.id, user_id=user_id, car_id=car_id, redis=redis)
    if not booking:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Can't create booking")

    await repo_cart.delete_cart(redis=redis,user_id=user_id)

    return await get_unconfirmed_booking(redis=redis, user_id=user_id, db=db)


@booking_router.get("/{user_id}", response_model=BookingResponseSchema,
                  dependencies=[Depends(RateLimiter(times=10, seconds=20)),Depends(only_admin_access)])
@with_currency(["price", "options.options.price", "total_price", "amount"], all_matches=True)
async def get_booking_by_user_id(
        user_id: UUID = Depends(auth_service.get_current_user),
        db: AsyncSession = Depends(get_db),
        redis: Redis = Depends(get_redis)
):
    booking = await repo_booking.get_booking_by_user_id(user_id=user_id, db=db, redis=redis)
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
                  dependencies=[Depends(RateLimiter(times=10, seconds=20)),Depends(only_admin_access)])
@with_currency(["price", "options.options.price", "total_price", "amount"], all_matches=True)
async def create_booking(
        total_price: int,
        user_id: UUID = Depends(auth_service.get_current_user),
        db: AsyncSession = Depends(get_db),
        redis: Redis = Depends(get_redis)
):
    if await repo_booking.get_booking_by_user_id(user_id=user_id, db=db, redis=redis):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already has active booking")

    booking =  await repo_booking.create_booking(total_price=total_price,user_id=user_id, db=db, redis=redis)

    if booking == PaymentStatus.pending or booking == PaymentStatus.failed:
        raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail="Payment required")

    if not booking:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Can't create booking")

    return await repo_booking.get_booking_by_user_id(user_id=user_id, db=db, redis=redis)


@booking_router.delete("/}",
                  dependencies=[Depends(RateLimiter(times=10, seconds=20))])
async def cansel_booking(
        booking_id: UUID,
        db: AsyncSession = Depends(get_db)
):
    booking = await repo_booking.delete_booking_by_id(booking_id, db)
    if booking:
        return {"Success": "Booking Successfully Cancelled "}
    return {"Fail": "Booking Cancellation Failed"}

