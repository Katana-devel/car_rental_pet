from pathlib import Path
import os
from pydantic_settings import BaseSettings
from pydantic import ConfigDict

# === Paths ===
BASE_DIR = Path(__file__).resolve().parents[3]
LOGS_DIR = BASE_DIR / "logs"
INFO_LOG_FILE = LOGS_DIR / "app.log"
ERROR_LOG_FILE = LOGS_DIR / "error.log"
WARNING_LOG_FILE = LOGS_DIR / "warning.log"
DEBUG_LOG_FILE = LOGS_DIR / "debug.log"


# === Base settings ===
class Settings(BaseSettings):
    model_config = ConfigDict(
        extra="ignore",
        env_file=os.path.join(BASE_DIR, ".env"), 
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


# === App config ===
class AppConfig(Settings):
    DEBUG: bool = False


# === Start config ===
class StartAppConfig(Settings):
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000


# === Instances ===
app_config = AppConfig()
start_app_config = StartAppConfig()
