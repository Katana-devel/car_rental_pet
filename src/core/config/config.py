import json
from typing import Optional
from pydantic import EmailStr, field_validator

from src.core.config.base_config import Settings
from src.models.users import Gender
from src.core.logger import logger
from src.core.config.base_config import BASE_DIR

class DBConfig(Settings):
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: int = 12348765
    POSTGRES_DB: str = "PPJ1"
    POSTGRES_HOST: str = "db"
    POSTGRES_PORT: int = 5432

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:"
            f"{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:"
            f"{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )
    class Config:
        env_file = BASE_DIR / ".env"
        env_file_encoding = 'utf-8'
    

class JWTConfig(Settings):
    SECRET_KEY: str = "1234567890"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    EMAIL_TOKEN_EXPIRE_DAYS: int = 7


class AdminConfig(Settings):
    ADMIN_PASSWORD: str = "admin"
    ADMIN_FULLNAME: str = "Admin User"
    ADMIN_AGE: int = 30
    ADMIN_GENDER: Gender = Gender.M
    ADMIN_EMAIL: str ="admin@example.com"

class RedisConfig(Settings):
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None
    REDIS_DB: int = 0


class RabbitMQConfig(Settings):
    RABBITMQ_DEFAULT_USER: str
    RABBITMQ_DEFAULT_PASS: str
    RABBITMQ_HOST: str = "rabbitmq"
    RABBITMQ_PORT:int = 5672

    @property
    def AMQP_URL(self) -> str:
        return f"amqp://{self.RABBITMQ_DEFAULT_USER}:{self.RABBITMQ_DEFAULT_PASS}@{self.RABBITMQ_HOST}:{self.RABBITMQ_PORT}/"

class EmailConfig(Settings):
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_PORT: int
    MAIL_SERVER: str
    MAIL_FROM_NAME: str

admin_config = AdminConfig()
db_config = DBConfig()
jwt_config = JWTConfig()
redis_config = RedisConfig()
rabbitmq_config = RabbitMQConfig()
email_config = EmailConfig()

# cloudinary_config = CloudinaryConfig()
print(f"DBConfig: {db_config.DATABASE_URL}")

