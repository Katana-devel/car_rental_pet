import traceback
from email.policy import default
from typing import List, Optional, Annotated
from uuid import UUID
from fastapi import APIRouter, File, Form, HTTPException, Depends, UploadFile, status, Query
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi_limiter.depends import RateLimiter

from src.core.logger.logger import logger
from src.db.database import get_db
from src.db.redis import get_redis
from src.models.users import Role
from src.repository import options as repositories_options
from src.repository import car as repositories_car
from src.schemas.car import OptionsCreationSchema, OptionsResponseSchema
from src.services.auth import auth_service
from src.services.currency.сurrency_decorator import with_currency
from src.services.roles import RoleAccessService


only_admin_access = RoleAccessService([Role.admin])

options_router = APIRouter(prefix='/options', tags=['options'])


@options_router.get("/all_options", response_model=list[OptionsResponseSchema],
                  dependencies=[Depends(RateLimiter(times=10, seconds=20)),Depends(only_admin_access)])
@with_currency(["price", "options.options.price"], all_matches=True)
async def get_options(limit: int = Query(10, ge=1, le=500), offset: int = Query(0, ge=0),
                      db: AsyncSession = Depends(get_db), user_id: UUID = Depends(auth_service.get_current_user),
                      redis: Redis = Depends(get_redis)):
    options = await repositories_options.get_options(limit, offset, db)
    if options is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Any option found")
    return options


@options_router.get(
    "/",
    response_model=list[OptionsResponseSchema],
    dependencies=[Depends(RateLimiter(times=10, seconds=20)), Depends(only_admin_access)],
)
@with_currency(["price", "options.options.price"], all_matches=True)
async def get_options_by_name(
        option_name: str | list[str] = Query(...),
        db: AsyncSession = Depends(get_db),
        user_id: UUID = Depends(auth_service.get_current_user),
        redis: Redis = Depends(get_redis)
):
    if isinstance(option_name, str):
        option_name = option_name.split(",")

    options = await repositories_options.get_options_by_name(option_name, db)
    if not options:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Can't find an option")
    return options


@options_router.post("/", response_model=OptionsResponseSchema,
                  dependencies=[Depends(RateLimiter(times=10, seconds=20)),Depends(only_admin_access)])
async def create_option(option_data: OptionsCreationSchema, db: AsyncSession = Depends(get_db)):

    try:
        option = await repositories_options.create_option(option_data, db)
    except Exception as e:
        logger.error(f"500: Can't create option: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Can't create an option")

    return option



@options_router.delete("/", dependencies=[Depends(RateLimiter(times=10, seconds=20)), Depends(only_admin_access)])
async def delete_option(option_name: str, db: AsyncSession = Depends(get_db)):
    option = await repositories_options.delete_option_by_name(option_name, db)
    if not option:
        raise HTTPException(status_code=404, detail="This option not found")
    return {"detail": "Deleted"}


