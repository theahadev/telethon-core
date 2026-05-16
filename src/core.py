"""
core.py — shared bot state and event registration helpers.

Set `bot` and `config` before importing any handlers:
    import core
    core.bot = TelegramClient(...)
    core.config = {...}
    core.setupLogging()  # Call after core.config is populated
"""

import asyncio
import inspect
import os
import signal
import sys
from typing import Any, Callable, Dict, Optional, cast

from loguru import logger
from telethon import TelegramClient, events, functions, types

# Global bot state
bot: TelegramClient = None  # ty: ignore[invalid-assignment]
# Global config dict
config: Dict[str, str | bool] = None  # ty: ignore[invalid-assignment]
# Commands queued for registration
commands: list[types.BotCommand] = []


#################################################
# Event registration helpers
#################################################
def on_message(func: Callable[..., Any], pattern: Optional[str] = None) -> None:
    """Listen for new messages. Optionally filter by regex pattern."""
    func_name = getattr(func, "__name__", repr(func))
    logger.debug(f"Registering on_message handler: {func_name}, pattern={pattern}")
    bot.on(events.NewMessage(pattern=pattern))(func)


def on_edit(func: Callable[..., Any], pattern: Optional[str] = None) -> None:
    """Listen for edited messages. Optionally filter by regex pattern."""
    func_name = getattr(func, "__name__", repr(func))
    logger.debug(f"Registering on_edit handler: {func_name}, pattern={pattern}")
    bot.on(events.MessageEdited(pattern=pattern))(func)


def on_delete(func: Callable[..., Any]) -> None:
    """Listen for deleted messages. Only provides deleted_id/deleted_ids, no message content."""
    func_name = getattr(func, "__name__", repr(func))
    logger.debug(f"Registering on_delete handler: {func_name}")
    bot.on(events.MessageDeleted())(func)


def on_read(func: Callable[..., Any]) -> None:
    """Listen for messages being read."""
    func_name = getattr(func, "__name__", repr(func))
    logger.debug(f"Registering on_read handler: {func_name}")
    bot.on(events.MessageRead())(func)


def on_callback(func: Callable[..., Any], pattern: Optional[str] = None) -> None:
    """Listen for inline keyboard button presses. Optionally filter by regex pattern."""
    func_name = getattr(func, "__name__", repr(func))
    logger.debug(f"Registering on_callback handler: {func_name}, pattern={pattern}")
    bot.on(events.CallbackQuery(pattern=pattern))(func)


def on_inline(func: Callable[..., Any], pattern: Optional[str] = None) -> None:
    """Listen for inline queries (@bot something). Optionally filter by regex pattern."""
    func_name = getattr(func, "__name__", repr(func))
    logger.debug(f"Registering on_inline handler: {func_name}, pattern={pattern}")
    bot.on(events.InlineQuery(pattern=pattern))(func)


def on_chat_action(func: Callable[..., Any]) -> None:
    """Listen for chat actions: users joining/leaving, title changes, pins, etc."""
    func_name = getattr(func, "__name__", repr(func))
    logger.debug(f"Registering on_chat_action handler: {func_name}")
    bot.on(events.ChatAction())(func)


def on_user_update(func: Callable[..., Any]) -> None:
    """Listen for user updates: typing indicators, online status, etc."""
    func_name = getattr(func, "__name__", repr(func))
    logger.debug(f"Registering on_user_update handler: {func_name}")
    bot.on(events.UserUpdate())(func)


def on_raw(func: Callable[..., Any]) -> None:
    """Listen for raw Telegram Update objects. Unabstracted, use as last resort."""
    func_name = getattr(func, "__name__", repr(func))
    logger.debug(f"Registering on_raw handler: {func_name}")
    bot.on(events.Raw())(func)


#################################################
# Command registering with trigger character
#################################################
# This is mostly relevant for user accounts, yet won't hurt to have
# both ways compatibility in bots too.
def on_command(func: Callable[..., Any], command: str, catchall: bool = True) -> None:
    """Listen for messages starting with a specific command trigger character."""
    func_name = getattr(func, "__name__", repr(func))

    if config["is_bot"]:
        if catchall:
            # Matches both /command and /command@username
            pattern = (
                rf"^{config['trigger_char']}{command}(@{config['username']})?(\s|$)"
            )
        else:
            # Matches only /command@username, to avoid conflicts in groups with multiple bots
            # FIXME: users will be annoyed to use /command@username in pm instead of /command
            pattern = rf"^{config['trigger_char']}{command}@{config['username']}"
    else:
        if config["username"] == "":
            logger.warning(
                "Username was not found. on_command handlers be broken (/command@)."
            )
        if catchall:
            # For user accounts, catchall works differently, no username suffix
            pattern = (
                rf"^{config['trigger_char']}{command}(@{config['username']})?(\s|$)"
            )
        else:
            # I mean, if they really wanna disable catchall and have manual trigger, let them
            logger.debug(
                "User account with catchall disabled: using exact match pattern without username suffix"
            )
            pattern = rf"^{config['trigger_char']}{command}@{config['username']}"
    logger.debug(f"Registering on_command handler: {func_name}, command={command}")
    bot.on(events.NewMessage(pattern=pattern))(func)


