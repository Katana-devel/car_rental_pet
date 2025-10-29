import asyncio
import ssl
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import aio_pika
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_limiter import FastAPILimiter
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from src.api.auth.auth import auth_router
from src.api.auth.password_reset import password_reset_router
from src.api.promocode.promocode import promo_code_router
from src.core.config.config import rabbitmq_config
from src.db.redis import redis_manager
from src.repository.user import create_admin
from src.db.database import sessionmanager
from src.api.car.car import cars_router
from src.api.cart.cart import cart_router
from src.api.options.options import options_router
from src.api.user.user import user_router
from src.api.booking.booking import booking_router
from src.api.payment.payment import payment_router
from src.api.currency.currency_exchange import currency_router
from src.core.logger.logger import logger
from src.services.booking_services import booking_history
from src.repository.payment import cancel_expired_payments
from src.services.currency.currency_exchange import update_currency_data
from src.services.messages import password_reset_producer, password_reset_consumer
from src.services.messages.message_sub_producer import setup as email_msg_setup
from src.services.messages.message_sub_consumer import setup as cons_email_msg_setup
from src.services.messages.message_sub_consumer import main as cons_email_msg_main
from tests.email_messages_test import test_email
from ssl_context_ignore import ssl_context_ignore


scheduler = AsyncIOScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("App starting up...")

    await redis_manager.connect()
    async with sessionmanager.session() as db:
        await create_admin(db)
    async with redis_manager.session() as redis:
        await FastAPILimiter.init(redis)

    app.state.rabbitmq_conn = await aio_pika.connect_robust(rabbitmq_config.RABBITMQ_URL,
                                                            ssl_context=ssl_context_ignore())
    app.state.rabbitmq_channel = await app.state.rabbitmq_conn.channel()

    await email_msg_setup()
    asyncio.create_task(cons_email_msg_main())
    await password_reset_producer.setup()
    asyncio.create_task(password_reset_consumer.main())


    scheduler.add_job(booking_history, IntervalTrigger(minutes=5))
    scheduler.add_job(cancel_expired_payments, IntervalTrigger(minutes=3))
    scheduler.add_job(update_currency_data, IntervalTrigger(days=1))
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
    "http://localhost",  # allows localhost requests
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
app.include_router(payment_router, prefix="/api")
app.include_router(password_reset_router,prefix="/api")
app.include_router(currency_router,prefix="/api")
app.include_router(promo_code_router,prefix="/api")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
