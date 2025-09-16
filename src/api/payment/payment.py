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
from src.repository import payment as repo_payment
from src.repository import booking as repo_booking
from src.api.booking import booking as api_booking




only_admin_access = RoleAccessService([Role.admin])

payment_router = APIRouter(prefix='/payment', tags=['payment'])



@payment_router.get("/{payment_id}",
                  dependencies=[Depends(RateLimiter(times=10, seconds=20))])
async def get_payment_by_id(payment_id: UUID, db: AsyncSession = Depends(get_db)):
    payment = await repo_payment.get_payment_by_id(payment_id, db)
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="payment is not found")

    return payment

@payment_router.post("/{payment_id}",
                  dependencies=[Depends(RateLimiter(times=10, seconds=20))])
async def pay_for_payment(payment_id: UUID, db: AsyncSession = Depends(get_db), redis: Redis = Depends(get_redis)):
    is_payment_exist = await repo_payment.get_payment_by_id(payment_id, db)
    if not is_payment_exist:
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="There is no payment")

    payment = await repo_payment.pay_for_payment(payment_id, db)
    if not payment:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Payment failed")

    await api_booking.create_booking(user_id=payment.user_id, db=db, redis=redis)

    return payment