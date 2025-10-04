from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone

from fastapi import Depends
from pydantic import EmailStr
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import get_db
from src.models.users import Role, User, Gender
from src.schemas.user import UserCreationSchema, UserProfileSchema
from src.core.config import config
from src.services.auth import auth_service
from src.models.users import User
from src.core.logger.logger import logger




async def get_user_by_email(email: EmailStr, db: AsyncSession = Depends(get_db)):
    stmt = select(User).where(User.email == email)
    user = await db.execute(stmt)
    user = user.unique().scalar_one_or_none()
    return user 



async def create_user(body: UserCreationSchema, db: AsyncSession = Depends(get_db)):
    user = User(**body.model_dump())
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user 


async def update_token(user: User, token: str | None, db: AsyncSession):
    user.refresh_token = token 
    await db.commit()
    return user 



async def get_all_users_from_db(db: AsyncSession) -> List[User]:
    stmt = select(User)
    user = await db.execute(stmt)
    user = list(user.scalars().all)
    return user 



async def delete_user(email, db: AsyncSession) -> List[User]:
    stmt = delete(User).where(User.email == email)
    await db.execute(stmt) 
    return await get_all_users_from_db(db=db)



async def update_user(email: EmailStr, update_data: dict, db: AsyncSession) -> User:
    user = await get_user_by_email(email, db=db)
    try:
        if user:
            for key, value in update_data.items():
                if value is not None:
                    setattr(user, key, value)
        db.add(user)
        await db.commit()
        await db.refresh(user)
    except:
        raise ValueError(f"User with email {email} not found.")
    return user




async def create_admin(db: AsyncSession) -> User:
    admin_user = await get_user_by_email(config.admin_config.ADMIN_EMAIL, db)

    if admin_user:
        logger.info(f"Admin user {config.admin_config.ADMIN_EMAIL} already exists.")
        return admin_user 
    admin_user = User(
        full_name=config.admin_config.ADMIN_FULLNAME,
        email=config.admin_config.ADMIN_EMAIL,
        password=auth_service.get_password_hash(config.admin_config.ADMIN_PASSWORD),
        age=config.admin_config.ADMIN_AGE,
        gender=config.admin_config.ADMIN_GENDER,
        role=Role.admin,
        is_confirmed=True
    )
    db.add(admin_user)
    await db.commit()
    await db.refresh(admin_user)
    return admin_user
    



async def get_user_by_id(user_id: UUID, db: AsyncSession):
    stmt = select(User).where(User.id == user_id)
    user = await db.execute(stmt)
    user = user.unique().scalar_one_or_none()
    return user


async def update_user_profile_data(
        user_data : UserProfileSchema,
        user_id: UUID,
        db: AsyncSession
    ):
    user = await get_user_by_id(user_id, db)

    if user_data.full_name:
        user.full_name = user_data.full_name
    if user_data.gender:
        user.gender = user_data.gender
    if user_data.age:
        user.age = user_data.age
    if user_data.address:
        user.address = user_data.address
    if user_data.number:
        user.number = user_data.number
    if user_data.currency:
        user.currency = user_data.currency

    await db.commit()
    await db.refresh(user)

    return await get_user_by_id(user_id,db)


async def is_number(number: str, db : AsyncSession):
    stmt = select(User).where(User.number == number)
    user = await db.execute(stmt)
    user = user.unique().scalar_one_or_none()
    return user


async def confirmed_email(email: EmailStr, db: AsyncSession) -> None:
    user = await get_user_by_email(email, db)
    user.is_confirmed = True
    await db.commit()

async def password_reset(new_password: str,user_id: UUID, db: AsyncSession):
    user = await get_user_by_id(user_id, db)
    if user:
        user.password = auth_service.get_password_hash(new_password)
        await db.commit()
        await db.refresh(user)
        return user
    return None

# async def ban_user(user: User, db: AsyncSession):
    # ... # through user is_active (do not nessesary now)