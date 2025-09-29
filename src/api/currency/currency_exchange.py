from fastapi import APIRouter, Query, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from redis.asyncio import Redis

from src.db.redis import get_redis
from src.services.currency.currency_exchange import convert

currency_router = APIRouter(prefix='/change_currency', tags=['change_currency'])
get_refresh_token = HTTPBearer()


@currency_router.get("/price/")
async  def get_price(price_usd: float, currency: str = Query("USD"), redis: Redis = Depends(get_redis)):
    try:
        response = {"currency": currency, "price": await convert(price_usd, currency, redis)}
        return response
    except:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown currency")