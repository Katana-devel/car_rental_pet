import enum
from typing import Optional, Union


from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import ARRAY, Boolean, String, Integer, DateTime, ForeignKey, Enum, func, text


from src.db.base import Base


class CarClass(str, enum.Enum):
    economy = "economy"
    standard = "standard"
    suv = "suv"
    lux = "lux"
    cabriolet = "cabriolet"
    van = "van"


class Car(Base):
    __tablename__ = "cars"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    brand: Mapped[str] = mapped_column(String(100), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    car_class: Mapped[CarClass] = mapped_column(Enum(CarClass), nullable=False)
    price: Mapped[int] = mapped_column(Integer, nullable=False)

    options: Mapped[list["CarOptions"]] = relationship(
        "CarOptions",
        back_populates="car",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean(), default=True, nullable=False, server_default=text("true")
    )
    booking: Mapped[list["Booking"]] = relationship(
        "Booking",
        back_populates="car",
        cascade="all, delete-orphan"
    )


class Options(Base):
    __tablename__ = "options"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    option_name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    price: Mapped[int] = mapped_column(Integer, nullable=False)

    cars: Mapped[list["CarOptions"]] = relationship(
        "CarOptions",
        back_populates="options",
        cascade="all, delete-orphan",
        passive_deletes=True
    )


class CarOptions(Base):
    __tablename__ = "car_options"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )

    car_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cars.id", ondelete="CASCADE"),
        nullable=False
    )
    options_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("options.id", ondelete="CASCADE"),
        nullable=False
    )

    car: Mapped["Car"] = relationship(
        "Car",
        back_populates="options"
    )
    options: Mapped["Options"] = relationship(
        "Options",
        back_populates="cars"
    )

