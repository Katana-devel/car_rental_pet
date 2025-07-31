import logging
import os
from src.core.config.base_config import app_config, INFO_LOG_FILE, ERROR_LOG_FILE, WARNING_LOG_FILE, DEBUG_LOG_FILE, LOGS_DIR

class ErrorTypeFilter(logging.Filter):
    def __init__(self, allowed_roles):
        super().__init__()
        self.allowed_roles = allowed_roles

    def filter(self, record):
        return record.levelname in self.allowed_roles



def setup_logger():
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("backend_app_logger")
    if app_config.DEBUG:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)


    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    info_file_handler = logging.FileHandler(INFO_LOG_FILE, encoding="utf-8")
    info_file_handler.setLevel(logging.INFO)
    info_file_handler.setFormatter(formatter)
    info_file_handler.addFilter(ErrorTypeFilter(["INFO"]))


    error_file_handler = logging.FileHandler(ERROR_LOG_FILE, encoding="utf-8")
    error_file_handler.setLevel(logging.ERROR)
    error_file_handler.setFormatter(formatter)
    error_file_handler.addFilter(ErrorTypeFilter(["ERROR"]))


    warning_file_handler = logging.FileHandler(WARNING_LOG_FILE, encoding="utf-8")
    warning_file_handler.setLevel(logging.WARNING)
    warning_file_handler.setFormatter(formatter)
    warning_file_handler.addFilter(ErrorTypeFilter(["WARNING"]))


    console_file_handler = logging.StreamHandler()
    console_file_handler.setLevel(logging.INFO)
    console_file_handler.setFormatter(formatter)


    debug_file_handler = logging.FileHandler(DEBUG_LOG_FILE, encoding="utf-8")
    debug_file_handler.setLevel(logging.DEBUG)
    debug_file_handler.setFormatter(formatter)
    debug_file_handler.addFilter(ErrorTypeFilter(["DEBUG"]))


    logger.addHandler(info_file_handler)
    logger.addHandler(error_file_handler)
    logger.addHandler(warning_file_handler)
    logger.addHandler(console_file_handler)

    if app_config.DEBUG:
        logger.addHandler(debug_file_handler)


    return logger


logger = setup_logger()