#################################################
# Setting bot commands list with the API
#################################################
def set_bot_command(command: str, description: str) -> None:
    """Queue a bot command for registration with Telegram.

    Call this from your handler modules. Commands are sent to the
    Telegram API in bulk when registerCommands() is awaited.
    """
    commands.append(types.BotCommand(command=command.lower(), description=description))
    logger.debug(f"Queued command: /{command.lower()} - {description}")


async def _register_commands() -> None:
    """Register bot commands from commands.txt file.

    Reads commands in format: COMMAND=Description
    Registers them with Telegram's bot command API.
    """
    logger.debug("registerCommands() called")
    try:
        logger.debug(f"Setting {len(commands)} bot commands")
        await bot(
            functions.bots.SetBotCommandsRequest(
                scope=types.BotCommandScopeDefault(),
                lang_code="en",
                commands=commands,
            )
        )
        logger.info(f"Successfully registered {len(commands)} bot commands.")
    except Exception as e:
        logger.error(f"Error registering bot commands: {e}", exc_info=True)


#################################################
# Bot lifecycle management
#################################################
async def start() -> None:
    """Start the bot and run until disconnected. Handles graceful shutdown on SIGINT/SIGTERM."""
    logger.debug("start() called, setting up event loop and signal handlers")
    loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(
            sig, lambda s=sig: asyncio.ensure_future(shutdown(reason=s.name))
        )
    logger.debug("Signal handlers registered for SIGINT and SIGTERM")
    # Add Telegram log handler after bot is running, so we can send messages
    logger.debug("Setting up Telegram logging")
    config["log_telegram"] = _setup_tg_log()
    logger.debug("Setting up extra variables in config")
    await _setup_config_extras()
    # Check config for potential issues and log warnings if needed
    logger.debug("Checking configuration for potential issues")
    _check_config()
    logger.debug("Registering bot commands")
    await _register_commands()
    # Log bot start with username or user_id for clarity
    logger.info(
        f"""Bot started as {f"@{config['username']}" if config["username"] != "" else config["user_id"]}."""
    )
    logger.debug("Waiting for bot to disconnect...")
    await bot.run_until_disconnected()


def restart() -> None:
    """Restart the bot by re-executing the current Python script."""
    logger.debug(f"restart() called with executable: {sys.executable}")
    logger.info("Restarting bot...")
    os.execv(sys.executable, [sys.executable] + sys.argv)


async def shutdown(reason: str = "Unknown") -> None:
    """Gracefully shut down the bot."""
    # Extract caller information for logging
    if reason in ("SIGINT", "SIGTERM"):
        caller = "OS signal"
    else:
        frame = inspect.stack()[1]
        caller = f"{frame.filename}:{frame.lineno} in {frame.function}"
    logger.debug("shutdown() called, disconnecting bot")
    logger.info(f"Bot stopped. Reason: {reason} | Caller: {caller}")
    await logger.complete()
    await bot.disconnect()


#################################################
# Logging functions
#################################################
async def _log_to_telegram(message: Any) -> None:
    """Send log messages to Telegram."""
    record: Any = message.record

    level: str = record["level"].name
    name: str = record["name"]
    function: str = record["function"]
    line: int = record["line"]
    text: str = record["message"]
    time: str = record["time"].strftime("%d/%m/%Y %H:%M:%S")
    extra: Dict[str, Any] = record["extra"]

    msg: str = (
        f"**#{level}**\n"
        f"**Time:** `{time}`\n"
        f"**Module:** `{name}.{function}:{line}`\n\n"
        f"**Details:** `{text}`\n"
        + (f"\n**Debug:** `{extra['debug']}`" if extra.get("debug") else "")
    )
    await bot.send_message(int(config["log_channel"]), msg)


