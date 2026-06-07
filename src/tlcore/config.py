# config.py
#
# Secrets and configuration management, environment variable loading, client initialization.
#
# load_secrets(): Load secrets from .env file and store them in state variables.
# validate_secrets(): Validate the loaded secrets, ensuring required values are present and correctly formatted.
# load_config(): Load configuration from config.toml file and store it in state.config variable.
# validate_config(): Validate the loaded configuration, ensuring required values are present and correctly formatted.
# init_client(): Initialize the TelegramClient using the loaded secrets, and store the client object in state.client variable.

import os
import tomllib

from dotenv import load_dotenv
from loguru import logger
from telethon import TelegramClient

from . import state

#######################################
# Secrets management
#######################################


def load_secrets(path: str = ".env") -> None:
    """Load secrets from .env file."""
    try:
        load_dotenv(path)
    except FileNotFoundError:
        logger.error(f".env file not found at '{path}'.")
        raise FileNotFoundError(
            f".env file not found at '{path}'. Please create one with the required secrets."
        )

    # load variables
    state.api_id = os.getenv("API_ID")
    state.api_hash = os.getenv("API_HASH")
    state.session_string = os.getenv("SESSION_STRING")

    if os.getenv("BOT_TOKEN"):
        print("WARNING: BOT_TOKEN is set. Are you sure your configuration is right?")


def validate_secrets() -> None:
    logger.debug(
        f"API_ID: {state.api_id if state.api_id else '<not set>'},"
        f"API_HASH: {state.api_hash[:10] if state.api_hash else '<not set>'}..."
    )

    # Validate api_id and api_hash, if either is missing, use default values and log a warning
    if state.api_id is None or state.api_hash is None:
        if state.api_id is None and state.api_hash is None:
            logger.info("API_ID and API_HASH are not set. Using the default values.")
        elif state.api_id is None:
            logger.warning(
                "API_ID is not set, despite API_HASH being set. Using the default values."
            )
        elif state.api_hash is None:
            logger.warning(
                "API_HASH is not set, despite API_ID being set. Using the default values."
            )
        state.api_id = "5"  # Using a string since its not an int yet
        state.api_hash = "1c5c96d5edd401b1ed40db3fb5633e2d"

    # Validate that api_id is an integer
    try:
        int(state.api_id)
    except (ValueError, TypeError):
        raise ValueError("API_ID must be set to a valid integer in your .env file")

    # Validate that session_string is provided
    logger.debug(f" SESSION_STRING: {'set' if state.session_string else 'not set'}")

    if not state.session_string:
        if os.getenv("BOT_TOKEN"):
            raise ValueError(
                "BOT_TOKEN is set but SESSION_STRING is not set. Please generate a session string instead."
            )
        else:
            raise ValueError("SESSION_STRING is not set. Please provide one.")


#######################################
# Configuration management
#######################################


def load_config(path: str = "config.toml") -> None:
    """Load configuration from config.toml file."""
    if not path:
        logger.info("No configuration file path provided. Skipping config loading.")
        return
    try:
        with open(path, "rb") as f:
            state.config = tomllib.load(f)
    except FileNotFoundError:
        logger.warning(f"Configuration file '{path}' not found. Using empty config.")
        state.config = {}


def validate_config() -> None:
    """Validate the loaded configuration."""
    # Will be updated as the config vars start to take shape
    logger.warning("Stub validate_config() called.")
    return


#######################################
# Client management
#######################################


def init_client() -> None:
    """Initialize the TelegramClient using the loaded secrets."""
    logger.debug("Initializing TelegramClient...")

    # we already validated this in validate_secrets(), so we can trust that
    # api_id and api_hash are set to valid values
    assert state.api_id, "api_id not loaded, call load_secrets() first"
    assert state.api_hash, "api_hash not loaded, call load_secrets() first"

    if state.session_string:
        logger.debug("Initializing TelegramClient with session string...")
        # Lazy import to save a few kb ram when not using session strings
        from telethon.sessions import StringSession

        state.client = TelegramClient(
            StringSession(state.session_string), int(state.api_id), state.api_hash
        )

    # Clear secrets from memory immediately after use
    state.api_id, state.api_hash, state.session_string = (
        None,
        None,
        None,
    )
