from typing import Any

from loguru import logger
from telethon.tl.types import User

import core


async def addchat_handler(event: Any) -> None:
    """Handle chat action events when bot is added to groups or channels.

    Sends welcome messages when the bot is added to a new chat.
    Handles both group and channel contexts.

    Args:
        event: The ChatAction event object from telethon containing action details
    """
    logger.debug(f"Add chat handler triggered in chat: {event.chat_id}")
    try:
        # Get current bot info
        assert core.bot is not None
        bot_me = await core.bot.get_me()

        # Assert that bot_me is a User instance with an id
        assert isinstance(bot_me, User), f"Expected User, got {type(bot_me)}"
        bot_id = bot_me.id
        logger.debug(f"Bot ID: {bot_id}")

        # Check if this is a user addition/join event and the bot was added
        if (event.user_added or event.user_joined) and not event.action_message:
            assert hasattr(event, "user_ids"), "Event missing user_ids attribute"

            if bot_id in event.user_ids:
                logger.debug(f"Bot was added to chat. Chat ID: {event.chat_id}")

                # Send welcome message based on chat type
                if event.is_group:
                    message = "This is a placeholder text for when the bot is added in groups."
                    logger.debug(f"Sending welcome message to group: {event.chat_id}")
                    await event.reply(message)

                elif event.is_channel:
                    message = "This is a placeholder text for when the bot is added in channels."
                    logger.debug(f"Sending welcome message to channel: {event.chat_id}")
                    await event.reply(message)

                logger.debug(
                    f"Successfully sent welcome message to chat: {event.chat_id}"
                )
            else:
                logger.debug(
                    f"User added event but bot ({bot_id}) not in user_ids: {event.user_ids}"
                )
    except Exception as e:
        logger.error(f"Error in addchat_handler: {e}", exc_info=True)
        raise


core.onChatAction(addchat_handler)
logger.debug("Add chat handler successfully registered")
