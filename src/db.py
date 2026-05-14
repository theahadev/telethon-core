# TODO:
# implement sql database
# specs:
#
# async
#
# database path passed from core.config with DB_PATH
#
# type conversions should be handled, like if i write int, i should get int back, not string
# maybe we can do with serialization and deserialization of data to preserve types
#
# sanitization of every key name and table name to prevent sql injection
#
# each module gets a default table like "handlers.game"
#
# global table for shared data between modules
#
# the ability to create subtables (also sanitized) like "handlers.game.scores"
#
#
# available methods:
#
#
# key operations (local):
#
# setKey(key, value, table=None): return True, value, key, table (if failed, return False, error, key, table)
# getKey(key, table=None): return True, value, key, table (if failed, return False, error, key, table)
# delKey(key, table=None): return True, value (last value before deleting) key, table (if failed, return False, error, key, table)
# listKeys(table=None): return True, list of keys, table (if failed, return False, error, table)
#
# the table parameter is optional, if not provided, it defaults to the module's default table
#
# key operations (global):
# setGlobal(key, value): return True, value, key (if failed, return False, error, key)
# getGlobal(key): return True, value, key (if failed, return False, error, key)
# delGlobal(key): return True, value (last value before deleting) key (if failed, return False, error, key)
# listGlobal(): return True, list of keys (if failed, return False, error)
#
# table operations (local):
# dropTable(table=None): return True, list of keys before dropping, table (if failed, return False, error, table)
# dumpTable(table=None): return True, dict of key-value pairs, table (if failed, return False, error, table)
# listTables(): return True, list of tables (if failed, return False, error)
#
# table operations (global):
# theres NO drop operation for global table!!
# dumpGlobal(): return True, dict of key-value pairs (if failed, return False, error)
#
#
# notes:
# modules will never know about each other, so they will never access each other's tables directly
# they will only access the global table for shared data
# the global table will be a single table with key-value pairs, no subtables allowed in global table
# the handlers will know subtables only as "subtablename", but in the database, they will be stored as
# "handlers.handlername.subtitlename" to prevent conflicts between modules
# a table called "handlers" will be used to store logs for module names and table modifications
# like, if a module creates a table called "handlers.game.scores", it will log creation date-time, and keep a field for last access date
# same logs will be done for "handlers.modulename" too
# the global table will log more granularly, like if a key is set, it will log the key name, value
# and date-time of modification
# log rotation will be implemented later, not at this stage.
#
#
# table formats and examples:
#
#
# handlers table:
# table | key | last_modified
# handlers.game.scores | user_1234 | 1778732000
#
# global table:
# key | value | last_modified | modified_by
# score_multiplier | 2 | 1778732000 | game
#
# handlers.modulename table:
# key | value | last_modified
# some_config | 1234 | 1778732000
#
# handlers.modulename.subtablename table:
# key | value | last_modified
# user_1234 | 5700 | 1778732000
#
# first create a roadmap, after verifying it with me and getting clear instruction to continue,
# implement it according to the roadmap and my instructions at that moment.
