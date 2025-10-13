from typing import List
from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends, status, Query
from redis import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi_limiter.depends import RateLimiter

from src.db.database import get_db
from src.db.redis import get_redis
from src.models.users import Role
from src.schemas.promocode import CreatePromoCodeSchema, PromoCodeResponseSchema
from src.services.auth import auth_service
from src.services.roles import RoleAccessService
from src.repository import promocode as repo_promocode

only_admin_access = RoleAccessService([Role.admin])

promo_code_router = APIRouter(prefix='/promo_code', tags=['promo_code'])


@promo_code_router.get("/get_promo_codes",dependencies=[Depends(RateLimiter(times=10, seconds=20)),
                                Depends(only_admin_access)], response_model=List[PromoCodeResponseSchema])
async def get_promo_codes(db: AsyncSession = Depends(get_db)):
    p_code = await repo_promocode.get_promo_codes(db=db)
    if not p_code:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Can't find any promo code")
    return p_code


@promo_code_router.post("/create_promo_code",dependencies=[Depends(RateLimiter(times=10, seconds=20)),
                                Depends(only_admin_access)], response_model=PromoCodeResponseSchema)
async def create_promo_code(p_code_data: CreatePromoCodeSchema, db: AsyncSession = Depends(get_db), redis: Redis = Depends(get_redis),
                          user_id: UUID = Depends(auth_service.get_current_user)):
    create_p_code = await repo_promocode.create_promo_code(p_code_data=p_code_data, db=db)
    if not create_p_code:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Can't create the promo code")

    return await repo_promocode.get_promo_code(p_code_unique=create_p_code.unique_code, db=db)


@promo_code_router.post("/deactivate_promo_code",dependencies=[Depends(RateLimiter(times=10, seconds=20)),
                                Depends(only_admin_access)], response_model=PromoCodeResponseSchema)
async def deactivate_promo_code(p_code_unique: str, db: AsyncSession = Depends(get_db), redis: Redis = Depends(get_redis),
                          user_id: UUID = Depends(auth_service.get_current_user)):
    p_code = await repo_promocode.get_promo_code(p_code_unique=p_code_unique, db=db)
    if not p_code:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="The promo code not found")

    deactivate_p_code = await repo_promocode.deactivate_promo_code(p_code_unique=p_code_unique, db=db)
    if not deactivate_p_code:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Can't deactivate the promo code")

    return deactivate_p_code