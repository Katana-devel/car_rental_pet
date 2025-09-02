
from typing import Any

from sqlalchemy import UUID, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.cars import Car, CarOptions
from src.repository import options as repo_options
from src.repository import car as repo_car
from src.schemas.car import OptionsResponseSchema
from src.schemas.cart import CartItem



async def selected_options(car_data: CartItem , db: AsyncSession):
    car = await repo_car.get_car(car_data.car_id, db)
    car_opt = car.options
    user_opt = car_data.options
    options = []
    for opt in car_opt:
        if opt.options.option_name in user_opt:
            options.append({
                "option_name": opt.options.option_name,
                "price": opt.options.price
            })
            return options
        else:
            return []
    return None



async def total_sum(car_id, options: list[OptionsResponseSchema] ,duration : int,  db: AsyncSession):
    car = await repo_car.get_car(car_id, db)
    options_sum = sum(option["price"] for option in options) if car.options else 0
    return (car.price * duration) + (options_sum * duration)

