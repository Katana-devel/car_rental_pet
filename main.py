#!/bin/env python3

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_limiter import FastAPILimiter

from src.api.auth.auth import auth_router
from src.db.redis import redis_manager
from src.repository.user import create_admin
from src.db.database import sessionmanager
from src.api.car.car import cars_router
from src.api.car.cart import cart_router
from src.api.options.options import options_router
from src.core.logger.logger import logger



@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("App starting up...")

    await redis_manager.connect()
    async with sessionmanager.session() as db:
        await create_admin(db)
    # Отримуємо сесію Redis для FastAPILimiter
    async with redis_manager.session() as redis:
        await FastAPILimiter.init(redis)

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

