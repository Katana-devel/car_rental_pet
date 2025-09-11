from typing import Annotated, Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr, HttpUrl

from src.models.users import Role, Gender



class UserCreationSchema(BaseModel):
    full_name: Annotated[str, Field(min_length=6, max_length=50)]
    email: EmailStr
    password: Annotated[str, Field(min_length=6, max_length=25)]
    

class UserResponseSchema(BaseModel):
    id: UUID
    full_name: Annotated[str, Field(min_length=6, max_length=50)]
    email: Optional[EmailStr] = None
    number: Optional[str] = None
    age: Optional[int] = None
    address: Optional[str] = None
    gender : Optional[Gender] = None
    role: Role



class TokenSchema(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"



class UserProfileSchema(BaseModel):
    email: EmailStr
    full_name: str
    number : str
    gender: Optional[Gender] = None
    age: Optional[int] = None
    address: Optional[str] = None



class UpdateUserProfileSchema(BaseModel):
    password: Optional[Annotated[str, Field(min_length=6, max_length=25)]]
    full_name: Optional[Annotated[str, Field(min_length=6, max_length=50)]]
    email: Optional[EmailStr] = None
    number: Optional[int] = None
    age: Optional[int] = None
    address: Optional[str] = None
    gender: Optional[Gender] = None
