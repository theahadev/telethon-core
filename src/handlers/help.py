from typing import Any

from loguru import logger

import core


async def help_handler(event: Any) -> None:
    """Handle /help command from users.

    Provides different help text depending on the chat context:
    - Private chats: personalized greeting
    - Groups: group-specific greeting
    - Channels: channel-specific greeting

    Args:
        event: The event object from telethon containing message details
    """
    logger.debug(f"Help handler triggered by user: {event.sender_id}")
    try:
        message = ""

        # Handle private messages
        if event.is_private:
            message = """
This is a placeholder text for /help command in pm's.
"""
            logger.debug(
                f"Sending help text for private chat to user: {event.sender_id}"
            )

        # Handle group messages
        elif event.is_group:
            message = """
This is a placeholder text for /help command in groups.
"""
            logger.debug(f"Sending help text for group to user: {event.sender_id}")

        # Handle channel messages
        elif event.is_channel:
            message = """
This is a placeholder text for /help command in channels.
"""
            logger.debug(f"Sending help text for channel to user: {event.sender_id}")

        if message:
            await event.reply(message, parse_mode="markdown")
            logger.debug(
                f"Successfully replied to help command from user: {event.sender_id}"
            )
    except Exception as e:
        logger.error(f"Error in help_handler: {e}")
        raise


core.onMessage(help_handler, pattern=r"^/help(\s|$)")
logger.debug("Help handler successfully registered")
