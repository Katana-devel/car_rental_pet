from typing import Annotated, Optional, List
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field

from src.models.cars import CarClass


class OptionsCreationSchema(BaseModel):
    option_name: str
    price: int


class OptionsResponseSchema(BaseModel):
    option_name: str
    price: int

    model_config = {"from_attributes": True}


class CarOptionsResponseSchema(BaseModel):
    options: OptionsResponseSchema

    model_config = {"from_attributes": True}


class CarCreationSchema(BaseModel):
    brand: str
    model: Annotated[str, Field(min_length=2, max_length=100)]
    year: Annotated[int, Field(ge=1886, le=datetime.now().year + 1)]
    car_class: CarClass
    price: int


class CarResponseSchema(BaseModel):
    id: UUID
    brand: str
    model: str
    year: int
    car_class: CarClass
    price: int
    options: List[CarOptionsResponseSchema] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class CarUpdateSchema(BaseModel):
    brand: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    car_class: Optional[CarClass] = None
    price: Optional[int] = None

    model_config = {"from_attributes": True}
