from typing import List, Optional
from uuid import UUID, uuid4

from fastapi import Depends
from redis.asyncio import Redis
from redis.commands.json.path import Path

from src.db.redis import get_redis
from src.models.users import Role, User, Gender
from src.core.config import config
from src.models.users import User
from src.core.logger.logger import logger
from src.schemas.cart import CartItem, CartResponseSchema
from src.repository.user import get_user_by_id
from src.services.auth import auth_service


async def get_cart(redis, user_id: UUID = Depends(auth_service.get_current_user)):
    user_id = str(user_id)
    if redis.json().get(f"cart_by_user_id:{user_id}", "$.car_id"):
        return await redis.json().get(f"cart_by_user_id:{user_id}", "$")
    return None



async def add_to_cart(
        redis,
        car_id: UUID,
        options: list[str],
        duration: int,
        total_sum : int,
        user_id: UUID = Depends(auth_service.get_current_user)
):
    cart_creation_json = {
        'car_id': str(car_id),
        'total_price': total_sum,
        'options': options,
        'duration': duration
    }

    await redis.json().set(f"cart_by_user_id:{user_id}", "$", cart_creation_json)

    return await redis.json().get(f"cart_by_user_id:{user_id}", "$")



async def delete_cart(redis, user_id: UUID = Depends(auth_service.get_current_user)):
    user_id = str(user_id)
    delete_cart_ = await redis.json().delete(f"cart_by_user_id:{user_id}", "$")
    if delete_cart_:
        return True
    return False

