# Telethon Core

A modular Telegram bot framework built on [Telethon](https://github.com/LonamiWebs/Telethon) with structured logging, environment-based config, and auto-discovery of handlers.

## Features

- **Modular handlers** - drop a `.py` file in `handlers/` and it's automatically loaded
- **Multi-sink logging** - independent log levels for stdout, file, and Telegram channel via [loguru](https://github.com/Delgan/loguru)
- **Environment-based config** - all settings via `.env`, no hardcoded values
- **Graceful lifecycle** — SIGINT/SIGTERM handling for clean shutdowns; `restart()` via `os.execv`
- **Auto command registration** - define commands in `commands.txt`, they're registered with Telegram on startup
- **Docker ready** - includes `Dockerfile` and `docker-compose.yml`

## Requirements

- Python 3.11+
- Telegram API credentials from [my.telegram.org](https://my.telegram.org)
- Bot token from [@BotFather](https://t.me/botfather)

## Quick Start

### Docker (recommended)

```bash
git clone https://github.com/theahadev/telethon-core.git
cd telethon-core
cp .env.example .env
# fill in your credentials in .env
docker compose up -d
```

### Manual

```bash
git clone https://github.com/theahadev/telethon-core.git
cd telethon-core
pip install -r requirements.txt
# or: uv sync
cp .env.example .env
# fill in your credentials in .env
python main.py
```

## Configuration

Copy `.env.example` to `.env` and fill in your values. Required variables are marked below.

### Core

| Variable | Required | Description |
|----------|----------|-------------|
| `API_ID` | ✅ | Telegram API ID from [my.telegram.org](https://my.telegram.org) |
| `API_HASH` | ✅ | Telegram API Hash |
| `BOT_TOKEN` | ✅ | Bot token from [@BotFather](https://t.me/botfather) |
| `DATA_FOLDER` | ✅ | Directory for session file and persistent data |

### Logging

| Variable | Description | Default |
|----------|-------------|---------|
| `LOG_LEVEL_STDOUT` | Console log level | `INFO` |
| `LOG_LEVEL_FILE` | File log level | `INFO` |
| `LOG_FILE_PATH` | Path to log file (enables file logging) | — |
| `LOG_ROTATION` | Log rotation policy (e.g. `500 MB`, `1 week`) | — |
| `LOG_RETENTION` | Log retention policy (e.g. `1 month`) | — |
| `LOG_COMPRESSION` | Compression for rotated logs (`gz`, `zip`, etc.) | — |
| `LOG_CHANNEL` | Telegram channel ID for log forwarding (enables Telegram logging) | — |
| `LOG_LEVEL_TELEGRAM` | Telegram log level | `INFO` |

> **Note:** Errors and above always go to stderr regardless of `LOG_LEVEL_STDOUT`. Telegram logging requires `LOG_CHANNEL` to be set.

## Project Structure

```
telethon-core/
├── main.py              # Entry point — loads config, sets up client, imports handlers
├── core.py              # Shared state, event wrappers, logging setup, lifecycle
├── commands.txt         # Bot commands in COMMAND=Description format
├── requirements.txt     # Python dependencies
├── pyproject.toml       # Project metadata
├── Dockerfile
├── docker-compose.yml
├── .env.example         # Environment variable template
└── handlers/
    ├── __init__.py      # Auto-discovery and loading of handler modules
    ├── start.py         # /start handler
    ├── help.py          # /help handler
    └── addchat.py       # Bot added to chat handler
```

## Writing Handlers

Create any `.py` file in `handlers/` - it's auto-loaded on startup. Register events at module level using the helpers from `core`:

```python
from typing import Any
from loguru import logger
import core

async def my_handler(event: Any) -> None:
    await event.reply("hello!")

core.onMessage(my_handler, pattern=r"^/hello(\s|$)")
```

Available event wrappers: `onMessage`, `onEdit`, `onDelete`, `onRead`, `onCallback`, `onInline`, `onChatAction`, `onUserUpdate`, `onRaw`.

## Bot Commands

Edit `commands.txt` in `COMMAND=Description` format:

```
start=Start the bot
help=Get help
```

Commands are registered with Telegram automatically on startup.

## License

MIT — see [LICENSE](LICENSE).
