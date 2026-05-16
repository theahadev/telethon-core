# TODO for database
Database was overwhelming the TODO.md file, so i decided to move it to a separate file.

## Database

### Core Infrastructure
- [ ] Initialize database with `_initDatabase(db_path)`
- [ ] Create _metadata table with schema (key TEXT PRIMARY KEY, value TEXT NOT NULL)
- [ ] Populate _metadata with version="1" and created_at timestamp
- [ ] Create global table with schema (key TEXT PRIMARY KEY, type TEXT NOT NULL, value TEXT, last_modified INTEGER NOT NULL, modified_by TEXT NOT NULL)
- [ ] Create _handlers registry table with schema (handler TEXT NOT NULL, table TEXT NOT NULL, last_modified INTEGER NOT NULL, PRIMARY KEY (handler, table))
- [ ] Create _audit log table with schema (id INTEGER PRIMARY KEY AUTOINCREMENT, table TEXT NOT NULL, key TEXT, type TEXT, value TEXT, action TEXT NOT NULL, module TEXT NOT NULL, timestamp INTEGER NOT NULL)

### Handler/Module Tables
- [ ] Dynamically create handler tables named `handlers.<modulename>` with schema (key TEXT PRIMARY KEY, type TEXT NOT NULL, value TEXT, last_modified INTEGER NOT NULL)
- [ ] Support subtables with naming pattern `handlers.<modulename>.<subtable>`
- [ ] Implement `_ensureTable(conn, table)` to create tables on demand
- [ ] Register tables in _handlers registry

### Module/Handler Detection
- [ ] Implement `_fetchHandlerName()` using inspect.stack() to detect caller
- [ ] Skip db.py frames and return __name__ of first external caller
- [ ] Handle module names with/without "handlers." prefix (e.g., "game" → "handlers.game")
- [ ] Fallback to "unknown" if detection fails

### Name Sanitization & Validation
- [ ] Implement `_sanitize(name)` to validate against `^[a-zA-Z0-9_]+$`
- [ ] Validate all key names against sanitization rules
- [ ] Validate all table name components (split by dots) against sanitization rules
- [ ] Raise ValueError on invalid input
- [ ] Apply sanitization to all public-facing inputs

### Serialization
- [ ] Implement `_serialize(value)` to convert Python types to (type_tag, value_str)
  - [ ] Handle str → ("str", raw string)
  - [ ] Handle int → ("int", str(n))
  - [ ] Handle float → ("float", str(n))
  - [ ] Handle bool → ("bool", "true"|"false")
  - [ ] Handle None → ("null", "")
  - [ ] Handle list → ("list", json.dumps(v))
  - [ ] Handle dict → ("dict", json.dumps(v))
  - [ ] Handle tuple → ("tuple", json.dumps(list(v)))
  - [ ] Handle set → ("set", json.dumps(list(v)))
- [ ] Raise TypeError for unsupported types

### Deserialization
- [ ] Implement `_deserialize(type_tag, value_str)` to restore Python values
  - [ ] Restore "str" → str
  - [ ] Restore "int" → int
  - [ ] Restore "float" → float
  - [ ] Restore "bool" → bool (parse "true"|"false")
  - [ ] Restore "null" → None
  - [ ] Restore "list" → list (json.loads)
  - [ ] Restore "dict" → dict (json.loads)
  - [ ] Restore "tuple" → tuple (json.loads then convert)
  - [ ] Restore "set" → set (json.loads then convert)
- [ ] Raise ValueError for unknown type tags

### Local (Module-Scoped) Functions
- [ ] Implement `setKey(key, value, table=None)` to write a key
  - [ ] Create table if needed via _ensureTable
  - [ ] Validate key name with _sanitize
  - [ ] Serialize value with _serialize
  - [ ] Insert/update row with current timestamp
  - [ ] Audit the operation
  - [ ] Return (True, value, key, scoped_table) on success
  - [ ] Return (False, error_dict, key, scoped_table) on failure
- [ ] Implement `getKey(key, table=None)` to read a key
  - [ ] Validate key name with _sanitize
  - [ ] Return (True, deserialized_value, key, scoped_table) on success
  - [ ] Return (False, error_dict, key, scoped_table) on key not found (error code 103)
  - [ ] Return error if table doesn't exist (error code 104)
- [ ] Implement `delKey(key, table=None)` to delete a key
  - [ ] Validate key name with _sanitize
  - [ ] Fetch and audit old value before deletion
  - [ ] Return (True, old_value, key, scoped_table) on success
  - [ ] Return (False, error_dict, key, scoped_table) on key not found (error code 103)
