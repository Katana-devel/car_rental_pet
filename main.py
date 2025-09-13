#!/bin/env python3

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_limiter import FastAPILimiter
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from src.api.auth.auth import auth_router
from src.db.redis import redis_manager
from src.repository.user import create_admin
from src.db.database import sessionmanager
from src.api.car.car import cars_router
from src.api.cart.cart import cart_router
from src.api.options.options import options_router
from src.api.user.user import user_router
from src.api.booking.booking import booking_router
from src.core.logger.logger import logger
from src.services.booking_services import booking_history


scheduler = AsyncIOScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("App starting up...")

    await redis_manager.connect()
    async with sessionmanager.session() as db:
        await create_admin(db)
    async with redis_manager.session() as redis:
        await FastAPILimiter.init(redis)

    scheduler.add_job(booking_history, IntervalTrigger(minutes=5))
    scheduler.start()
    logger.info("Scheduler started...")

    yield
    logger.info("App shutting down...")
    await redis_manager.close()
    await FastAPILimiter.close()

app = FastAPI(
    debug=True,
    lifespan=lifespan,
    title="petproject1 API",
    version="1.0",
    description="FastAPI backend application",
)

origins = [
    "http://localhost",  # Дозволяє запити з localhost
    "http://localhost:3000",  # frontend
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth_router, prefix="/api")
app.include_router(cars_router, prefix="/api")
app.include_router(cart_router, prefix="/api")
app.include_router(options_router, prefix="/api")
app.include_router(user_router, prefix="/api")
app.include_router(booking_router, prefix="/api")

