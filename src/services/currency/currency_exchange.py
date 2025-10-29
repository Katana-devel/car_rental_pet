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

        string_rates = {k: str(v) for k, v in rates.items()}
        await redis.hset("exchange:usd", mapping=string_rates)
        logger.info("Currency data updated")


async def convert(price_usd: float, currency: str, redis: Redis):
    currency_key = (currency or "usd").lower()
    rate_raw = await redis.hget("exchange:usd", currency_key)
    if not rate_raw:
        currency_key = "usd"
        rate_raw = await redis.hget("exchange:usd", currency_key)
        if not rate_raw:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Exchange rate not available"
            )

    if isinstance(rate_raw, memoryview):
        rate_raw = rate_raw.tobytes()

    if isinstance(rate_raw, (bytes, bytearray)):
        rate_str = rate_raw.decode('utf-8')
    else:
        rate_str = str(rate_raw)

    rate = Decimal(rate_str)
    value = Decimal(str(price_usd)) * rate
    price = int(value.quantize(Decimal("1"), rounding=ROUND_HALF_UP))

    return {"currency": currency_key, "price": price}


async def check_currency(currency, redis: Redis):
    check = await redis.hget("exchange:usd", currency.lower())
    if not check:
        currency = "usd"

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The currency is unknown. The default USD has been set instead."
        )
    return currency