- [ ] Implement `listKeys(table=None)` to list all keys
  - [ ] Return (True, [key, ...], scoped_table) on success
  - [ ] Return (False, error_dict, scoped_table) if table not found
- [ ] Implement `dumpTable(table=None)` to return all rows with metadata
  - [ ] Return dict with keys mapping to {"type": str, "value": deserialized, "last_modified": int}
  - [ ] Return (True, dump_dict, scoped_table) on success
  - [ ] Return (False, error_dict, scoped_table) if table not found
- [ ] Implement `dropTable(table=None)` to drop a table entirely
  - [ ] Prevent dropping default table of global (error code 105)
  - [ ] Audit full dumpTable output before dropping
  - [ ] Return (True, dump_dict, scoped_table) on success
  - [ ] Return (False, error_dict, scoped_table) on failure
- [ ] Implement `listTables()` to list all tables owned by module
  - [ ] Return scoped names ("" for default, "scores" for subtables)
  - [ ] Return (True, [scoped_name, ...]) on success
  - [ ] Return (False, error_dict) on failure

### Global Functions
- [ ] Implement `setGlobal(key, value)` to write global key
  - [ ] Validate key name with _sanitize
  - [ ] Serialize value
  - [ ] Populate modified_by with detected module name
  - [ ] Return (True, value, key) on success
  - [ ] Return (False, error_dict, key) on failure
- [ ] Implement `getGlobal(key)` to read global key
  - [ ] Return (True, deserialized_value, key) on success
  - [ ] Return (False, error_dict, key) on key not found (error code 103)
- [ ] Implement `delGlobal(key)` to delete global key
  - [ ] Fetch and audit old value before deletion
  - [ ] Return (True, old_value, key) on success
  - [ ] Return (False, error_dict, key) on key not found (error code 103)
- [ ] Implement `listGlobal()` to list all global keys
  - [ ] Return (True, [key, ...]) on success
  - [ ] Return (False, error_dict) on failure
- [ ] Implement `dumpGlobal()` to return all global rows with metadata
  - [ ] Return dict with keys mapping to {"type": str, "value": deserialized, "last_modified": int, "modified_by": str}
  - [ ] Return (True, dump_dict) on success
  - [ ] Return (False, error_dict) on failure

### Audit Logging
- [ ] Implement `_audit(conn, table, key, type_tag, value_str, action, module)` function
  - [ ] Append row to _audit with all parameters
  - [ ] Handle key and type_tag as None for dropTable case
  - [ ] Support actions: "set", "del", "drop", "set_global", "del_global"
  - [ ] Store full dumpTable output as value for "drop" action
  - [ ] Record current unix timestamp
- [ ] Audit every mutating operation (set, del, drop, setGlobal, delGlobal)

### Error Handling
- [ ] Implement error dict structure with fields: error_code, error_desc, error_key, error_table, error_detail, error_raw
- [ ] Client errors (1xx):
  - [ ] Error 100: invalid key name (sanitization failure)
  - [ ] Error 101: invalid table name (sanitization failure)
  - [ ] Error 102: unsupported type (serialization failure)
  - [ ] Error 103: key not found (getKey/delKey on nonexistent)
  - [ ] Error 104: table not found (operation on nonexistent table)
  - [ ] Error 105: operation not permitted (e.g., drop global)
- [ ] System errors (2xx):
  - [ ] Error 200: db not initialized (_initDatabase not called)
  - [ ] Error 201: sqlite error (generic failure with error_raw)
  - [ ] Error 202: serialization error (_serialize failed)
  - [ ] Error 203: deserialization error (_deserialize failed)
- [ ] Log all errors via loguru at ERROR level before returning
- [ ] Never raise exceptions to caller

### Return Value Contracts
- [ ] All public functions are async
- [ ] All functions return tuples
- [ ] Success returns True as first element
- [ ] Failure returns False as first element followed by error_dict
- [ ] Local functions include scoped_table in return tuple
- [ ] Global functions do not include table in return tuple

### Utilities
- [ ] Implement `_resolveTable(module, subtable)` to build full internal table name
  - [ ] Handle module with/without "handlers." prefix
  - [ ] Handle None subtable (use module's default table)
  - [ ] Examples: ("handlers.game", None) → "handlers.game", ("game", "scores") → "handlers.game.scores"
