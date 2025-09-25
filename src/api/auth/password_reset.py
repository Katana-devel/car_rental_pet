from types import new_class
from uuid import UUID

from fastapi import APIRouter, status, HTTPException
from fastapi.params import Depends
from fastapi.security import HTTPBearer
from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import get_db
from src.repository import user as repositories_users
from src.services.auth import auth_service
from src.services.messages import password_reset_producer
from src.services.password_strength import validate_password as password_strength

password_reset_router = APIRouter(prefix='/password_reset', tags=['password_reset'])
get_refresh_token = HTTPBearer()



@password_reset_router.post('/request',status_code=status.HTTP_201_CREATED)
async def unlogged_in_password_reset_request(
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



@password_reset_router.post('/request/logged_in',status_code=status.HTTP_201_CREATED)
async def logged_in_password_reset_request(
        user_id: UUID = Depends(auth_service.get_current_user),
        db: AsyncSession = Depends(get_db)
):
    user = await repositories_users.get_user_by_id(user_id, db)

    if not user or not user.is_confirmed:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User unauthorized")

    await password_reset_producer.reset_password_message(
        user_id=str(user.id),
        email=user.email,
        host="http://localhost:8000"
    )

    return {"message": "Check your email for password resset email"}


@password_reset_router.post('/confirm/{token}', status_code=status.HTTP_200_OK)
async def password_reset_confirmation(
    token: str,
    new_password: str,
    db: AsyncSession = Depends(get_db)
):
    payload = await auth_service.decode_password_reset_token(token)
    subject = payload.get("sub")
    if subject is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token payload")

    from uuid import UUID as UUID_cls
    try:
        user_uuid = UUID_cls(subject)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token subject")

    user = await repositories_users.get_user_by_id(user_uuid, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error")

    if not password_strength(new_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password is too weak")

    await repositories_users.password_reset(new_password, user_uuid, db)
    return {"message": "Password has been reset"}


