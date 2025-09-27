import json
from uuid import UUID

from fastapi import HTTPException, status
from redis.asyncio import Redis


async def password_reset_access(user_id: UUID, redis: Redis,) -> dict:
    access_key = f"password_access:{user_id}"
    access_value = json.dumps({"access": True})

    access = await redis.set(access_key, access_value, ex=15*60, nx=True)

    if not access:
        current_access = await redis.get(access_key)
        if current_access:
            return json.loads(current_access)

    return {"access": True}