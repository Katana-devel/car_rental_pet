import json

from fastapi import Depends, HTTPException, status
from redis import Redis
from sqlalchemy import UUID
from sqlalchemy.ext.asyncio import AsyncSession

#TODO Booking history, status Done

async def unconfirmed_booking_exp(redis, user_id: UUID, car_id: UUID):

    lock_key = f"car_locked:{car_id}"
    lock_value = json.dumps({"user_id": str(user_id), "car_id": str(car_id)})

    redis_lock = await redis.set(lock_key, lock_value, ex=15*60, nx=True)
    if not redis_lock:
        raise HTTPException(status_code=status.HTTP_306_RESERVED, detail="Car locked")

    return json.loads(lock_value)




async def booking_history():
    ...