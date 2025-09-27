from types import new_class
from uuid import UUID

from fastapi import APIRouter, status, HTTPException
from fastapi.params import Depends
from fastapi.security import HTTPBearer
from pydantic import EmailStr
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import get_db
from src.db.redis import get_redis
from src.repository import user as repositories_users
from src.schemas.password_reset import ResetPasswordRequest
from src.services.auth import auth_service
from src.services.messages import password_reset_producer
from src.services.password_strength import validate_password as password_strength
from src.services.password_reset_services import password_reset_access

password_reset_router = APIRouter(prefix='/password_reset', tags=['password_reset'])
get_refresh_token = HTTPBearer()


@password_reset_router.post('/change_password',status_code=status.HTTP_201_CREATED)
async def change_password(
        new_password: str,
        email: EmailStr,
        redis: Redis = Depends(get_redis),
        db: AsyncSession = Depends(get_db)
): #If user logged_in - access
    user = await repositories_users.get_user_by_email(email, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incorrect email")

    access_key = f"password_access:{user.id}"
    if not await redis.get(access_key):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access forbidden. Make password reset request first")

    if not password_strength(new_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password is too weak")

    _password_reset =await repositories_users.password_reset(new_password,user.id, db)
    if _password_reset:
        await redis.delete(access_key)
    else:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Password change failed")
    return {"Success": "Password successfully changed"}


@password_reset_router.post('/request',status_code=status.HTTP_201_CREATED)
async def password_reset_request(
        email: EmailStr,
        db: AsyncSession = Depends(get_db)
):
    user = await repositories_users.get_user_by_email(email, db)

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User is not found")


    await password_reset_producer.reset_password_message(
        user_id=str(user.id),
        email=user.email,
        host="http://localhost:8000"
    )

    return {"message": "Check your email for password resset email"}


@password_reset_router.get('/confirm/{token}', status_code=status.HTTP_200_OK)
async def password_reset_confirmation(
    token: str,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis)
):
    payload = await auth_service.decode_password_reset_token(token)
    subject = payload.get("sub")
    if subject is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token payload")

    try:
        user_uuid = UUID(subject)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token subject")

    user = await repositories_users.get_user_by_id(user_uuid, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error")


    await password_reset_access(subject, redis)
    return {"message": "You can change your password"}

