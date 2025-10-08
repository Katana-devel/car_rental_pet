from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.schemas.promocode import CreatePromoCodeSchema
from src.models.promocodes import PromoCode

async def create_promo_code(p_code_data: CreatePromoCodeSchema, db: AsyncSession):
    p_code = PromoCode(**p_code_data.model_dump())
    db.add(p_code)
    await db.commit()
    await db.refresh(p_code)
    return p_code



async def get_promo_code(p_code_unique: str, db: AsyncSession):
    stmt = select(PromoCode).where(PromoCode.unique_code == p_code_unique)
    p_code = await db.execute(stmt)
    return p_code.unique().scalar_one_or_none()


async def deactivate_promo_code(p_code_unique: str, db: AsyncSession):
    p_code = await get_promo_code(p_code_unique=p_code_unique, db=db)
    p_code.is_active = False
    await db.commit()
    await db.refresh(p_code)
    return p_code
