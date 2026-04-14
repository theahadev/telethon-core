from typing import Any

from loguru import logger

import core


async def start_handler(event: Any) -> None:
    """Handle /start command from users.

    Args:
        event: The event object from telethon containing message details
    """
    logger.debug(f"Start handler triggered by user: {event.sender_id}")
    try:
        logger.debug("Sending start response message")
        await event.reply("meow meow mrow...")
        logger.debug(
            f"Successfully replied to start command from user: {event.sender_id}"
        )
    except Exception as e:
        logger.error(f"Error in start_handler: {e}")
        raise


core.onMessage(start_handler, pattern=r"^/start(\s|$)")
logger.debug("Start handler successfully registered")
