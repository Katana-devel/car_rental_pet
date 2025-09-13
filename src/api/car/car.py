import traceback
from typing import List, Optional, Annotated
from uuid import UUID
from fastapi import APIRouter, File, Form, HTTPException, Depends, UploadFile, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi_limiter.depends import RateLimiter

from src.core.logger.logger import logger
from src.db.database import get_db
from src.models.users import Role
from src.repository import car as repositories_car
from src.repository import options as repositories_options
from src.schemas.car import CarResponseSchema, CarUpdateSchema, CarCreationSchema
from src.services.availabilities import is_car_booked
from src.services.roles import RoleAccessService


only_admin_access = RoleAccessService([Role.admin])

cars_router = APIRouter(prefix='/cars', tags=['cars'])

@cars_router.get("/", response_model=List[CarResponseSchema],
                  dependencies=[Depends(RateLimiter(times=10, seconds=20)),Depends(only_admin_access)])
async def get_cars(limit: int = Query(10, ge=1, le=500), offset: int = Query(0, ge=0),  db: AsyncSession = Depends(get_db)):
    cars = await repositories_car.get_cars(limit, offset, db)
    unbooked_cars = []
    for car in cars:
        car_id = car.id
        if await is_car_booked(car_id, db):
            continue
        unbooked_cars.append(car)
    return unbooked_cars


@cars_router.get("/{car_id}", response_model=CarResponseSchema, 
                 dependencies=[Depends(RateLimiter(times=10, seconds=20)),Depends(only_admin_access)])
async def get_car(car_id : UUID,db: AsyncSession = Depends(get_db)):

    if await is_car_booked(car_id, db):
        raise HTTPException(status_code=status.HTTP_306_RESERVED, detail="Car is reserved")
    
    car = await repositories_car.get_car(car_id, db)
    if car is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Can't find a car")
    
    return car 


@cars_router.post("/car_options", response_model=CarResponseSchema,
                 dependencies=[Depends(RateLimiter(times=10, seconds=20)),Depends(only_admin_access)])
async def add_options_for_car(
    car_id: UUID,
    option_name: list[str] = Query(...),
    db: AsyncSession = Depends(get_db)
):
    car = await repositories_car.get_car(car_id, db)
    if car is None:
        raise HTTPException(status_code=404, detail="Can't find a car")

    options = await repositories_options.get_options_by_name(option_name, db)
    if not options:
        raise HTTPException(status_code=404, detail="Can't find option(s)")

    option_ids = [opt.id for opt in options]
    try:
        await repositories_car.add_options_for_car(car.id, option_ids, db)
    except Exception as e:
        logger.error(f"Failed to add options to car {car.id}: {e}")
        raise HTTPException(status_code=500, detail="Can't add option to car")

    return await repositories_car.get_car(car_id=car.id, db=db)




@cars_router.post("/", response_model=CarResponseSchema,
                   dependencies=[Depends(RateLimiter(times=10, seconds=20)),Depends(only_admin_access)])
async def create_car(car_data: CarCreationSchema, db: AsyncSession = Depends(get_db)):

    try: 
        car = await repositories_car.create_car(car_data, db)
    except Exception as e:
        logger.error(f"500: Can't create option: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Car creation failed")

    return await repositories_car.get_car(car_id=car.id, db=db) 



@cars_router.patch("/{car_id}", response_model=CarResponseSchema, 
                   dependencies=[Depends(RateLimiter(times=10, seconds=20)),Depends(only_admin_access)])
async def update_car(car_id: UUID, car_data: CarUpdateSchema,  db: AsyncSession = Depends(get_db)):
    
    car = await repositories_car.get_car(car_id, db=db)
    if car is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Can't find a car")
    
    updated_car = await repositories_car.update_car(car_id, car_data, db)
    return updated_car 



@cars_router.delete("/{car_id}",
                     dependencies=[Depends(RateLimiter(times=10, seconds=20)),Depends(only_admin_access)])
async def delete_car(car_id: UUID, db: AsyncSession = Depends(get_db)):
    
    car = await repositories_car.get_car(car_id, db=db)
    if car is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Can't find a car")
    
    await repositories_car.delete_car(car.id, db=db)

    return "Car Successfully Deleted"


@cars_router.delete("/{car_id}/car_options", dependencies=[Depends(RateLimiter(times=10, seconds=20)), Depends(only_admin_access)])
async def delete_option_for_car(option_name: str, car_id: UUID, db: AsyncSession = Depends(get_db)):
    option = await repositories_options.get_options_by_name(option_name, db)
    if option is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="This option not found")

    car = await repositories_car.get_car(car_id, db)
    if car is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="This car not found")
    await repositories_car.delete_option_for_car(car, option[0].id, db)