def _setup_tg_log() -> bool:
    """Set up Telegram log handler if log_channel is configured."""
    logger.debug("Initiating telegram logging setup")
    log_level_telegram = config["log_level_telegram"]
    log_channel = config["log_channel"]

    # Exit if log_level_telegram is NONE, because logging is disabled.
    if log_level_telegram == "NONE":
        logger.debug("Telegram logging is disabled (log_level_telegram=NONE)")
        return False

    # Exit if log_channel is not set, because no destination configured.
    if log_channel == "NONE":
        logger.warning(
            "LOG_LEVEL_TELEGRAM is set but LOG_CHANNEL is not configured. Telegram logging will be disabled."
        )
        return False

    logger.debug(
        f"Adding Telegram log handler with level: {log_level_telegram}, channel: {log_channel}"
    )
    logger.add(_log_to_telegram, level=log_level_telegram, enqueue=True)
    return True


_log_format: str = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green>"
    " | <level>{level: <8}</level>"
    " | <cyan>{name: <16}</cyan>"
    " | <cyan>{function: <20}</cyan> | <cyan>{line: >03}</cyan>"
    " - <level>{message}</level>"
)


def _setup_stdout_log() -> bool:
    """Set up stdout logging based on configuration from core.config."""
    logger.debug("Initiating stdout logging setup")
    # If you need the logs before stdout logging is set up, comment out the next line.
    logger.remove()  # Remove default logger
    logger.debug("Removed default logger handlers")
    logger.debug("Fun fact: these last 2 comments are invisible in the logs :D")

    # Read logging configuration from core.config
    log_level_stdout = config["log_level_stdout"]

    # Exit if log_level_stdout is NONE, because logging is disabled.
    if log_level_stdout == "NONE":
        logger.debug("Stdout logging is disabled (log_level_stdout=NONE)")
        return False

    # Filter out logs with level >= 40 (ERROR and above) from stdout
    # they will be sent to stderr and Telegram instead
    def stdout_filter(record: Any) -> bool:
        return record["level"].no < 40

    # Add stdout handler
    logger.debug(f"Adding stdout handler with level: {log_level_stdout}")
    logger.add(
        sys.stdout,
        format=_log_format,
        level=log_level_stdout,
        filter=stdout_filter,
    )

    # Add stderr handler
    logger.debug("Adding stderr handler with level: ERROR")
    logger.add(sys.stderr, format=_log_format, level="ERROR")
    return True


def _setup_file_log() -> bool:
    """Set up file logging based on configuration from core.config."""
    logger.debug("Initiating file logging setup")

    # Read logging configuration from core.config
    log_level_file = config["log_level_file"]
    log_file_path = config["log_file_path"]

    log_rotation = config["log_rotation"]
    log_retention = config["log_retention"]
    log_compression = config["log_compression"]

    # Exit if log_level_file is NONE, because logging is disabled.
    if log_level_file == "NONE":
        logger.debug("File logging is disabled (log_level_file=NONE)")
        return False

    # Exit if log_file_path is not set, because no destination configured.
    if log_file_path == "NONE":
        logger.warning(
            "LOG_LEVEL_FILE is set but LOG_FILE_PATH is not configured. File logging will be disabled."
        )
        return False

    logger.debug(
        f"Setting up file logging level: {log_level_file}, path: {log_file_path}"
    )

    file_handler_kwargs = {
        "format": _log_format,
        "level": log_level_file,
        "enqueue": True,
    }

    if log_rotation != "NONE":
        file_handler_kwargs["rotation"] = log_rotation
        logger.debug(f"File rotation enabled: {log_rotation}")

    if log_retention != "NONE":
        file_handler_kwargs["retention"] = log_retention
        logger.debug(f"File retention enabled: {log_retention}")

    if log_compression != "NONE":
        file_handler_kwargs["compression"] = log_compression
        logger.debug(f"File compression enabled: {log_compression}")

    logger.add(log_file_path, **file_handler_kwargs)  # ty: ignore
    return True


#################################################
# Config management and extras setup
#################################################


async def _setup_config_extras() -> None:
    config["is_bot"] = await bot.is_bot()
    me = cast(types.User, await bot.get_me(input_peer=False))
    config["user_id"] = str(me.id)
    # im too tired to figure out falsy
    config["username"] = me.username if me.username else ""


def _check_config() -> None:
    """Check some variables and complain if they are unfitting for situation."""
    if config["trigger_char"] == "":
        logger.warning("Trigger character is empty. on_command handlers might misfire.")
    if not config["is_bot"] and config["trigger_char"] == "/":
        logger.warning(
            "Using '/' (forward slash) as trigger character for user accounts can cause conflicts with normal bots. Consider changing trigger_char in config."
        )
