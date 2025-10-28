import json
from typing import Optional
from pydantic import EmailStr, field_validator

from src.core.config.base_config import Settings
from src.models.users import Gender
from src.core.logger import logger
from src.core.config.base_config import BASE_DIR

class DBConfig(Settings):
    DATABASE_URL: str
    class Config:
        env_file = BASE_DIR / ".env"
        env_file_encoding = 'utf-8'
    

class JWTConfig(Settings):
    SECRET_KEY: str = "1234567890"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    EMAIL_TOKEN_EXPIRE_DAYS: int = 7
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = 30


class AdminConfig(Settings):
    ADMIN_PASSWORD: str = "admin"
    ADMIN_FULLNAME: str = "Admin User"
    ADMIN_AGE: int = 30
    ADMIN_GENDER: Gender = Gender.M
    ADMIN_EMAIL: str ="admin@example.com"


class RedisConfig(Settings):
    REDIS_URL: str | None = None
    REDIS_HOST: str = "localhost"  # Default fallback
    REDIS_PORT: int = 6379  # Default fallback
    REDIS_PASSWORD: str | None = None
    REDIS_DB: int = 0

    class Config:
        env_file = BASE_DIR / ".env"
        env_file_encoding = 'utf-8'

    @property
    def url(self):
        if self.REDIS_URL:
            return self.REDIS_URL
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

class RabbitMQConfig(Settings):
    RABBITMQ_URL: str | None = None
    @property
    def AMQP_URL(self) -> str:
        return self.RABBITMQ_URL


class EmailConfig(Settings):
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_PORT: int
    MAIL_SERVER: str
    MAIL_FROM_NAME: str


class GoogleOID(Settings):
    CLIENT_ID:str
    CLIENT_SECRET:str
    GOOGLE_REDIRECT_URL:str
    GOOGLE_TOKEN_URL: str



admin_config = AdminConfig()
db_config = DBConfig()
jwt_config = JWTConfig()
redis_config = RedisConfig()
rabbitmq_config = RabbitMQConfig()
email_config = EmailConfig()
google_oid_config = GoogleOID()



