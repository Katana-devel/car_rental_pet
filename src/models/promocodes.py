import enum
from datetime import datetime
import random
import string

from sqlalchemy import text, Enum, DateTime, func, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base


def generate_code(length: int = 8) -> str:
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choices(chars, k=length))



class DiscountType(str, enum.Enum):
    percent = "percent"
    fixed = "fixed"


class PromoCode(Base):
    __tablename__ = "promo_codes"
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    unique_code: Mapped[str] = mapped_column(
        unique=True,
        nullable=False,
        index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    discount: Mapped[int] = mapped_column(nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    discount_type: Mapped[str] = mapped_column("discount_type", Enum(DiscountType), nullable=False)
    usage_limit: Mapped[int] = mapped_column(nullable=False)
    times_used: Mapped[int] = mapped_column(nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(
        Boolean(), default=True, nullable=False, server_default=text("true")
    )
    def __init__(self, **kwargs):
        if "unique_code" not in kwargs:
            kwargs["unique_code"] = generate_code(random.randint(6, 8))
        super().__init__(**kwargs)