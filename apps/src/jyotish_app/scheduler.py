"""Scheduler for daily Telegram messages at 5:30 AM IST."""
from __future__ import annotations

import json
import logging
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)

IST = ZoneInfo("Asia/Kolkata")
DAILY_HOUR = 5
DAILY_MINUTE = 30
SCHEDULE_FILE = Path("data/schedule_state.json")


def _next_run_time() -> datetime:
    """Calculate the next 5:30 AM IST."""
    now = datetime.now(tz=IST)
    target = now.replace(hour=DAILY_HOUR, minute=DAILY_MINUTE, second=0, microsecond=0)
    if now >= target:
        target += timedelta(days=1)
    return target


def _load_chart(chart_path: str = "charts/manish.json") -> "ChartData | None":
    """Load chart from JSON file."""
    from jyotish_engine.models.chart import ChartData

    path = Path(chart_path)
    if not path.exists():
        logger.error("Chart not found: %s", path)
        return None
    return ChartData.model_validate_json(path.read_text())


def _send_telegram_message(token: str, chat_id: str, message: str) -> bool:
    """Send a message via Telegram Bot API (no dependency on python-telegram-bot)."""
    import urllib.request
    import urllib.parse

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = urllib.parse.urlencode({
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown",
    }).encode()

    try:
        req = urllib.request.Request(url, data=data)
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status == 200
    except Exception as e:
        logger.error("Failed to send Telegram message: %s", e)
        return False


def run_scheduler(
    chart_path: str = "charts/manish.json",
    level: str = "medium",
    telegram_token: str | None = None,
    chat_id: str | None = None,
) -> None:
    """Run the daily scheduler loop.

    Sends daily guidance at 5:30 AM IST via Telegram.

    Args:
        chart_path: Path to saved chart JSON.
        level: Daily guidance level (simple/medium/detailed).
        telegram_token: Telegram bot token (or TELEGRAM_BOT_TOKEN env).
        chat_id: Telegram chat ID (or TELEGRAM_CHAT_ID env).
    """
    token = telegram_token or os.environ.get("TELEGRAM_BOT_TOKEN", "")
    target_chat = chat_id or os.environ.get("TELEGRAM_CHAT_ID", "")

    if not token or not target_chat:
        logger.error("Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID env vars")
        return

    logger.info("Scheduler started. Daily at %02d:%02d IST", DAILY_HOUR, DAILY_MINUTE)

    while True:
        next_run = _next_run_time()
        wait_seconds = (next_run - datetime.now(tz=IST)).total_seconds()
        logger.info("Next run: %s (in %.0f seconds)", next_run.isoformat(), wait_seconds)

        time.sleep(max(0, wait_seconds))

        # Generate daily guidance
        chart = _load_chart(chart_path)
        if not chart:
            logger.error("Could not load chart. Skipping today.")
            continue

        from jyotish_products.plugins.daily.engine import DailyLevel, run_daily

        try:
            daily_level = DailyLevel(level)
        except ValueError:
            daily_level = DailyLevel.MEDIUM

        message = run_daily(chart, daily_level)
        logger.info("Generated daily message (%d chars)", len(message))

        success = _send_telegram_message(token, target_chat, message)
        if success:
            logger.info("Daily message sent to chat %s", target_chat)
        else:
            logger.error("Failed to send daily message")

        # Sleep 1 minute to avoid double-sending
        time.sleep(60)
