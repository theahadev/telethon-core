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
    logger.warning("Stub start() called.")
