from typing import List, Optional
from sqlalchemy import UUID, func, select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from src.models.cars import Car
from src.schemas.car import CarCreationSchema, CarUpdateSchema



async def get_cars(limit: int, offset: int ,db: AsyncSession):
    stmt = select(Car).limit(limit).offset(offset)
    cars = await db.execute(stmt)
    cars = list(cars.scalars().all())
    return cars 



async def get_car(car_id: UUID, db: AsyncSession):
    stmt = select(Car).where(Car.id == car_id)
    car = await db.execute(stmt)
    return car.unique().scalar_one_or_none()



async def create_car(car_data: CarCreationSchema, db: AsyncSession):
    car = Car(**car_data.model_dump())
    db.add(car)
    await db.commit()
    await db.refresh(car)
    return car



async def update_car(car_id: UUID, car_data: CarUpdateSchema, db: AsyncSession):
    
    car = await get_car(car_id=car_id, db=db)

    if not car:
        raise ValueError(f"Car {car_id} not found.")
    car_data = car_data.model_dump(exclude_unset=True).items()
    for key, value in car_data:
        setattr(car, key, value)
    await db.commit()
    await db.refresh(car)

    return car



async def delete_car(car_id: UUID, db: AsyncSession):
    car = await get_car(car_id=car_id, db=db)
    if car:
        await db.delete(car)
        await db.commit()
    return car