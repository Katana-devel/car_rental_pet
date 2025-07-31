from redis.asyncio import Redis
import contextlib
from src.core.config import config


class RedisSessionManager:
    def __init__(self, host: str, port: int, db: int, password: str | None = None):
        self._redis_client = Redis(
            host=host,
            port=port,
            db=db,
            password=password,
        )

    async def connect(self):
        try:
            await self._redis_client.ping()
        except Exception as e:
            # log.error(f"Ошибка подключения к Redis: {e}")
            print("connection error")
            
    async def close(self):
        if self._redis_client:
            await self._redis_client.close()

    @contextlib.asynccontextmanager
    async def session(self):
        if self._redis_client is None:
            raise Exception("Redis is not initialized")
        yield self._redis_client



# Створюємо глобальний об'єкт менеджера Redis
redis_manager = RedisSessionManager(
    host=config.redis_config.REDIS_HOST,
    port=config.redis_config.REDIS_PORT,
    db=config.redis_config.REDIS_DB,
    password=config.redis_config.REDIS_PASSWORD
)


async def get_redis():
    async with redis_manager.session() as redis:
        yield redis