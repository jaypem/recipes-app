import os
import logging
from logging.handlers import RotatingFileHandler


def get_logger(name: str = "llm_client") -> logging.Logger:
    LOG_PATH = os.getenv("LLM_LOG_PATH", "llm_client.log")
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    if not logger.hasHandlers():
        handler = RotatingFileHandler(LOG_PATH, maxBytes=5 * 1024 * 1024, backupCount=2)
        formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger
