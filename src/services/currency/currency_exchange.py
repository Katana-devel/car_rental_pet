
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from fastapi import HTTPException, status

from fastapi.params import Depends
from redis.asyncio import Redis
import httpx

from src.core.logger.logger import logger
from src.db.redis import get_redis, redis_manager

API_URL = f"https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@{date.today().isoformat()}/v1/currencies/usd.json"


async def update_currency_data():
    async with redis_manager.session() as redis:
        async with httpx.AsyncClient() as client:
            response = await client.get(API_URL)
            response.raise_for_status()
            data = response.json()
        rates = data.get("usd", {})
        if not rates:
            logger.warning("No rates received from API")
            return
        await redis.hset("exchange:usd", mapping=rates)
        logger.info("Currency data updated")



async def convert(price_usd: float, currency: str, redis: Redis):
    rate = await redis.hget("exchange:usd", currency.lower())
    if not rate:
        currency = "usd"
        rate = await redis.hget("exchange:usd", currency)

    rate = Decimal(rate.decode())
    value = Decimal(price_usd) * rate

    price = int(value.quantize(Decimal("1"), rounding=ROUND_HALF_UP))

    return {"currency": currency, "price": price}


async def check_currency(currency, redis: Redis):
    check = await redis.hget("exchange:usd", currency.lower())
    if not check:
        currency = "usd"
        HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The currency is unknown. The default USD has been set instead.")
        return currency
    return currency