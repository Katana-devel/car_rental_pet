from typing import List
from sqlalchemy import UUID, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_

from src.models.cars import Options, CarOptions, Car
from src.schemas.car import OptionsCreationSchema



async def get_options(limit: int, offset: int, db: AsyncSession):
    stmt = select(Options).limit(limit).offset(offset)
    options = await db.execute(stmt)
    return list(options.scalars().all())


async def get_options_by_name(option_name: str | list[str], db: AsyncSession):
    if isinstance(option_name, str):
        option_name = [option_name]

    stmt = select(Options).where(Options.option_name.in_(option_name))
    option = await db.execute(stmt)
    return option.scalars().all()



async def create_option(option_data : OptionsCreationSchema, db: AsyncSession):
    option = await get_options_by_name(option_data.option_name, db)
    if not option:
        option = Options(**option_data.model_dump())
        db.add(option)
        await db.commit()
        await db.refresh(option)
    return option



async def delete_option_by_name(option_name: str, db: AsyncSession):
    stmt = select(Options).where(Options.option_name == option_name)
    res = await db.execute(stmt)
    option = res.scalar_one_or_none()
    if option:
        await db.delete(option)
        await db.commit()
    return option
