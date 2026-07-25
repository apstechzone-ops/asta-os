from backend.logging_ import get_logger

logger = get_logger(__name__)


async def log_reminder(message: str) -> None:
    logger.info("[Reminder] %s", message)
