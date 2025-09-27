import enum
from typing import Optional

from pydantic import EmailStr
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import Boolean, String, Integer, DateTime, ForeignKey, Enum, func, text

from src.db.base import Base



class Role(str, enum.Enum):
    user = "user"
    admin = "admin"



class Gender(str, enum.Enum):
    F = "F"
    M = "M"



class User(Base):
    __tablename__ = "users"
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    password: Mapped[str] = mapped_column(String(100),  nullable=False)
    gender: Mapped[str] = mapped_column("gender", Enum(Gender), nullable=True)
    email: Mapped[Optional[EmailStr]] = mapped_column(String(100), nullable=True, unique=True)
    number: Mapped[Optional[str]] = mapped_column(String(25), nullable=True, unique=True)
    age: Mapped[Optional[int]] = mapped_column(nullable=True) #TODO: Verify with passport
    address: Mapped[str] = mapped_column(String(150), nullable=True)
    role: Mapped[Enum] = mapped_column("role", Enum(Role), nullable=False, default=Role.user)
    refresh_token: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_confirmed:Mapped[bool] = mapped_column(
        Boolean(), default=False, nullable=False, server_default=text("false")
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean(), default=True, nullable=False, server_default=text("true")
    )
    booking: Mapped[list["Booking"]] = relationship(
        "Booking",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    bookings_history: Mapped["BookingHistory"] = relationship(
        "BookingHistory",
        back_populates="user",
    )
    payments: Mapped["Payment"] = relationship(
        "Payment",
        back_populates="user"
    )



    #TODO: Make check if user inputs email -  email column, if number - number column
    #Make proper validation form  for number +380...