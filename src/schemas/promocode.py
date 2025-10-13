from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, field_validator, computed_field
from src.models.promocodes import DiscountType



class CreatePromoCodeSchema(BaseModel):
    unique_code: Optional[str]
    discount_type: DiscountType
    discount: int
    expires_at: datetime
    usage_limit: int

    @field_validator("expires_at", mode="before")
    def parse_human_datetime(cls, value):
        if isinstance(value, datetime):
            return value

        for fmt in ("%Y-%m-%d %H:%M", "%d.%m.%Y %H:%M", "%Y-%m-%d"):
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
        raise ValueError(
            "Invalid datetime format. Use 'YYYY-MM-DD HH:MM' or 'DD.MM.YYYY HH:MM'"
        )

    class Config:
        orm_mode = True

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

    @computed_field
    def expires_at_human(self) -> str:
        return self.expires_at.strftime("%d.%m.%Y %H:%M")

    @computed_field
    def created_at_human(self) -> str:
        return self.created_at.strftime("%d.%m.%Y %H:%M")

    class Config:
        orm_mode = True