from fastapi import APIRouter, HTTPException, Depends, Request, status, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm, HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import get_db
from src.repository import user as repositories_users
from src.schemas.user import UserProfileSchema, UserResponseSchema
from src.services.auth import auth_service
from src.services.password_strength import validate_password as password_strength


user_router = APIRouter(prefix='/user', tags=['user'])
get_refresh_token = HTTPBearer()


@user_router.post("/", response_model=UserResponseSchema, status_code=status.HTTP_201_CREATED)
async def add_user_profile_data(
        user_data: UserProfileSchema,
        user_id: UUID = Depends(auth_service.get_current_user),
        db : AsyncSession = Depends(get_db)
):
    user = await repositories_users.get_user_by_id(user_id, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User don't have account")

    if len(user_data.full_name) < 6:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="full name min length is 6 simbols ")
    user_info = await repositories_users.add_user_profile_data(user_data, user_id, db)
    if not user_info:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Can't add user details")


    return user_info