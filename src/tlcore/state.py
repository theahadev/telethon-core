# state.py
#
# Global state management, storing secrets, configuration values and client object.

from telethon import TelegramClient

api_id: str | None = None
api_hash: str | None = None
session_string: str | None = None

client: TelegramClient | None = None
config: dict = {}
