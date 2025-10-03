from datetime import datetime, timedelta, timezone

from sqlalchemy import UUID, func, select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from src.db.database import sessionmanager
from src.models import Payment
from src.models.payments import PaymentStatus
from src.repository import booking as repo_booking



async def get_payment_by_id(payment_id: UUID, db :AsyncSession):
    stmt = select(Payment).where(Payment.id == payment_id)
    payment = await db.execute(stmt)
    payment = payment.scalar_one_or_none()
    return payment


async def create_payment(
        user_id: UUID,
        car_id: UUID,
        amount: int,
        db: AsyncSession,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=15)
):
    payment = Payment(user_id=user_id, car_id=car_id, amount=amount, status=PaymentStatus.pending, expires_at=expires_at)
    db.add(payment)
    await db.commit()
    await db.refresh(payment)
    return payment


async def pay_for_payment(payment_id: UUID, db :AsyncSession):
    stmt = (
        update(Payment)
        .where(Payment.id == payment_id)
        .values(status=PaymentStatus.success)
        .returning(Payment)
    )
    result = await db.execute(stmt)
    await db.commit()
    return result.scalar_one_or_none()



async def cancel_expired_payments():
    async with sessionmanager.session() as db:
        stmt_update = (
            update(Payment)
            .where(
                Payment.expires_at < datetime.now(timezone.utc),
                Payment.status == PaymentStatus.pending
            )
            .values(status=PaymentStatus.failed)
            .returning(Payment)
        )

        result = await db.execute(stmt_update)
        await db.commit()
        return result.scalars().all()