# error_handler.py
from logger import logger

def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        # Позволяет завершать программу с Ctrl+C
        return
    logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))