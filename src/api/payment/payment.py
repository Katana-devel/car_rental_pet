
from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends, status, Query
from redis import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi_limiter.depends import RateLimiter

from src.core.logger.logger import logger
from src.db.database import get_db
from src.db.redis import get_redis
from src.models.users import Role

from src.services.auth import auth_service
from src.services.currency.сurrency_decorator import with_currency
from src.services.roles import RoleAccessService
from src.repository import payment as repo_payment
from src.api.booking import booking as api_booking
from src.services import promocode_service




only_admin_access = RoleAccessService([Role.admin])

payment_router = APIRouter(prefix='/payment', tags=['payment'])



@payment_router.get("/{payment_id}",
                  dependencies=[Depends(RateLimiter(times=10, seconds=20))])
@with_currency(["price", "options.options.price", "total_price", "amount"], all_matches=True)
async def get_payment_by_id(payment_id: UUID, db: AsyncSession = Depends(get_db), redis: Redis = Depends(get_redis),
                          user_id: UUID = Depends(auth_service.get_current_user)):
    payment = await repo_payment.get_payment_by_id(payment_id=payment_id, db=db)
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="payment is not found")

    return payment

@payment_router.post("/{payment_id}",
                  dependencies=[Depends(RateLimiter(times=10, seconds=20))])
@with_currency(["price", "options.options.price", "total_price", "amount"], all_matches=True)
async def pay_for_payment(payment_id: UUID,
                          db: AsyncSession = Depends(get_db),
                          redis: Redis = Depends(get_redis),
                          user_id: UUID = Depends(auth_service.get_current_user)
):
    payment= await repo_payment.get_payment_by_id(payment_id, db)
    if not payment:
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="There is no payment")

    discount = await promocode_service.price_with_discount(amount=payment.amount,user_id=user_id, db=db, redis=redis)
    if discount:
        payment.amount = discount

    payment = await repo_payment.pay_for_payment(payment_id=payment_id, db=db)
    if not payment:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Payment failed")

    await api_booking.create_booking(total_price=payment.amount, user_id=payment.user_id, db=db, redis=redis)

    try:
        await promocode_service.finalize_promo_usage(user_id=user_id, redis=redis, db=db)
    except Exception as e:
        logger.error(f"Failed to finalize promo usage for user {user_id}: {e}")

    return payment