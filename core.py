"""
core.py — shared bot state and event registration helpers.

Set `bot` and `data` before importing any handlers:
    import core
    core.bot = TelegramClient(...)
    core.data = {...}
    core.setupLogging()  # Call after core.data is populated
"""

import asyncio
import os
import signal
import sys
from typing import Any, Callable, Dict, Optional

from loguru import logger
from telethon import TelegramClient, events

bot: Optional[TelegramClient] = None
data: Optional[Dict[str, Any]] = None

# If you need the logs before setupLogging() is called,
# comment out the next line. The logs will be on stderr.
logger.remove()  # kill default handler immediately


# Event registration helpers
def onMessage(func: Callable[..., Any], pattern: Optional[str] = None) -> None:
    """Listen for new messages. Optionally filter by regex pattern."""
    assert bot is not None
    logger.debug(f"Registering onMessage handler: {func.__name__}, pattern={pattern}")
    bot.on(events.NewMessage(pattern=pattern))(func)


def onEdit(func: Callable[..., Any], pattern: Optional[str] = None) -> None:
    """Listen for edited messages. Optionally filter by regex pattern."""
    assert bot is not None
    logger.debug(f"Registering onEdit handler: {func.__name__}, pattern={pattern}")
    bot.on(events.MessageEdited(pattern=pattern))(func)


def onDelete(func: Callable[..., Any]) -> None:
    """Listen for deleted messages. Only provides deleted_id/deleted_ids, no message content."""
    assert bot is not None
    logger.debug(f"Registering onDelete handler: {func.__name__}")
    bot.on(events.MessageDeleted())(func)


def onRead(func: Callable[..., Any]) -> None:
    """Listen for messages being read."""
    assert bot is not None
    logger.debug(f"Registering onRead handler: {func.__name__}")
    bot.on(events.MessageRead())(func)


def onCallback(func: Callable[..., Any], pattern: Optional[str] = None) -> None:
    """Listen for inline keyboard button presses. Optionally filter by regex pattern."""
    assert bot is not None
    logger.debug(f"Registering onCallback handler: {func.__name__}, pattern={pattern}")
    bot.on(events.CallbackQuery(pattern=pattern))(func)


def onInline(func: Callable[..., Any], pattern: Optional[str] = None) -> None:
    """Listen for inline queries (@bot something). Optionally filter by regex pattern."""
    assert bot is not None
    logger.debug(f"Registering onInline handler: {func.__name__}, pattern={pattern}")
    bot.on(events.InlineQuery(pattern=pattern))(func)


def onChatAction(func: Callable[..., Any]) -> None:
    """Listen for chat actions: users joining/leaving, title changes, pins, etc."""
    assert bot is not None
    logger.debug(f"Registering onChatAction handler: {func.__name__}")
    bot.on(events.ChatAction())(func)


def onUserUpdate(func: Callable[..., Any]) -> None:
    """Listen for user updates: typing indicators, online status, etc."""
    assert bot is not None
    logger.debug(f"Registering onUserUpdate handler: {func.__name__}")
    bot.on(events.UserUpdate())(func)


def onRaw(func: Callable[..., Any]) -> None:
    """Listen for raw Telegram Update objects. Unabstracted, use as last resort."""
    assert bot is not None
    logger.debug(f"Registering onRaw handler: {func.__name__}")
    bot.on(events.Raw())(func)


# Bot lifecycle management
async def run() -> None:
    """Start the bot and run until disconnected. Handles graceful shutdown on SIGINT/SIGTERM."""
    logger.debug("run() called, setting up event loop and signal handlers")
    loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: asyncio.ensure_future(shutdown()))
    logger.debug("Signal handlers registered for SIGINT and SIGTERM")
    # Add Telegram log handler after bot is running, so we can send messages
    logger.debug("Setting up Telegram logging")
    setupTelegramLog()
    logger.info("Bot started.")
    assert bot is not None
    logger.debug("Waiting for bot to disconnect...")
    await bot.run_until_disconnected()  # type: ignore


def restart() -> None:
    """Restart the bot by re-executing the current Python script."""
    logger.debug(f"restart() called with executable: {sys.executable}")
    logger.info("Restarting bot...")
    os.execv(sys.executable, [sys.executable] + sys.argv)


async def shutdown() -> None:
    """Gracefully shut down the bot."""
    logger.debug("shutdown() called, disconnecting bot")
    logger.info("Bot stopped.")
    assert bot is not None
    await bot.disconnect()  # type: ignore


