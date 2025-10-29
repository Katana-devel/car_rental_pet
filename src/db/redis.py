from redis.asyncio import Redis
import contextlib
import ssl as ssl_module

from src.core.config import config
from src.core.logger.logger import logger


class RedisSessionManager:
    def __init__(self, host: str, port: int, db: int, password: str | None = None, url: str | None = None):
        if url:
            # For Upstash Redis URLs (rediss://)
            ssl_context = ssl_module.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl_module.CERT_NONE

            self._redis_client = Redis.from_url(
                url,
                decode_responses=True,
                ssl_cert_reqs=ssl_module.CERT_NONE
            )
        else:
            # For manual configuration with SSL
            self._redis_client = Redis(
                host=host,
                port=port,
                db=db,
                password=password,
                ssl=True,
                ssl_cert_reqs=ssl_module.CERT_NONE,
                decode_responses=True
            )

    async def connect(self):
        try:
            await self._redis_client.ping()
            logger.info("Connected to Redis successfully")
        except Exception as e:
            logger.error(f"Error connecting to Redis: {e}")
            raise

    async def close(self):
        if self._redis_client:
            await self._redis_client.close()

    @contextlib.asynccontextmanager
    async def session(self):
        if self._redis_client is None:
            raise Exception("Redis is not initialized")
        yield self._redis_client


redis_manager = RedisSessionManager(
    host=config.redis_config.REDIS_HOST,
    port=config.redis_config.REDIS_PORT,
    db=config.redis_config.REDIS_DB,
    password=config.redis_config.REDIS_PASSWORD,
    url=getattr(config.redis_config, "REDIS_URL", None)
)


async def get_redis():
    async with redis_manager.session() as redis:
        yield redis
