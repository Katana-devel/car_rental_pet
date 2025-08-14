from typing import Annotated, Optional, List
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field



class CartData(BaseModel):
    options: Optional[List[str]] = []
    duration: int

class CartAddItemSchema(BaseModel):
    car_id: UUID
    cart_data: CartData


class CartResponseSchema(BaseModel):
    cart_data: list
    total_sum: int
