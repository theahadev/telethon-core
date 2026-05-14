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
    table         TEXT NOT NULL          -- full internal table name e.g. "handlers.game.scores"
    last_modified INTEGER NOT NULL
    PRIMARY KEY (handler, table)

── _audit ─────────────────────────────────────────────────────────────────────
Append-only audit log. Written on every mutating operation.

Schema:
    id            INTEGER PRIMARY KEY AUTOINCREMENT
    table         TEXT NOT NULL          -- full internal table name
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
    tuple         → "tuple"    → json.dumps(list(v))
    set           → "set"      → json.dumps(list(v))

    On deserialization, types are fully restored:
        "str"   → str
        "int"   → int
        "float" → float
        "bool"  → bool
        "null"  → None
        "list"  → list
        "dict"  → dict
        "tuple" → tuple
        "set"   → set

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
Falls back to "unknown" if detection fails.

Module name is used to:
    - build the default table name: "handlers.<modulename>"
      if __name__ is already "handlers.game", full table becomes "handlers.game"
      if __name__ is just "game", full table becomes "handlers.game"
    - populate the `module` column in _audit and `modified_by` in global

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ERROR FORMAT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

All errors are returned as a dict (never raised to caller):

    {
        "error_code":   int,        -- see error codes below
        "error_desc":   str,        -- short machine-readable name
        "error_key":    str | None, -- key involved, null if not applicable
        "error_table":  str | None, -- SCOPED table name ("" for default, "scores" for subtable)
                                    -- never the full internal path (handlers.game.scores)
        "error_detail": str | None, -- human-readable sentence e.g.
                                    -- "key 'meow' does not exist in table ''"
        "error_raw":    str | None  -- str(exception) for unexpected errors, null for clean errors
    }

── Error codes ────────────────────────────────────────────────────────────────

    1xx — client errors (caller did something wrong)

        100   invalid key name       key failed sanitization
        101   invalid table name     table name failed sanitization
        102   unsupported type       value type not serializable
        103   key not found          getKey/delKey on nonexistent key
        104   table not found        operation on nonexistent table
        105   operation not permitted e.g. attempted to drop global table

    2xx — system errors (db internals)

        200   db not initialized     _initDatabase() not called yet
        201   sqlite error           generic sqlite failure, detail in error_raw
        202   serialization error    _serialize() failed unexpectedly
        203   deserialization error  _deserialize() failed unexpectedly

── Error examples ─────────────────────────────────────────────────────────────

    key not found:
    {
        "error_code":   103,
        "error_desc":   "key not found",
        "error_key":    "meow",
        "error_table":  "",
        "error_detail": "key 'meow' does not exist in table ''",
        "error_raw":    null
    }

    sqlite failure:
    {
        "error_code":   201,
        "error_desc":   "sqlite error",
        "error_key":    "meow",
        "error_table":  "scores",
        "error_detail": "database operation failed on table 'scores'",
        "error_raw":    "disk I/O error"
    }

    db not initialized:
    {
        "error_code":   200,
        "error_desc":   "db not initialized",
        "error_key":    null,
        "error_table":  null,
        "error_detail": "_initDatabase() has not been called",
        "error_raw":    null
    }

All errors are also logged via loguru at ERROR level before being returned.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PUBLIC API
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

All public functions are async. All return tuples. Never raise to the caller.

table parameter is always the SCOPED subtable name (e.g. "scores"), not the full path.
Omit or pass None for the module's default table.

── Local (module-scoped) ───────────────────────────────────────────────────────

setKey(key, value, table=None)
    Write a key. Creates table if needed.
    Returns:
        (True,  value,      key, scoped_table)
        (False, error_dict, key, scoped_table)

getKey(key, table=None)
    Read a key.
    Returns:
        (True,  value,      key, scoped_table)
        (False, error_dict, key, scoped_table)

delKey(key, table=None)
    Delete a key. Audits the old value.
    Returns:
        (True,  old_value,  key, scoped_table)
        (False, error_dict, key, scoped_table)

listKeys(table=None)
    List all keys in a table.
    Returns:
        (True,  [key, ...],      scoped_table)
        (False, error_dict,      scoped_table)

dropTable(table=None)
    Drop a table entirely. Audits a full dump before dropping.
    Returns:
        (True,  dump_dict,  scoped_table)
        (False, error_dict, scoped_table)

dumpTable(table=None)
    Return all rows with types and timestamps.
    Returns:
        (True, {
            key: {
                "type":          str,
                "value":         <deserialized>,
                "last_modified": int
            }, ...
        }, scoped_table)
        (False, error_dict, scoped_table)

listTables()
    List all tables owned by this module (default + subtables), as scoped names.
    "" = default table, "scores" = subtable
    Returns:
        (True,  ["", "scores", ...])
        (False, error_dict)

── Global ──────────────────────────────────────────────────────────────────────

setGlobal(key, value)
    Returns:
        (True,  value,     key)
        (False, error_dict, key)

getGlobal(key)
    Returns:
        (True,  value,     key)
        (False, error_dict, key)

delGlobal(key)
    Returns:
        (True,  old_value, key)
        (False, error_dict, key)

listGlobal()
    Returns:
        (True,  [key, ...])
        (False, error_dict)

dumpGlobal()
    Same format as dumpTable but includes modified_by per entry.
    Returns:
        (True, {
            key: {
                "type":          str,
                "value":         <deserialized>,
                "last_modified": int,
                "modified_by":   str
            }, ...
        })
        (False, error_dict)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
INTERNAL FUNCTIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

These are not part of the public API. Handlers must never call them directly.

_fetchHandlerName() -> str
    Walks inspect.stack(), skips db.py frames, returns __name__ of first external frame.
    Falls back to "unknown" if detection fails.

_resolveTable(module: str, subtable: str | None) -> str
    Builds full internal table name from module name and optional subtable.
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
    Fully restores tuple and set types.
    Raises ValueError for unknown type tags.

_ensureTable(conn, table: str) -> None
    Creates the table if it doesn't exist (handlers.<x> schema).
    Upserts a row into _handlers with handler name, full table name, current timestamp.

_audit(conn, table, key, type_tag, value_str, action, module) -> None
    Appends a row to _audit. All params are pre-serialized strings.
    key and type_tag may be None (dropTable case).

_initDatabase(db_path: str) -> None
    Called once by main.py before any handlers load.
    Creates all system tables (_handlers, _audit, _metadata, global) if they don't exist.
    Inserts _metadata rows (version, created_at) if not already present.
    Sets the module-level _db_path used by all other functions.
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
    "frozen":  {"type": "tuple", "value": (1, 2, 3),        "last_modified": 1748732007},
    "unique":  {"type": "set",   "value": {1, 2, 3},        "last_modified": 1748732008},
}, "")

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TODO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

- implement all functions above
- _audit log rotation (future, not now)
"""

# implementation goes here
