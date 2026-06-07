# TODO

This is a list of things that i am planning to add to the project in the future. This is not a complete list and is fully dependent on my mood to keep this list updated or to follow this list. Feel free to send a PR if you want to add something to this list or if you want to implement something from this list.

## Immediate

- [ ] Implement validate_config() in config.py
- [ ] Update the bot.start() call in lifecycle.py

## Database

- [ ] Implement it from DATABASE.md
- [ ] Add \_audit log rotation mechanism
- [ ] Add sub tables for global table
- [ ] Add proper names for global and handler root tables
- [ ] Add logging level config for database
- [ ] Think about storing session string in database for portability and evaluate security implications
- [ ] Add database backup and restore functionality
- [ ] Add database migration system for future updates

## Docs

- [ ] Add docstrings for all functions and classes
- [ ] Add usage examples for all modules
- [ ] Add basic and advanced example env
- [ ] Add a getting started guide for new users
- [ ] Add a contributing guide

## Docker

- [ ] Fix dockerfile and update to run with uv
- [ ] Update docker compose file
- [ ] Add better documentation for running with docker
- [ ] Think about adding a docker image to docker hub for easier usage

## Development

- [ ] Better module development guides
- [ ] Add more example modules for different use cases and showcase different features

## Handlers

- [ ] Think about a core function to install module dependencies
- [x] Add a config for trigger character and think about enforcement
- [x] Think about seperating function registeration from onMessage() function and encourage the 1. one
- [ ] on the on_command function, fix pm behavior
