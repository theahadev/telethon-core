"""
db.py — async SQLite key-value store for telethon-core handlers.

Usage:
    import db
    await db.setKey("meow", True)
    await db.setKey("woof", False, "dogs")
    await db.setGlobal("pets", ["cats", "dogs"])

db is initialized by main.py via _initDatabase(core.config["db_path"]) before handlers load.
Handlers never instantiate anything — just import and call.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DATABASE LAYOUT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

All tables live in a single SQLite file at core.config["db_path"].

── Module tables ──────────────────────────────────────────────────────────────
Named as: handlers.<modulename>          e.g. handlers.game
Subtables: handlers.<modulename>.<sub>   e.g. handlers.game.scores

Schema:
    key           TEXT PRIMARY KEY
    type          TEXT NOT NULL          -- one of: str int float bool null list dict tuple set
    value         TEXT                   -- serialized (see SERIALIZATION)
    last_modified INTEGER NOT NULL       -- unix timestamp

── global ─────────────────────────────────────────────────────────────────────
Shared KV store. Any module can read/write. No subtables.

Schema:
    key           TEXT PRIMARY KEY
    type          TEXT NOT NULL
    value         TEXT
    last_modified INTEGER NOT NULL
    modified_by   TEXT NOT NULL          -- module name that last touched it

── _handlers ──────────────────────────────────────────────────────────────────
Registry of all module tables and subtables. Written by _ensureTable().

Schema:
    handler       TEXT NOT NULL          -- e.g. "game"
    table         TEXT NOT NULL          -- full table name e.g. "handlers.game.scores"
    last_modified INTEGER NOT NULL
    PRIMARY KEY (handler, table)

── _audit ─────────────────────────────────────────────────────────────────────
Append-only audit log. Written on every mutating operation.

Schema:
    id            INTEGER PRIMARY KEY AUTOINCREMENT
    table         TEXT NOT NULL          -- full table name
    key           TEXT                   -- NULL for dropTable
    type          TEXT                   -- type of value BEFORE action (NULL for dropTable row)
    value         TEXT                   -- value BEFORE action; for dropTable: full dumpTable output (json)
    action        TEXT NOT NULL          -- "set" | "del" | "drop" | "set_global" | "del_global"
    module        TEXT NOT NULL          -- handler that triggered it
    timestamp     INTEGER NOT NULL       -- unix timestamp

    dropTable audit row:
        key   = NULL
        type  = "dict"
        value = full serialized dumpTable output (same format as dumpTable return value, json-encoded)
        action = "drop"

── _metadata ──────────────────────────────────────────────────────────────────
Created once on _initDatabase(). Never mutated by handlers.

Schema:
    key           TEXT PRIMARY KEY
    value         TEXT NOT NULL

Pre-populated rows:
    version       "1"
    created_at    "<unix timestamp>"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SERIALIZATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

type column holds a string tag. value column holds the serialized value as TEXT.

    Python type   → type tag   → value column
    ───────────────────────────────────────────
    str           → "str"      → raw string, no quotes
    int           → "int"      → str(n)
    float         → "float"    → str(n)
    bool          → "bool"     → "true" | "false"
    None          → "null"     → "" (empty string)
    list          → "list"     → json.dumps(v)
    dict          → "dict"     → json.dumps(v)
    tuple         → "tuple"    → json.dumps(list(v))   # coerced to list on deserialize
    set           → "set"      → json.dumps(list(v))   # coerced to list on deserialize

    tuple and set are stored with their own type tags so round-trip is lossless
    if the caller cares (they probably don't, but the info is preserved).

    On deserialization:
        tuple → returns list  (immutability is caller's problem)
        set   → returns list

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SANITIZATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

_sanitize(name) validates any key or table name component against:
    ^[a-zA-Z0-9_]+$

Full table names use dots as separators and are validated per-segment.
Raises ValueError on invalid input. Called on every public-facing input.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MODULE / HANDLER DETECTION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

_fetchHandlerName() walks the call stack using the `inspect` module.
It skips frames inside db.py itself and returns the __name__ of the first
external caller. e.g. if handlers/game.py calls setKey(), returns "handlers.game".

Module name is used to:
    - build the default table name: "handlers.<modulename>"  (only the last segment is used
      if __name__ is already "handlers.game" — full name becomes "handlers.game")
    - populate the `module` column in _audit and `modified_by` in global

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PUBLIC API
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

All public functions are async. All return tuples. Never raise to the caller.

── Local (module-scoped) ───────────────────────────────────────────────────────

setKey(key, value, table=None)
    Write a key. Creates table if needed.
    table: optional subtable name (just the short name e.g. "scores", NOT the full path)
    Returns:
        (True,  value,      key, full_table)
        (False, error_str,  key, full_table)

getKey(key, table=None)
    Read a key.
    Returns:
        (True,  value,      key, full_table)
        (False, error_str,  key, full_table)   -- includes "key not found" case

delKey(key, table=None)
    Delete a key. Audits the old value.
    Returns:
        (True,  old_value,  key, full_table)
        (False, error_str,  key, full_table)

listKeys(table=None)
    List all keys in a table.
    Returns:
        (True,  [key, ...],      full_table)
        (False, error_str,       full_table)

dropTable(table=None)
    Drop a table entirely. Audits a full dump before dropping.
    Returns:
        (True,  dump_dict,  full_table)     -- dump_dict same format as dumpTable
        (False, error_str,  full_table)

dumpTable(table=None)
    Return all rows with types and timestamps.
    Returns:
        (True,  {
            key: {
                "type":          str,
                "value":         <deserialized>,
                "last_modified": int
            }, ...
        }, full_table)
        (False, error_str, full_table)

listTables()
    List all tables owned by this module (default + all subtables).
    Returns:
        (True,  [full_table_name, ...])
        (False, error_str)

── Global ──────────────────────────────────────────────────────────────────────

setGlobal(key, value)
    Returns:
        (True,  value,     key)
        (False, error_str, key)

getGlobal(key)
    Returns:
        (True,  value,     key)
        (False, error_str, key)

delGlobal(key)
    Returns:
        (True,  old_value, key)
        (False, error_str, key)

listGlobal()
    Returns:
        (True,  [key, ...])
        (False, error_str)

dumpGlobal()
    Same format as dumpTable but includes modified_by field per entry:
    Returns:
        (True,  {
            key: {
                "type":          str,
                "value":         <deserialized>,
                "last_modified": int,
                "modified_by":   str
            }, ...
        })
        (False, error_str)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
INTERNAL FUNCTIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

These are not part of the public API. Handlers must never call them directly.

_fetchHandlerName() -> str
    Walks inspect.stack(), skips db.py frames, returns __name__ of first external frame.
    Falls back to "unknown" if detection fails.

_resolveTable(module: str, subtable: str | None) -> str
    Builds full table name from module name and optional subtable.
    Examples:
        ("handlers.game", None)       -> "handlers.game"
        ("handlers.game", "scores")   -> "handlers.game.scores"
        ("game", None)                -> "handlers.game"
        ("game", "scores")            -> "handlers.game.scores"
    Calls _sanitize() on each segment.

_sanitize(name: str) -> str
    Validates a single name segment against ^[a-zA-Z0-9_]+$.
    Raises ValueError if invalid.
    Returns name unchanged if valid.

_serialize(value) -> tuple[str, str]
    Converts a Python value to (type_tag, value_str) for storage.
    Raises TypeError for unsupported types.

_deserialize(type_tag: str, value_str: str) -> any
    Converts (type_tag, value_str) back to Python value.
    Raises ValueError for unknown type tags.

_ensureTable(conn, table: str) -> None
    Creates the table if it doesn't exist (handlers.<x> schema).
    Upserts a row into _handlers with handler name, full table name, and current timestamp.

_audit(conn, table, key, type_tag, value_str, action, module) -> None
    Appends a row to _audit. All params are pre-serialized strings.
    key and type_tag may be None (dropTable case).

_initDatabase(db_path: str) -> None
    Called once by main.py before any handlers load.
    Creates all system tables (_handlers, _audit, _metadata, global) if they don't exist.
    Inserts _metadata rows (version, created_at) if not already present.
    Sets the module-level `_db_path` used by all other functions.
    Must be called before any public function is used.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DUMP FORMAT EXAMPLE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

(True, {
    "cat":     {"type": "str",   "value": "meowmeow",      "last_modified": 1748732000},
    "count":   {"type": "int",   "value": 42,               "last_modified": 1748732001},
    "flag":    {"type": "bool",  "value": True,             "last_modified": 1748732002},
    "tags":    {"type": "list",  "value": ["a", "b", "c"], "last_modified": 1748732003},
    "cfg":     {"type": "dict",  "value": {"x": 1},         "last_modified": 1748732004},
    "score":   {"type": "float", "value": 3.14,             "last_modified": 1748732005},
    "nothing": {"type": "null",  "value": None,             "last_modified": 1748732006},
    "frozen":  {"type": "tuple", "value": [1, 2, 3],        "last_modified": 1748732007},
    "unique":  {"type": "set",   "value": [1, 2, 3],        "last_modified": 1748732008},
}, "handlers.game")

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TODO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

- implement all functions above
- _audit log rotation (future, not now)
"""

# implementation goes here
