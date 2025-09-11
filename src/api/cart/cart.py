import traceback
from datetime import date
from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi_limiter.depends import RateLimiter

from src.db.database import get_db
from src.db.redis import get_redis
from src.models.users import Role
from src.repository import cart as repositories_cart
from src.repository import car as repositories_car
from src.schemas.cart import CartResponseSchema, CartItem
from src.services.auth import auth_service
from src.services.cart_services import total_sum, selected_options
from src.services.roles import RoleAccessService
from src.core.logger.logger import logger
from src.services import cart_services

all_user_access = RoleAccessService([Role.admin, Role.user])

cart_router = APIRouter(prefix='/cart', tags=['cart'])


@cart_router.get("/", response_model=CartResponseSchema,
                   dependencies=[Depends(RateLimiter(times=10, seconds=20)), Depends(all_user_access)],)
async def get_cart(user_id: UUID = Depends(auth_service.get_current_user),
    redis: Redis = Depends(get_redis)
):
    cart = await repositories_cart.get_cart(redis, user_id)
    if cart is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User has no cart")

    return CartResponseSchema(
        car_id=cart[0]["car_id"],
        options=cart[0]["options"],
        total_price =cart[0]["total_price"],
        start_time=date.fromisoformat(cart[0]["start_time"]),
        end_time =date.fromisoformat(cart[0]["end_time"])
    )



@cart_router.post("/", response_model=CartResponseSchema,
                   dependencies=[Depends(RateLimiter(times=10, seconds=20)), Depends(all_user_access)])
async def add_to_cart(
        car_data: CartItem,
        user_id: UUID = Depends(auth_service.get_current_user),
        db: AsyncSession = Depends(get_db),
        redis: Redis = Depends(get_redis)
):
    car = await repositories_car.get_car(car_data.car_id, db=db)
    if car is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='This car not found')

    options = await selected_options(car_data, db=db)
    if options is None:
        options = []

    if car_data.start_time < date.today() or car_data.end_time < date.today():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid date")

    total_sum_ = await cart_services.total_sum(
        car_id=car.id,
        options=options,
        start_time=car_data.start_time,
        end_time=car_data.end_time,
        db=db
    )

    try:
        result = await repositories_cart.add_to_cart(redis, car.id, options, car_data.start_time, car_data.end_time, total_sum_, user_id)
    except Exception as e:
        logger.error(f"500: Can't add car to cart: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    return CartResponseSchema(
        car_id=car.id,
        options=result[0]["options"],
        total_price = total_sum_,
        start_time=result[0]["start_time"],
        end_time=result[0]["end_time"]
    )



@cart_router.delete("/", dependencies=[Depends(RateLimiter(times=10, seconds=20)), Depends(all_user_access)])
async def delete_cart(user_id: UUID = Depends(auth_service.get_current_user),
    redis: Redis = Depends(get_redis)):

    if await repositories_cart.get_cart(redis, user_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found")

    try:
        await repositories_cart.delete_cart(redis, user_id)
    except Exception as e :
        logger.error(f"500:Can't delete the cart: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    return "Cart successfully deleted"


