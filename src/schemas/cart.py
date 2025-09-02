from typing import Annotated, Optional, List
from uuid import UUID

from pydantic import BaseModel, Field

from src.schemas.car import OptionsCreationSchema, OptionsResponseSchema


class CartItem(BaseModel):
    car_id: UUID
    options: Optional[List[str]] = None
    duration: int


class CartResponseSchema(BaseModel):
    car_id: UUID
    options: List[OptionsResponseSchema]
    total_price: int
    duration : int
