from datetime import datetime

from pydantic import BaseModel
from sqlalchemy import UUID

from src.models.promocodes import DiscountType

class CreatePromoCodeSchema(BaseModel):
    discount: DiscountType
    discount: int
    expires_at: datetime
    usage_limit: int


class PromoCodeResponseSchema(BaseModel):
    id: UUID
    unique_code: str
    discount_type: DiscountType
    discount: int
    created_at: datetime
    expires_at: datetime
    times_used: int
    usage_limit: int
    is_active: bool
