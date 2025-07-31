from typing import List, Optional, Annotated
from uuid import UUID
from fastapi import APIRouter, File, Form, HTTPException, Depends, UploadFile, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi_limiter.depends import RateLimiter

from src.db.database import get_db
from src.models.users import User
from src.models.users import Role
from src.repository import car as repositories_car
from src.schemas.car import CarResponseSchema, CarUpdateSchema, CarCreationSchema
from src.services.roles import RoleAccessService
from src.services.auth import auth_service  


only_admin_access = RoleAccessService(Role.admin)

cars_router = APIRouter(prefix='/cars', tags=['cars'])

@cars_router.get("/", response_model=List[CarResponseSchema],
                  dependencies=[Depends(RateLimiter(times=10, seconds=20)),Depends(only_admin_access)])
async def get_cars(limit: int = Query(10, ge=1, le=500), offset: int = Query(0, ge=0),  db: AsyncSession = Depends(get_db)):
    
    cars = await repositories_car.get_cars(limit, offset, db)
    if cars is None: 
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Any car found")
    return cars


@cars_router.get("/{car_id}", response_model=CarResponseSchema, 
                 dependencies=[Depends(RateLimiter(times=10, seconds=20)),Depends(only_admin_access)])
async def get_car(car_id : UUID,db: AsyncSession = Depends(get_db)):
    
    car = await repositories_car.get_car(car_id, db)
    
    if car is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Can't find a car")
    
    return car 


@cars_router.post("/", response_model=CarResponseSchema,
                   dependencies=[Depends(RateLimiter(times=10, seconds=20)),Depends(only_admin_access)])
async def create_car(car_data: CarCreationSchema, db: AsyncSession = Depends(get_db)):

    try: 
        car = await repositories_car.create_car(car_data, db)
    except Exception as e: 
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

    
    

@cars_router.delete("/{car_id}", response_model=CarResponseSchema,
                     dependencies=[Depends(RateLimiter(times=10, seconds=20)),Depends(only_admin_access)])
async def delete_car(car_id: UUID, db: AsyncSession = Depends(get_db)):
    
    car = await repositories_car.get_car(car_id, db=db)
    if car is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Can't find a car")
    
    await repositories_car.delete_car(car_id, db=db)

    return car 
