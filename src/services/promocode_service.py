
import json
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from uuid import UUID

from fastapi import HTTPException, status

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.logger.logger import logger
from src.repository import promocode as repo_promocode
from src.repository import user as repo_user
from src.repository import cart as repo_cart
from src.models.promocodes import DiscountType



async def percentage(discount: int, sum_: int):
    if discount <= 0 or sum_ <= 0:
        return None
    value = Decimal(discount * sum_ / 100)
    return int(value.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


async def get_valid_promo_by_code(unique_code: str, db: AsyncSession):
    p_code = await repo_promocode.get_promo_code(p_code_unique=unique_code, db=db)

    if not p_code:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Promo code is not found")

    if not p_code.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Promo code had been deactivated")

    if p_code.expires_at <= datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Promo code expired")

    if p_code.times_used >= p_code.usage_limit:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This promo code  has reached its limit.")

    return p_code


async def price_with_discount(amount, user_id: UUID, db: AsyncSession, redis: Redis):
    redis_key = f"promo_applied:{user_id}"
    max_allowed_discount = amount * 0.3
    p_code = await redis.get(redis_key)

    if p_code:
        p_code_applied = json.loads(p_code)
        discount = p_code_applied["discount"]
        discount_type = p_code_applied["discount_type"]

        if discount_type == DiscountType.fixed:
            updated_total_price = amount - discount
            if updated_total_price >= max_allowed_discount:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="discount is to large")
            else:
                return updated_total_price

        if discount_type == DiscountType.percent:
            discount = await percentage(discount=discount, sum_=amount)
            if not discount:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="can't calculate discount")
            updated_total_price = amount - discount
            if updated_total_price <= max_allowed_discount:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="discount is to big")
            else:
                return updated_total_price

    return None



async def apply_promo_to_cart(user_id: UUID, unique_code: str, db:AsyncSession, redis: Redis):
    p_code = await get_valid_promo_by_code(unique_code=unique_code, db=db)
    if not p_code:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Promo code is not valid")

    user = await repo_user.get_user_by_id(user_id=user_id, db=db)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User is not found")

    redis_key = f"promo_applied:{user_id}"
    redis_value = json.dumps({
        "code": p_code.unique_code,
        "discount": p_code.discount,
        "discount_type": p_code.discount_type,
    })

    redis_promo = await redis.set(redis_key, redis_value, nx=True)
    if not redis_promo:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to store promo in Redis")

    return


async def finalize_promo_usage(user_id: UUID, redis, db: AsyncSession):
    redis_key = f"promo_applied:{user_id}"
    unique_code = await redis.get(redis_key)

    if not unique_code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Promo is not applied")
    unique_code = json.loads(unique_code)

    p_code = await repo_promocode.get_promo_code(p_code_unique=unique_code["code"], db=db)
    if not p_code:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Promo code not found")

    p_code.times_used += 1
    if p_code.times_used >= p_code.usage_limit:
        p_code.active = False

    await db.commit()
    await db.refresh(p_code)

    exists = await redis.exists(redis_key)
    logger.info(f"Exists before delete: {exists}")
    deleted = await redis.delete(redis_key)
    logger.info(f"Deleted: {deleted}")

