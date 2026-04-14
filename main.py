import os
from pathlib import Path

from dotenv import load_dotenv
from loguru import logger
from telethon import TelegramClient

import core

# Load environment variables
load_dotenv()


# Raise a clear error on missing keys
def getEnvVar(key: str) -> str:
    value = os.getenv(key)
    if value is None:
        raise RuntimeError(f"Missing required environment variable: {key}")
    logger.debug(f"Loaded environment variable: {key}")
    return value


# Get optional env variables with defaults
def getEnvVarOptional(key: str, default: str | None = None) -> str | None:
    value = os.getenv(key, default)
    if value:
        logger.debug(f"Loaded optional environment variable: {key}")
    return value


# Telethon stuff
logger.debug("Loading Telegram API credentials...")
api_id = int(getEnvVar("API_ID"))
api_hash = getEnvVar("API_HASH")
bot_token = getEnvVar("BOT_TOKEN")
logger.debug(f"Telegram API ID: {api_id}, API Hash: {api_hash[:10]}...")

# Other env variables
logger.debug("Loading configuration variables...")
data_folder = Path(getEnvVar("DATA_FOLDER")).expanduser().resolve()
logger.debug(f"Data folder path resolved to: {data_folder}")

# Logger level configuration from env vars
log_level_stdout = getEnvVarOptional("LOG_LEVEL_STDOUT")
log_level_file = getEnvVarOptional("LOG_LEVEL_FILE")
log_level_telegram = getEnvVarOptional("LOG_LEVEL_TELEGRAM")

log_channel = getEnvVarOptional("LOG_CHANNEL")
log_file_path = getEnvVarOptional("LOG_FILE_PATH")
log_rotation = getEnvVarOptional("LOG_ROTATION")
log_retention = getEnvVarOptional("LOG_RETENTION")
log_compression = getEnvVarOptional("LOG_COMPRESSION")


# Ensure data folder exists
if not os.path.exists(data_folder):
    logger.info(f"Data folder '{data_folder}' does not exist. Creating it...")
    logger.debug(f"Creating directory: {data_folder}")
    os.makedirs(data_folder, exist_ok=True)
    logger.info(f"Data folder '{data_folder}' created successfully.")
else:
    logger.debug(f"Data folder already exists: {data_folder}")

logger.debug("Initializing TelegramClient...")
core.bot = TelegramClient(f"{data_folder}/bot", api_id, api_hash)
logger.debug(f"TelegramClient initialized with session path: {data_folder}/bot")

core.data = {}

# Populate core.data with logging configuration if provided
logger.debug("Populating logging configuration...")
if log_level_stdout:
    core.data["log_level_stdout"] = log_level_stdout
    logger.debug(f"Set log_level_stdout: {log_level_stdout}")
if log_level_file:
    core.data["log_level_file"] = log_level_file
    logger.debug(f"Set log_level_file: {log_level_file}")
if log_level_telegram:
    core.data["log_level_telegram"] = log_level_telegram
    logger.debug(f"Set log_level_telegram: {log_level_telegram}")
if log_file_path:
    core.data["log_file_path"] = log_file_path
    logger.debug(f"Set log_file_path: {log_file_path}")

# Add log_channel if it's configured
if log_channel:
    core.data["log_channel"] = int(log_channel)
    logger.debug(f"Set log_channel: {log_channel}")

# Add log rotation/retention/compression if configured
if log_rotation:
    core.data["log_rotation"] = log_rotation
    logger.debug(f"Set log_rotation: {log_rotation}")
if log_retention:
    core.data["log_retention"] = log_retention
    logger.debug(f"Set log_retention: {log_retention}")
if log_compression:
    core.data["log_compression"] = log_compression
    logger.debug(f"Set log_compression: {log_compression}")

# Setup logging after core.data is populated
logger.debug("Setting up logging system...")
core.setupLogging()
logger.debug("Logging system setup completed.")

logger.debug("Importing event handlers...")
import handlers  # noqa: E402, F401

logger.debug("Event handlers imported successfully.")

logger.debug("Starting TelegramClient with bot token...")
with core.bot.start(bot_token=bot_token):
    logger.debug("TelegramClient started successfully. Running bot...")
    core.bot.loop.run_until_complete(core.run())
logger.debug("TelegramClient context exited.")
