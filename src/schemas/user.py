from typing import Annotated, Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr, HttpUrl

from src.models.users import Role, Gender




class UserCreationSchema(BaseModel):
    password: Annotated[str, Field(min_length=6, max_length=25)]
    full_name: Annotated[str, Field(min_length=6, max_length=50)]
    email: Optional[EmailStr] 
    number: Optional[str] 
    age: Optional[int] 
    gender: Gender
    

class UserResponseSchema(BaseModel):
    id: UUID
    full_name: Annotated[str, Field(min_length=6, max_length=50)]
    email: Optional[EmailStr] 
    number: Optional[str]
    age: Optional[int]
    gender : Gender
    role: Role



class TokenSchema(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"



class UserProfileSchema(BaseModel):
    email: EmailStr
    full_name: str
    gender: Gender
    age: Optional[int]


class UpdateUserProfileSchema(BaseModel):
    password: Annotated[str, Field(min_length=6, max_length=25)]
    full_name: Optional[str]
    email: Optional[EmailStr]
    number: Optional[int]
    age: Optional[str] 
    gender: Optional[Gender]