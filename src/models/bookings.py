import enum
from datetime import datetime, date
from typing import Optional


from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import Boolean, String, Integer, DateTime, ForeignKey, Enum, func, text, Date

from src.db.base import Base



class BookingStatus(str, enum.Enum):
    confirmed = "confirmed"
    done = "done"
    canceled = "canceled"


class Booking(Base):
    __tablename__ = "bookings"
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    status: Mapped[str] = mapped_column("status", Enum(BookingStatus), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    delivery_address: Mapped[str] = mapped_column(String(150), nullable=True)
    total_price: Mapped[int] = mapped_column(nullable=False)

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
    payment_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("payments.id", ondelete="SET NULL"),
        nullable=True
    )
    user : Mapped["User"] = relationship(
        "User",
        back_populates="booking",
    )
    car : Mapped["Car"] = relationship(
        "Car",
        back_populates="booking",
    )
    payment: Mapped["Payment"] = relationship(
        "Payment",
        back_populates="booking",
        foreign_keys=[payment_id]
    )

class BookingHistory(Base):
    __tablename__ = "bookings_history"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    status: Mapped[str] = mapped_column("status", Enum(BookingStatus), nullable=False)
    booking_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    booking_price: Mapped[int] = mapped_column()
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False
    )

    payment_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("payments.id", ondelete="SET NULL"),
        nullable=False
    )
    car_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cars.id"),
        nullable=False
    )

    user: Mapped["User"] = relationship(
        "User",
        back_populates="bookings_history",
    )
    payment: Mapped["Payment"] = relationship(
        "Payment",
        back_populates="booking_history",
        foreign_keys=[payment_id],
    )
    car: Mapped["Car"] = relationship(
        "Car",
        back_populates="booking_history",
    )
