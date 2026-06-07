# lifecycle.py
#
# still figuring out the function naming, unstable

from loguru import logger

from . import bot, state


def start_loop():
    logger.debug("Starting TelegramClient...")
    assert state.client, "TelegramClient not initialized, call init_client() first"
    with state.client.start():
        logger.debug("TelegramClient started successfully. Running bot...")
        # TODO: bot.start() refers to the old start() function in bot.py, replace it
        state.client.loop.run_until_complete(bot.start())
    logger.debug("TelegramClient context exited.")


def start():
    """Start the process and run until shutdown."""
    logger.warning("Stub start() called.")


def shutdown():
    """Gracefully shut down the process."""
    logger.warning("Stub shutdown() called.")


def restart():
    """Restart the process by using os.execv()."""
    logger.warning("Stub restart() called.")
