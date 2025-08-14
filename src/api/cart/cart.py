import traceback
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
from src.schemas.cart import CartResponseSchema, CartAddItemSchema
from src.services.auth import auth_service
from src.services.roles import RoleAccessService
from src.core.logger.logger import logger

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
    return CartResponseSchema(cart_data=cart, total_sum=150)



@cart_router.post("/", response_model=CartResponseSchema,
                   dependencies=[Depends(RateLimiter(times=10, seconds=20)), Depends(all_user_access)])
async def add_to_cart(
        car_data: CartAddItemSchema,
        user_id: UUID = Depends(auth_service.get_current_user),
        db: AsyncSession = Depends(get_db),
        redis: Redis = Depends(get_redis)
):
    car_id = await repositories_car.get_car(car_data.car_id, db=db)
    if car_id is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='This car not found')
    try:
        result = await repositories_cart.add_to_cart(redis, car_data, user_id)
    except Exception as e:
        logger.error(f"500: Can't add car to cart: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    return CartResponseSchema(cart_data=result,total_sum=150)



@cart_router.delete("/", dependencies=[Depends(RateLimiter(times=10, seconds=20)), Depends(all_user_access)])
async def remove_car_from_cart(user_id: UUID = Depends(auth_service.get_current_user),
    redis: Redis = Depends(get_redis)):

    if await repositories_cart.get_cart(redis, user_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found")

    try:
        await repositories_cart.remove_car_from_cart(redis, user_id)
    except Exception as e :
        logger.error(f"500:Can't delete the cart: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    return "Cart successfully deleted"
