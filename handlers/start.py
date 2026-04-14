from typing import Any

from loguru import logger

import core


async def start_handler(event: Any) -> None:
    """Handle /start command from users.

    Provides different start text depending on the chat context:
    - Private chats: personalized greeting
    - Groups: group-specific greeting
    - Channels: channel-specific greeting

    Args:
        event: The event object from telethon containing message details
    """
    logger.debug(f"Start handler triggered by user: {event.sender_id}")
    try:
        message = ""

        # Handle private messages
        if event.is_private:
            message = """
This is a placeholder text for /start command in pm's.
"""
            logger.debug(
                f"Sending start text for private chat to user: {event.sender_id}"
            )

        # Handle group messages
        elif event.is_group:
            message = """
This is a placeholder text for /start command in groups.
"""
            logger.debug(f"Sending start text for group to user: {event.sender_id}")

        # Handle channel messages
        elif event.is_channel:
            message = """
This is a placeholder text for /start command in channels.
"""
            logger.debug(f"Sending start text for channel to user: {event.sender_id}")

        if message:
            await event.reply(message, parse_mode="markdown")
            logger.debug(
                f"Successfully replied to start command from user: {event.sender_id}"
            )
    except Exception as e:
        logger.error(f"Error in start_handler: {e}")
        raise


core.onMessage(start_handler, pattern=r"^/start(\s|$)")
logger.debug("Start handler successfully registered")
