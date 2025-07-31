from pathlib import Path
import os

from pydantic_settings import BaseSettings
from pydantic import ConfigDict

BASE_DIR = Path(__file__).resolve().parents[3]
LOGS_DIR = BASE_DIR / 'logs'
INFO_LOG_FILE = LOGS_DIR / 'app.log'
ERROR_LOG_FILE = LOGS_DIR / 'error.log'
WARNING_LOG_FILE = LOGS_DIR / 'warning.log' 
DEBUG_LOG_FILE = LOGS_DIR / 'debug.log'

# pydantic from .env
class Settings(BaseSettings):
    model_config = ConfigDict(
        extra="ignore",
        env_file=os.path.join(BASE_DIR, ".env"),
        case_sensitive=True,
        env_file_encoding="utf-8",
    )
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not os.path.exists(os.path.join(BASE_DIR, ".env")):
            raise Exception(".env file not found. Using default or system environment variables.")


class AppConfig(Settings):
    DEBUG: bool = False

class StartAppConfig(Settings):
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000

app_config = AppConfig()
start_app_config = StartAppConfig()