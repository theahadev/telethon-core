from typing import Any

from loguru import logger

import core


async def shutdown_handler(event: Any) -> None:
    """Handle /shutdown command from users.

    Provides different shutdown text depending on the chat context:
    - Private chats: personalized greeting
    - Groups: group-specific greeting
    - Channels: channel-specific greeting

    Args:
        event: The event object from telethon containing message details
    """
    logger.debug(f"shutdown handler triggered by user: {event.sender_id}")
    try:
        message = ""

        # Handle private messages
        if event.is_private:
            message = """
This is a placeholder text for /shutdown command in pm's.
"""
            await event.reply(message, parse_mode="markdown")
            logger.debug(
                f"Sending shutdown text for private chat to user: {event.sender_id}"
            )
            await core.shutdown("manual trigger from private chat")

        # Handle group messages
        elif event.is_group:
            message = """
This is a placeholder text for /shutdown command in groups.
"""
            await event.reply(message, parse_mode="markdown")
            logger.debug(f"Sending shutdown text for group to user: {event.sender_id}")
            await core.shutdown("manual trigger from group")

    except Exception as e:
        logger.error(f"Error in shutdown_handler: {e}")
        raise


core.on_message(shutdown_handler, pattern="/shutdown")
core.set_bot_command("shutdown", "Shut down the bot")
logger.debug("Shutdown handler successfully registered")
