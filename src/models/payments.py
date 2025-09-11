import enum
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base


class Payment(Base):
    __tablename__ = "payments"
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )

    booking: Mapped["Booking"] = relationship(
        "Booking",
        back_populates="payment",
        uselist=False # one book one payment
    )