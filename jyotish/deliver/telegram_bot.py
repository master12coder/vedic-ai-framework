"""Telegram bot for chart delivery (optional — needs python-telegram-bot)."""

from __future__ import annotations

from typing import Any

from jyotish.config import get as cfg_get

TELEGRAM_MAX_CHARS = 4096
_DISPLAY_LIMIT = TELEGRAM_MAX_CHARS - 96  # Leave room for truncation notice


def create_bot() -> Any:
    """Create and configure the Telegram bot.

    Returns:
        telegram.ext.Application instance.

    Requires: pip install python-telegram-bot
    """
    try:
        from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
    except ImportError:
        raise RuntimeError(
            "python-telegram-bot not installed. Run: pip install python-telegram-bot\n"
            "Or install with: pip install vedic-ai-framework[telegram]"
        )

    token = cfg_get("daily.telegram_bot_token", "")
    if not token:
        raise RuntimeError(
            "Telegram bot token not configured. "
            "Set daily.telegram_bot_token in config.yaml or TELEGRAM_BOT_TOKEN env var."
        )

    app = ApplicationBuilder().token(token).build()

    async def start(update: Any, context: Any) -> None:
        """Handle /start command — send welcome message."""
        await update.message.reply_text(
            "Namaste! I am Jyotish AI.\n\n"
            "Send me birth details in this format:\n"
            "CHART Name | DD/MM/YYYY | HH:MM | Place\n\n"
            "Example:\n"
            "CHART Rajesh Kumar | 15/08/1990 | 06:30 | Jaipur"
        )

    async def handle_chart_request(update: Any, context: Any) -> None:
        """Parse birth details from message and reply with chart."""
        text = update.message.text
        if not text.startswith("CHART"):
            await update.message.reply_text("Send: CHART Name | DD/MM/YYYY | HH:MM | Place")
            return

        try:
            parts = text.replace("CHART ", "").split("|")
            name = parts[0].strip()
            dob = parts[1].strip()
            tob = parts[2].strip()
            place = parts[3].strip()

            from jyotish.compute.chart import compute_chart
            from jyotish.interpret.formatter import format_chart_terminal

            chart_data = compute_chart(name=name, dob=dob, tob=tob, place=place)
            report = format_chart_terminal(chart_data)

            if len(report) > _DISPLAY_LIMIT:
                report = report[:_DISPLAY_LIMIT] + "\n\n... (truncated)"

            await update.message.reply_text(report)
        except Exception as e:
            await update.message.reply_text(f"Error: {e}")

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_chart_request))

    return app


def run_bot() -> None:
    """Start the Telegram bot polling loop."""
    app = create_bot()
    app.run_polling()
