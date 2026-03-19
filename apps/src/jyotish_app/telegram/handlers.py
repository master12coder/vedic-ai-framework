"""Telegram bot handlers — /start, /daily, /level, /kundali commands."""
from __future__ import annotations

import json
import logging
from pathlib import Path


logger = logging.getLogger(__name__)

# Default chart path for the primary user
DEFAULT_CHART_DIR = Path("charts")

# User level preferences (in-memory, persisted to JSON)
_user_levels: dict[int, str] = {}
_LEVELS_FILE = Path("data/telegram_levels.json")


def _load_levels() -> None:
    """Load user level preferences from disk."""
    global _user_levels
    if _LEVELS_FILE.exists():
        _user_levels = json.loads(_LEVELS_FILE.read_text())


def _save_levels() -> None:
    """Save user level preferences to disk."""
    _LEVELS_FILE.parent.mkdir(parents=True, exist_ok=True)
    _LEVELS_FILE.write_text(json.dumps(_user_levels))


def _get_user_level(user_id: int) -> str:
    """Get user's preferred daily level."""
    if not _user_levels:
        _load_levels()
    return _user_levels.get(user_id, "medium")


def _load_chart(chart_path: str | None = None) -> ChartData | None:
    """Load a saved chart from JSON."""
    from jyotish_engine.models.chart import ChartData

    if chart_path:
        path = Path(chart_path)
    else:
        # Try default Manish chart
        path = DEFAULT_CHART_DIR / "manish.json"

    if not path.exists():
        return None

    return ChartData.model_validate_json(path.read_text())


async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command — welcome message."""
    welcome = (
        "🙏 नमस्ते! Welcome to **Jyotish AI** — your Vedic astrology companion.\n\n"
        "Commands:\n"
        "/daily — Today's personalized guidance\n"
        "/level simple|medium|detailed — Set detail level\n"
        "/kundali — Full birth chart report\n"
        "/help — Show this message\n\n"
        "Your chart is pre-loaded. Type /daily to get started!"
    )
    await update.message.reply_text(welcome, parse_mode="Markdown")


async def handle_daily(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /daily command — send today's guidance at user's preferred level."""
    user_id = update.effective_user.id
    level_str = _get_user_level(user_id)

    chart = _load_chart()
    if not chart:
        await update.message.reply_text(
            "❌ No chart found. Save a chart first with the CLI:\n"
            "`jyotish save --name 'Name' --dob 'DD/MM/YYYY' --tob 'HH:MM' "
            "--place 'City' -o charts/manish.json`",
            parse_mode="Markdown",
        )
        return

    from jyotish_products.plugins.daily.engine import DailyLevel, run_daily

    try:
        level = DailyLevel(level_str)
    except ValueError:
        level = DailyLevel.MEDIUM

    result = run_daily(chart, level)
    await update.message.reply_text(result)


async def handle_level(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /level command — set daily guidance detail level."""
    user_id = update.effective_user.id
    args = context.args

    valid_levels = {"simple", "medium", "detailed"}

    if not args or args[0].lower() not in valid_levels:
        current = _get_user_level(user_id)
        await update.message.reply_text(
            f"Current level: **{current}**\n\n"
            f"Usage: /level simple|medium|detailed\n"
            f"• simple — one line: rating | color | mantra\n"
            f"• medium — 5-7 lines with key info\n"
            f"• detailed — full transit analysis",
            parse_mode="Markdown",
        )
        return

    new_level = args[0].lower()
    _user_levels[user_id] = new_level
    _save_levels()
    await update.message.reply_text(f"✅ Level set to **{new_level}**", parse_mode="Markdown")


async def handle_kundali(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /kundali command — send full chart report."""
    chart = _load_chart()
    if not chart:
        await update.message.reply_text("❌ No chart found. Save one with the CLI first.")
        return

    from jyotish_products.plugins.kundali.report import generate_report

    # Send computation-only sections (no LLM needed)
    sections = [
        "chart_summary", "diamond_chart", "yogas", "doshas",
        "mahadasha_timeline", "current_dasha", "gemstones",
    ]
    report = generate_report(chart, sections=sections)

    # Telegram has a 4096 char limit — split if needed
    max_len = 4000
    if len(report) <= max_len:
        await update.message.reply_text(f"```\n{report}\n```", parse_mode="Markdown")
    else:
        # Split into chunks
        chunks = [report[i:i + max_len] for i in range(0, len(report), max_len)]
        for chunk in chunks:
            await update.message.reply_text(f"```\n{chunk}\n```", parse_mode="Markdown")


def register_handlers(app: Application) -> None:
    """Register all handlers with the telegram Application."""
    from telegram.ext import CommandHandler

    app.add_handler(CommandHandler("start", handle_start))
    app.add_handler(CommandHandler("help", handle_start))
    app.add_handler(CommandHandler("daily", handle_daily))
    app.add_handler(CommandHandler("level", handle_level))
    app.add_handler(CommandHandler("kundali", handle_kundali))
    logger.info("Telegram handlers registered: /start, /daily, /level, /kundali")
