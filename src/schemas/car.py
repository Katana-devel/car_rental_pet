from typing import Annotated, Optional, List
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field

from src.models.cars import CarClass


#TODO: Only for admins 
class CarCreationSchema(BaseModel):
    brand: str
    model: Annotated[str, Field(min_length=2, max_length=100)]
    year: int
    car_class: CarClass
    price: int
    options: Optional[List[str]]


class CarResponseSchema(BaseModel):
    id: UUID
    brand: str
    model: str
    year: int
    car_class: CarClass
    price: int 
    options: Optional[List[str]]


class CarUpdateSchema(BaseModel):
    brand: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    car_class: Optional[CarClass] = None
    price: Optional[int] = None
    options: Optional[List[str]] = None



#TODO: create other el (Booking etc)interrelation with User 