"""
Structured logging configuration using loguru.
Provides a single `logger` import used across agents/services so that
real-time WebSocket streaming (Phase 3) can hook a sink into the same stream.
"""

import sys

from loguru import logger

from app.core.config import get_settings

settings = get_settings()


def configure_logging() -> None:
    logger.remove()  # drop default handler
    logger.add(
        sys.stdout,
        level=settings.log_level,
        colorize=True,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> "
            "- <level>{message}</level>"
        ),
    )
    logger.add(
        "logs/app.log",
        level="DEBUG",
        rotation="10 MB",
        retention="7 days",
        compression="zip",
        backtrace=True,
        diagnose=settings.app_env == "development",
    )


__all__ = ["logger", "configure_logging"]
