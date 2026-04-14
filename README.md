# Telethon Core

A modern, modular Telegram bot framework built on [Telethon](https://github.com/LonamiWebs/Telethon) with enterprise-grade logging, configuration management, and auto-discovery of handlers.

## Features

- **Fully Modular Architecture** - Drop Python files in `handlers/` and they're automatically discovered and loaded
- **Enterprise Logging** - Multiple simultaneous log outputs with independent log levels:
  - Console (stdout/stderr)
  - File with rotation, retention, and compression
  - Telegram channel for real-time alerts
- **Flexible Configuration** - Environment-based configuration with sensible defaults
- **Graceful Lifecycle Management** - Automatic signal handling (SIGINT, SIGTERM) for clean shutdowns and restarts
- **Docker Ready** - Includes Dockerfile and docker-compose.yml for containerized deployment
- **Comprehensive Event System** - Built on Telethon's event system with convenient wrapper functions:
  - Message handling (new and edited)
  - Callback queries (inline buttons)
  - Inline queries
  - Chat actions (members joining, title changes, etc.)
  - User updates (typing, online status)
  - Raw Telegram updates

## Requirements

- Python 3.11 or higher
- Telegram API credentials from [my.telegram.org](https://my.telegram.org)
- Telegram Bot Token from [@BotFather](https://t.me/botfather)

## Quick Start

### Using Docker (Recommended)

1. Clone the repository:
```bash
git clone https://github.com/theahadev/telethon-core.git
cd telethon-core
```

2. Create a `.env` file with your credentials:
```env
API_ID=your_api_id
API_HASH=your_api_hash
BOT_TOKEN=your_bot_token
DATA_FOLDER=./data
LOG_LEVEL_STDOUT=INFO
```

3. Build and run:
```bash
docker compose up -d
```

### Manual Installation

1. Clone the repository:
```bash
git clone https://github.com/thehadev/telethon-core.git
cd telethon-core
```

2. Install dependencies:
```bash
pip install -r requirements.txt
# or use uv for faster installations:
uv sync
```

3. Create a `.env` file (see [Configuration](#configuration))

4. Run the bot:
```bash
python3 main.py
```

## Configuration

Create a `.env` file in the root directory. **Bold** items are required.

### Core Settings

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| **`API_ID`** | Telegram API ID from [my.telegram.org](https://my.telegram.org) | — | `12345678` |
| **`API_HASH`** | Telegram API Hash from [my.telegram.org](https://my.telegram.org) | — | `abcd1234...` |
| **`BOT_TOKEN`** | Bot token from [@BotFather](https://t.me/botfather) | — | `123:ABC...` |
| **`DATA_FOLDER`** | Directory for storing bot session and data | — | `./data` |

### Logging Configuration

#### Console Logging

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `LOG_LEVEL_STDOUT` | Logging level for console output | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |

#### File Logging

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `LOG_LEVEL_FILE` | Logging level for file output | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `LOG_FILE_PATH` | Path to log file (enables file logging) | — | `/var/log/bot.log` or `./logs/bot.log` |
| `LOG_ROTATION` | When to rotate log file | — | `500 MB`, `00:00`, `1 week`, etc. |
| `LOG_RETENTION` | How long to keep rotated logs | — | `1 month`, `90 days`, etc. |
| `LOG_COMPRESSION` | Compression format for rotated logs | — | `zip`, `gz`, `bz2`, `xz` |

#### Telegram Logging

Send ERROR and above logs to a Telegram channel in real-time:

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `LOG_CHANNEL` | Channel ID for logging (enables Telegram logging) | — | `-100123456789` |
| `LOG_LEVEL_TELEGRAM` | Minimum log level to send to Telegram | `INFO` | `WARNING`, `ERROR`, `CRITICAL` |

Note: Get channel ID by forwarding a message from the channel to [@userinfobot](https://t.me/userinfobot).

## Project Structure

```
telethon-core/
├── main.py                      # Bot entry point and initialization
├── core.py                      # Shared bot state & event registration helpers
├── requirements.txt             # Python dependencies
├── pyproject.toml              # Project metadata and dependencies
├── Dockerfile                  # Container image definition
├── docker-compose.yml          # Docker compose configuration
├── commands.txt                # Bot commands for auto-registering
├── .env                        # Environment variables (not in git)
├── .gitignore                  # Git ignore rules
├── LICENSE                     # MIT License
├── data/                       # Persistent storage
│   └── bot.session             # Telethon session file (auto-created)
└── handlers/                   # Event handlers (auto-loaded)
    ├── __init__.py            # Handler discovery and loading
    ├── start.py               # /start command handler
    ├── help.py                # /help command handler
    └── addchat.py             # Add to chat handler
```

## Creating Custom Handlers

Handlers are automatically discovered and loaded from the `handlers/` directory.

_fixme: Add example handler code snippets and documentation_

### Bot Commands

Define commands in `commands.txt` with the format `COMMAND=Description`:

```
start=Start the bot
help=Show help information
hello=Say hello
restart=Restart the bot
```

These commands are automatically registered with Telegram when the bot starts.

### Check Telethon Documentation

For advanced Telethon features, see the [Telethon Documentation](https://docs.telethon.dev/).

## Dependencies

- **telethon** (1.36.0+) - Telegram client library
- **loguru** (0.7.3+) - Advanced logging
- **python-dotenv** (1.0.1+) - Environment variable management

See `requirements.txt` or `pyproject.toml` for exact versions.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Additional Resources

- [Telethon GitHub](https://github.com/LonamiWebs/Telethon)
- [Telegram Bot API](https://core.telegram.org/bots)
- [Telegram Client API](https://core.telegram.org/methods)
- [python-dotenv](https://github.com/theskumar/python-dotenv)
- [loguru](https://github.com/Delgan/loguru)
