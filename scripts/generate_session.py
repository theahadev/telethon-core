# scripts/generate_session.py
"""
Session String Generator for Telethon Bot
This script generates a session string for your Telethon bot.
"""

# TODO: add interactive generator with api id/hash inputs, and suggest generating a .env file with moving the old one to .env.bak
#
import asyncio

from telethon import TelegramClient
from telethon.sessions import StringSession

# Default android API credentials
# they work fine, if you get any weird quirks, try creating your own API credentials
# refer to docs/session.md for instructions

API_ID = 5
API_HASH = "1c5c96d5edd401b1ed40db3fb5633e2d"
session_file = "session_string.txt"


def verify_secrets() -> bool:
    # actually its not even neccessary since we dont load from
    # env file but anyway
    try:
        int(API_ID)
    except ValueError:
        print("Error: API_ID must be a valid integer")
        return False
    return True


async def authenticate_session() -> str:
    """Generate a session string for the bot"""
    print("Session String generator for telethon based applications\n")
    print("You will need to log in with your phone number or a bot token.")
    print("Waiting for telethon client to start and authenticate...\n")
    # Create client with StringSession
    async with TelegramClient(StringSession(), int(API_ID), API_HASH) as client:
        await client.start()
        session = await export_session(client=client)
        return session


async def export_session(client: TelegramClient) -> str:
    # Get the session string
    if client.session is None:
        raise RuntimeError("Error: Client session returned None, is something wrong?")
    session = client.session.save()  # Save the session to a string
    if not session:
        raise RuntimeError("Error: Failed to convert session into a session string")
    return session


async def print_session_string(session: str) -> None:
    print("\n\nSession string generated successfully!")
    print("Copy this session string to your .env file as SESSION_STRING:")
    print("-" * 50, "\n")
    print(session)
    print("\n", "-" * 50)


async def save_session_string(session_file: str, session: str) -> bool:
    # Save to file as backup
    try:
        with open("session_string.txt", "w") as f:
            f.write(session)
    except Exception as e:
        print(f"Error saving session string to file: {e}")
        return False

    print(f"Session string also saved to '{session_file}'")
    print("\n⚠️  Important:")
    print("   - Keep this session string secure and private")
    print("   - Add SESSION_STRING=<your_string> to your .env file")
    print(f"   - Delete '{session_file}' after copying to .env")
    return True


async def main():
    if not verify_secrets():
        return

    session = await authenticate_session()
    await print_session_string(session)
    await save_session_string(session_file, session)


if __name__ == "__main__":
    asyncio.run(main())
