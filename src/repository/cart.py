from datetime import datetime, date
from typing import List, Optional
from uuid import UUID, uuid4

from fastapi import Depends
from src.services.auth import auth_service


async def get_cart(redis, user_id: UUID = Depends(auth_service.get_current_user)):
    user_id = str(user_id)
    if await redis.json().get(f"cart_by_user_id:{user_id}", "$.car_id"):
        return await redis.json().get(f"cart_by_user_id:{user_id}", "$")
    return None



async def add_to_cart(
        redis,
        car_id: UUID,
        options: list[str],
        start_time: date,
        end_time: date,
        total_sum : int,
        user_id: UUID = Depends(auth_service.get_current_user)
):
    cart_creation_json = {
        'car_id': str(car_id),
        'total_price': total_sum,
        'options': options,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat()
    }

    await redis.json().set(f"cart_by_user_id:{user_id}", "$", cart_creation_json)

    return await redis.json().get(f"cart_by_user_id:{user_id}", "$")



async def delete_cart(redis, user_id: UUID = Depends(auth_service.get_current_user)):
    user_id = str(user_id)
    delete_cart_ = await redis.json().delete(f"cart_by_user_id:{user_id}", "$")
    if delete_cart_:
        return True
    return False

