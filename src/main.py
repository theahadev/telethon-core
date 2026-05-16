import os
from pathlib import Path

from dotenv import load_dotenv
from loguru import logger
from telethon import TelegramClient

import core


# Raise a clear error on missing keys
def get_env_var(key: str) -> str:
    value = os.getenv(key)
    if value is None:
        raise RuntimeError(f"Missing required environment variable: {key}")
    logger.debug(f"Loaded environment variable: {key}")
    return value


# Get optional env variables with defaults
def get_env_var_optional(key: str, default: str) -> str:
    value = os.getenv(key)
    if value is None:
        logger.debug(f"Environment variable '{key}' not set. Using default: {default}")
        return default
    logger.debug(f"Loaded optional environment variable: {key}")
    return value


# Set globals in an ugly way
api_id: int = 0
api_hash: str = "NONE"
bot_token: str = "NONE"
session_string: str = "NONE"

client_type: str = "bot"
session_name: str = "bot"

data_folder: str = "data"
db_path: str = "database.db"


# Load telethon API config
def load_secrets():
    global api_id, api_hash, bot_token, session_string, session_name
    logger.debug("Loading Telegram API credentials...")
    api_id = int(get_env_var("API_ID"))
    api_hash = get_env_var("API_HASH")
    bot_token = get_env_var_optional("BOT_TOKEN", bot_token)
    session_string = get_env_var_optional("SESSION_STRING", session_string)
    logger.debug(f"Telegram API ID: {api_id}, API Hash: {api_hash[:10]}...")

    session_name = get_env_var_optional("SESSION_NAME", session_name)
    logger.debug(f"Client type: {client_type}")

    if bot_token == "NONE" and session_string == "NONE":
        raise ValueError("Either BOT_TOKEN or SESSION_STRING must be provided")


# Load data folder path and resolve full paths
def load_resolve_paths():
    global data_folder, db_path
    # Load data folder path
    logger.debug("Loading data folder path...")
    data_folder = str(
        Path(get_env_var_optional("DATA_FOLDER", data_folder)).expanduser().resolve()
    )
    logger.debug(f"Data folder path resolved to: {data_folder}")

    # Resolve database path
    db_name = get_env_var_optional("DB_NAME", db_path)
    db_path = str(
        Path(get_env_var_optional("DB_PATH", data_folder)).expanduser().resolve()
        / db_name
    )
    logger.debug(f"Database path resolved to: {db_path}")


# Ensure data folder exists
def ensure_path():
    if not os.path.exists(data_folder):
        logger.debug(f"Data folder '{data_folder}' does not exist. Creating it...")
        logger.debug(f"Creating directory: {data_folder}")
        os.makedirs(data_folder, exist_ok=True)
        logger.info(f"Data folder '{data_folder}' created successfully.")
    else:
        logger.debug(f"Data folder already exists: {data_folder}")


def init_tg_client():
    global api_id, api_hash, session_string
    logger.debug("Initializing TelegramClient...")
    if session_string == "NONE":
        core.bot = TelegramClient(f"{data_folder}/{session_name}", api_id, api_hash)
        logger.debug(
            f"TelegramClient initialized on path: {data_folder}/{session_name}"
        )
    elif session_string != "NONE":
        from telethon.sessions import StringSession

        core.bot = TelegramClient(StringSession(session_string), api_id, api_hash)
        logger.debug("TelegramClient initialized with session string")
    # Immediately clear the variables from memory after init
    api_id, api_hash, session_string = 0, "NONE", "NONE"


def setup_config():
    core.config = {}

    # Populate core.config with logging configuration
    logger.debug("Populating logging configuration...")
    core.config["log_level_stdout"] = get_env_var_optional("LOG_LEVEL_STDOUT", "INFO")

    core.config["log_level_telegram"] = get_env_var_optional(
        "LOG_LEVEL_TELEGRAM", "INFO"
    )
    core.config["log_channel"] = get_env_var_optional("LOG_CHANNEL", "NONE")

    core.config["log_level_file"] = get_env_var_optional("LOG_LEVEL_FILE", "NONE")
    core.config["log_file_path"] = get_env_var_optional("LOG_FILE_PATH", "NONE")

    core.config["log_rotation"] = get_env_var_optional("LOG_ROTATION", "NONE")
    core.config["log_retention"] = get_env_var_optional("LOG_RETENTION", "NONE")
    core.config["log_compression"] = get_env_var_optional("LOG_COMPRESSION", "NONE")

    core.config["trigger_char"] = get_env_var_optional("TRIGGER_CHAR", "/")

    core.config["client_type"] = get_env_var_optional("CLIENT_TYPE", client_type)
    if core.config["client_type"] not in ("bot", "user"):
        raise ValueError(
            f"CLIENT_TYPE must be 'bot' or 'user', got '{core.config['client_type']}'"
        )


def setup_logging():
    logger.debug("Setting up logging system...")
    core.config["log_stdout"] = core._setup_stdout_log()
    core.config["log_file"] = core._setup_file_log()
    # Telegram logging is done after client is started, so we set it up in the start function
    logger.debug("Logging system setup completed.")


def start_loop():
    global bot_token
    global session_string
    if bot_token != "NONE":
        logger.debug("Starting TelegramClient with bot token...")
        with core.bot.start(bot_token=bot_token):
            # Clear bot token from memory
            bot_token = None  # ty: ignore[invalid-assignment]
            logger.debug("TelegramClient started successfully. Running bot...")
            core.bot.loop.run_until_complete(core.start())
    else:  # we already cleared session_string from memory, it's not trustable anymore
        logger.debug("Starting TelegramClient with session string...")
        with core.bot.start():
            logger.debug("TelegramClient started successfully. Running bot...")
            core.bot.loop.run_until_complete(core.start())
    logger.debug("TelegramClient context exited.")


if __name__ == "__main__":
    logger.remove()  # Nuke default logger for broken format
    load_dotenv()
    setup_config()
    setup_logging()
    load_resolve_paths()
    ensure_path()
    load_secrets()
    init_tg_client()
    start_loop()
