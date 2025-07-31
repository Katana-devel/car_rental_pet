from datetime import datetime, timedelta, timezone
import pickle
from typing import Any, Coroutine, Optional

from fastapi import Depends, HTTPException, status
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt 
from redis.asyncio import Redis

from src.db.database import get_db
from src.db.redis import get_redis
from src.models.users import User
from src.core.config import config
from src.services.password_strength import validate_password

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")


class Auth:
    
    def __init__(self): 
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.SECRET_KEY = config.jwt_config.SECRET_KEY
        self.ALGORITHM = config.jwt_config.ALGORITHM
        self.ACCESS_TOKEN_EXPIRE_MINUTES = config.jwt_config.ACCESS_TOKEN_EXPIRE_MINUTES
        self.REFRESH_TOKEN_EXPIRE_DAYS = config.jwt_config.REFRESH_TOKEN_EXPIRE_DAYS
        self.EMAIL_TOKEN_EXPIRE_DAYS = config.jwt_config.EMAIL_TOKEN_EXPIRE_DAYS


    def verify_password(self, plain_password, hashed_password):
        return self.pwd_context.verify(plain_password, hashed_password)


    def get_password_hash(self, password):
        return self.pwd_context.hash(password)
    
    
    def _create_token(self, data: dict, expires_delta: Optional[timedelta], scope: str):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=15)
        to_encode.update({"exp": expire, "scope": scope})
        encoded_jwt = jwt.encode(to_encode,self.SECRET_KEY, algorithm=self.ALGORITHM)
        return encoded_jwt
    

    def _decode_token(self, token: str, expected_scope: Optional[str] = None) -> dict: 
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            scope = payload.get("scope")
            if scope != expected_scope:
                    raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid scope for token",
                )
            return payload      
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
        )


    async def create_access_token(self, data: dict):
        scope= "access_token"
        return self._create_token(data, expires_delta=timedelta(minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES), scope=scope)


    async def create_refresh_token(self, data: dict):
        scope = "refresh_token"
        return self._create_token(data=data, expires_delta=timedelta(days=self.REFRESH_TOKEN_EXPIRE_DAYS), scope=scope)


    async def create_email_token(self, data: dict):
        scope="email_token"
        return self._create_token(data=data, expires_delta=timedelta(minutes=self.EMAIL_TOKEN_EXPIRE_DAYS), scope=scope)


    async def decode_email_token(self, token: str) -> str: 
        payload = self._decode_token(token=token, expected_scope="email_token")
        return payload
    

    async def decode_refresh_token(self, refresh_token: str) -> str:
        payload =  self._decode_token(token=refresh_token, expected_scope="refresh_token")
        return payload 


    async def authenticate_user(
        self, token: str= Depends(oauth2_scheme) , db: AsyncSession = Depends(get_db), redis: Redis = Depends(get_redis)
    ) -> Coroutine[Any, Any, User]:
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            if payload["scope"] == "access_token":
                email = payload.get("sub")
                if email is None:
                    raise credentials_exception
            else:
                raise credentials_exception
        except JWTError:
            raise credentials_exception
        user = await redis.get(f"user:{email}")
        if user is None:
            from src.repository.user import get_user_by_email
            user = await get_user_by_email(email, db)
            if user is None: 
                raise credentials_exception
            await redis.set(f"user:{email}", pickle.dumps(user))
            await redis.expire(f"user:{email}", 900)
        else:
            user = pickle.loads(user)    

        return user
    


auth_service = Auth()