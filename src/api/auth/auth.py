from fastapi import APIRouter, HTTPException, Depends, Request, status, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm, HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import get_db
from src.repository import user as repositories_users
from src.schemas.user import UserCreationSchema, TokenSchema, UserResponseSchema
from src.services.auth import auth_service
from src.services.password_strength import validate_password as password_strength


auth_router = APIRouter(prefix='/auth', tags=['auth'])
get_refresh_token = HTTPBearer()


@auth_router.post("/signup", response_model=UserResponseSchema, status_code=status.HTTP_201_CREATED)
async def signup(body: UserCreationSchema, request: Request, db: AsyncSession = Depends(get_db)):
    exist_user = await repositories_users.get_user_by_email(body.email, db=db)
    if exist_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Account already exists")
    
    if not password_strength(body.password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password is too easy")

    body.password = auth_service.get_password_hash(body.password)
    new_user = await repositories_users.create_user(body=body, db=db)
    return new_user 


@auth_router.post("/login",  response_model=TokenSchema)
async def login(body: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    user = await repositories_users.get_user_by_email(email=body.username, db=db)
    if user is None: 
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect password or email")
    verify_password = auth_service.verify_password(body.password, user.password)
    if not verify_password:
       raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect password or email")
    access_token = await auth_service.create_access_token(data={"sub":body.username})
    refresh_token = await auth_service.create_refresh_token(data={"sub":body.username})
    await repositories_users.update_token(user, refresh_token, db)
    return {"access_token" : access_token, "refresh_token": refresh_token,  "token_type": "bearer"}


@auth_router.get('/refresh_token',  response_model=TokenSchema)
async def refresh_token(credentials: HTTPAuthorizationCredentials = Depends(get_refresh_token),
                        db: AsyncSession = Depends(get_db)):
    token = credentials.credentials
    payload = auth_service._decode_token(token, expected_scope="refresh_token")
    email = payload["sub"]
    user = await repositories_users.get_user_by_email(email, db=db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect user")

    access_token = await auth_service.create_access_token(data={"sub":email})
    refresh_token = await auth_service.create_refresh_token(data={"sub":email})
    await repositories_users.update_token(user, refresh_token, db)
    return {"access_token" : access_token, "refresh_token": refresh_token,  "token_type": "bearer"}