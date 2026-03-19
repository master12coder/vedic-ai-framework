"""Telegram bot for daily companion delivery."""
from __future__ import annotations

import logging
import os


logger = logging.getLogger(__name__)


def start_bot(token: str | None = None) -> None:
    """Start the Telegram bot with all handlers.

    Args:
        token: Telegram bot token. If None, reads from TELEGRAM_BOT_TOKEN env var.
    """
    try:
        from telegram.ext import ApplicationBuilder
    except ImportError:
        raise ImportError(
            "Telegram bot requires python-telegram-bot. "
            "Install with: pip install 'jyotish[telegram]'"
        )

    bot_token = token or os.environ.get("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        raise ValueError(
            "No bot token provided. Set TELEGRAM_BOT_TOKEN env var or pass --token."
        )

    from jyotish_app.telegram.handlers import register_handlers

    logger.info("Starting Jyotish Telegram bot...")
    app = ApplicationBuilder().token(bot_token).build()
    register_handlers(app)
    logger.info("Bot running. Press Ctrl+C to stop.")
    app.run_polling()