# Logging setup
log_format: str = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green>"
    " | <level>{level: <9}</level>"
    " | <cyan>{name: <10}</cyan>"
    " | <cyan>{function: <20}</cyan> | <cyan>{line: >03}</cyan>"
    " - <level>{message}</level>"
)


async def logToTelegram(message: Any) -> None:
    """Send log messages to Telegram."""
    record: Any = message.record

    level: str = record["level"].name
    name: str = record["name"]
    function: str = record["function"]
    line: int = record["line"]
    text: str = record["message"]
    time: str = record["time"].strftime("%d/%m/%Y %H:%M:%S")
    extra: Dict[str, Any] = record["extra"]

    logger.debug(
        f"logToTelegram: Sending {level} message from {name}.{function}:{line}"
    )
    msg: str = (
        f"**#{level}**\n"
        f"**Time:** `{time}`\n"
        f"**Module:** `{name}.{function}:{line}`\n\n"
        f"**Details:** `{text}`\n"
        + (f"\n**Debug:** `{extra['debug']}`" if extra.get("debug") else "")
    )
    assert bot is not None
    assert data is not None
    await bot.send_message(data["log_channel"], msg)


def setupTelegramLog() -> None:
    """Set up Telegram log handler if log_channel is configured."""
    logger.debug("setupTelegramLog() called")
    assert data is not None
    log_level_telegram = data.get("log_level_telegram")
    log_channel = data.get("log_channel")
    logger.debug(
        f"Telegram log config - channel: {log_channel}, level: {log_level_telegram}"
    )
    if log_channel:
        if log_level_telegram is None:
            logger.warning("LOG_LEVEL_TELEGRAM is not set. Defaulting to INFO.")
        logger.debug(
            f"Adding Telegram log handler with level: {log_level_telegram or 'INFO'}"
        )
        logger.add(logToTelegram, level=log_level_telegram or "INFO", enqueue=True)
    elif log_level_telegram is not None:
        logger.warning(
            "LOG_LEVEL_TELEGRAM is set but LOG_CHANNEL is not configured. Telegram logging will be disabled."
        )


def setupLogging() -> None:
    """Set up logging based on configuration from core.data."""
    logger.debug("setupLogging() called")
    assert data is not None

    logger.remove()  # Remove default logger
    logger.debug("Removed default logger handlers")

    log_level_stdout = data.get("log_level_stdout")
    log_level_file = data.get("log_level_file")
    log_file_path = data.get("log_file_path")
    log_rotation = data.get("log_rotation")
    log_retention = data.get("log_retention")
    log_compression = data.get("log_compression")

    logger.debug(
        f"Logging config - stdout: {log_level_stdout}, file: {log_level_file}, path: {log_file_path}"
    )

    # Filter out logs with level >= 40 (ERROR and above) from stdout
    # they will be sent to stderr and Telegram instead
    def stdoutFilter(record: Any) -> bool:
        return record["level"].no < 40

    # Add stdout handler
    logger.debug(f"Adding stdout handler with level: {log_level_stdout or 'INFO'}")
    logger.add(
        sys.stdout,
        format=log_format,
        level=log_level_stdout or "INFO",
        filter=stdoutFilter,
    )

    # Add stderr handler
    logger.debug("Adding stderr handler with level: ERROR")
    logger.add(sys.stderr, format=log_format, level="ERROR")

    # Add file handler if path is specified
    if log_file_path:
        logger.debug(f"Setting up file logging to: {log_file_path}")
        file_handler_kwargs = {
            "format": log_format,
            "level": log_level_file or "INFO",
            "enqueue": True,
        }
        if log_rotation is not None:
            file_handler_kwargs["rotation"] = log_rotation
            logger.debug(f"File rotation enabled: {log_rotation}")
        if log_retention is not None:
            file_handler_kwargs["retention"] = log_retention
            logger.debug(f"File retention enabled: {log_retention}")
        if log_compression is not None:
            file_handler_kwargs["compression"] = log_compression
            logger.debug(f"File compression enabled: {log_compression}")
        logger.add(log_file_path, **file_handler_kwargs)
        if log_level_file is None:
            logger.warning("LOG_LEVEL_FILE is not set. Defaulting to INFO.")

    elif log_level_file:
        logger.warning(
            "LOG_LEVEL_FILE is set but LOG_FILE_PATH is not configured. File logging will be disabled."
        )
