import uuid
from typing import List, Optional

from sqlalchemy import UUID, func, select, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from src.models.cars import Car, CarOptions, Options
from src.schemas.car import CarCreationSchema, CarUpdateSchema
from src.repository import options as repo_options



async def get_cars(limit: int, offset: int ,db: AsyncSession):
    stmt = (
        select(Car)
        .options(
            selectinload(Car.options).selectinload(CarOptions.options)  #
        )
        .limit(limit)
        .offset(offset)
    )
    cars = await db.execute(stmt)
    cars = list(cars.scalars().all())
    return cars 



async def get_car(car_id: UUID, db: AsyncSession):
    stmt = (
        select(Car)
        .options(
            selectinload(Car.options).selectinload(CarOptions.options)
        )
        .where(Car.id == car_id)
    )
    car = await db.execute(stmt)
    return car.unique().scalar_one_or_none()



async def add_options_for_car(car_id: UUID, option_ids: str | list[str], db: AsyncSession):
    if isinstance(option_ids, (str, UUID)):
        option = CarOptions(car_id=car_id, options_id=option_ids)
        db.add(option)
    else:
        options = [CarOptions(car_id=car_id, options_id=opt) for opt in option_ids]
        db.add_all(options)
    await db.commit()
    return await get_car(car_id, db)


async def create_car(car_data: CarCreationSchema, db: AsyncSession):
    car = Car(**car_data.model_dump())
    db.add(car)
    await db.commit()
    await db.refresh(car)
    return car


async def update_car(car_id: uuid.UUID, car_data: CarUpdateSchema, db: AsyncSession):
    car = await get_car(car_id=car_id, db=db)
    if not car:
        raise ValueError(f"Car {car_id} not found.")

    data = car_data.model_dump(exclude_unset=True)
    options_in = data.pop("options", None)

    for key, value in data.items():
        setattr(car, key, value)

    if options_in is not None:
        if isinstance(options_in, (str, uuid.UUID)):
            options_in = [options_in]
        await db.execute(delete(CarOptions).where(CarOptions.car_id == car.id))

        associations = []
        for opt in options_in:

            if isinstance(opt, str):
                try:
                    opt_id = uuid.UUID(opt)
                except ValueError:
                    raise ValueError(f"Invalid UUID string for option: {opt}")
            elif isinstance(opt, uuid.UUID):
                opt_id = opt
            else:
                raise ValueError(f"Unsupported option id type: {type(opt)}")

            associations.append(CarOptions(car_id=car.id, options_id=opt_id))

        if associations:
            db.add_all(associations)

    await db.commit()
    await db.refresh(car)
    return await get_car(car_id=car.id, db=db)



async def delete_car(car_id: uuid.UUID, db: AsyncSession):
    car = await db.get(Car, car_id)
    if car is None:
        return None
    await db.delete(car)
    await db.commit()
    return car


async def delete_option_for_car(car: Car, option_id: UUID, db: AsyncSession):
    stmt = select(CarOptions).where(and_(CarOptions.options_id == option_id, CarOptions.car_id == car.id))
    print("----------------------------------1----------------------")
    option = await db.execute(stmt)
    print("----------------------------------2----------------------")
    option = option.scalar_one_or_none()
    print("----------------------------------3----------------------")

    if option:
        await db.delete(option)
        await db.commit()

#'list' object has no attribute 'id'