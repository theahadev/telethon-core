import asyncio
import inspect
import os
import signal
import sys

from loguru import logger

from . import core


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
    core.config["log_telegram"] = core._setup_tg_log()
    logger.debug("Setting up extra variables in config")
    await core._setup_config_extras()
    # Check config for potential issues and log warnings if needed
    logger.debug("Checking configuration for potential issues")
    core._check_config()
    # Loaded extra variables, ready to handlers functions now
    logger.debug("Importing modules...")
    import modules  # noqa: E402, F401

    logger.debug("Registering bot commands")
    await core._register_commands()
    # Log bot start with username or user_id for clarity
    logger.info(
        f"""Bot started as {f"@{core.config['username']}" if core.config["username"] != "" else core.config["user_id"]}."""
    )
    logger.debug("Waiting for bot to disconnect...")
    await core.client.run_until_disconnected()


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
    await core.client.disconnect()
