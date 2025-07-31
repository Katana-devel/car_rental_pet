import enum
from typing import Optional, Union


from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import ARRAY, Boolean, String, Integer, DateTime, ForeignKey, Enum, func, text


from src.db.base import Base



class CarClass(str, enum.Enum):
    economy = "economy"
    standart = "standart"
    suv = "suv"
    lux = "lux"
    cabriolet = "cabriolet"
    Van = "van"


# class Options(str, enum.Enum):
#     no_deposit = "no_deposit"
#     full_insurance = "full_insurance"
#     no_credit_card = "no_credit_card"
#     new_cars = "new_cars"
#     free_cancelation = "free_cancelation"
#     city_delivery = "city_delivery"
#     low_deposit = "low_deposit"
#     real_photos = "real_photos"
#     baby_seat = "baby_seat"




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
    options: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean(), default=True, nullable=False, server_default=text("true")
    )
    

#TODO: Car interrelation with options I should do many-to-many approach (Car -> Options) = (CarOptions (subtable))