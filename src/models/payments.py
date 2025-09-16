import enum
from datetime import datetime

from sqlalchemy import text, ForeignKey, Enum, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base


class PaymentStatus(str, enum.Enum):
    pending = "pending"
    success = "success"
    failed = "failed"



class Payment(Base):
    __tablename__ = "payments"
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    status: Mapped[str] = mapped_column("status", Enum(PaymentStatus), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    amount : Mapped[int] = mapped_column(nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    #booking_Unconfirmed - redis. booking can be confirmed and got ID only after payment

    car_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cars.id"),
        nullable=False
    )
    user_id: Mapped[UUID] =  mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False
    )

    booking: Mapped["Booking"] = relationship(
        "Booking",
        back_populates="payment",
        uselist=False,
        foreign_keys="[Booking.payment_id]",
        primaryjoin="Payment.id == Booking.payment_id",
    )

    car: Mapped["Car"] = relationship(
        "Car",
        back_populates = "payments"
    )
    user: Mapped["User"] = relationship(
        "User",
        back_populates="payments"
    )
    booking_history: Mapped["BookingHistory"] = relationship(
        "BookingHistory",
        back_populates="payment"
    )