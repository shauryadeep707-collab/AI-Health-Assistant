"""
Database abstraction layer for AI Health Assistant.
WHY this module exists: routes and services write SQL with ? placeholders and call
fetch_one / fetch_all / insert. This module transparently handles SQLite, PostgreSQL,
and Oracle differences so the rest of the code NEVER changes.

Key design decisions:
- ? placeholders are converted to %s (Postgres) or :1,:2... (Oracle) automatically
- All results are returned as plain dicts (not Row objects) for JSON serialisation
- Connections are managed per-request in Flask (stored in g)
- PostgreSQL uses a connection pool for efficiency
"""

import os
import re
import sqlite3
import threading
from contextlib import contextmanager

from backend.config import config

# --- Optional imports (don't fail if not installed) ---
try:
    import psycopg2
    import psycopg2.pool
    import psycopg2.extras
    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False

try:
    import oracledb
    HAS_ORACLE = True
except ImportError:
    HAS_ORACLE = False

# --- Connection pool (Postgres only) ---
_pg_pool = None
_pg_pool_lock = threading.Lock()


def _get_pg_pool():
    """Lazily create a PostgreSQL connection pool (thread-safe singleton)."""
    global _pg_pool
    if _pg_pool is None:
        with _pg_pool_lock:
            if _pg_pool is None:
                _pg_pool = psycopg2.pool.SimpleConnectionPool(
                    minconn=1, maxconn=5,
                    dsn=config.DATABASE_URL
                )
    return _pg_pool


def _convert_placeholders(sql, db_type):
    """
    Convert ? placeholders to the format needed by each database.
    WHY: SQLite uses ?, Postgres uses %s, Oracle uses :1, :2, etc.
    This lets all SQL in routes/services use ? uniformly.
    """
    if db_type == 'sqlite':
        return sql
    elif db_type == 'postgres':
        return sql.replace('?', '%s')
    elif db_type == 'oracle':
        # Replace each ? with :1, :2, :3, etc.
        counter = [0]
        def replacer(match):
            counter[0] += 1
            return f':{counter[0]}'
        return re.sub(r'\?', replacer, sql)
    return sql


def _row_to_dict(row, cursor=None, db_type='sqlite'):
    """Convert a database row to a plain dict."""
    if row is None:
        return None
    if db_type == 'sqlite':
        # sqlite3.Row supports dict() conversion
        return dict(row)
    elif db_type == 'postgres':
        if cursor and cursor.description:
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, row))
        return dict(row) if hasattr(row, 'keys') else row
    elif db_type == 'oracle':
        if cursor and cursor.description:
            columns = [desc[0].lower() for desc in cursor.description]
            return dict(zip(columns, row))
    return row


# =============================================================
# Public API - these are the ONLY functions routes/services call
# =============================================================

def get_connection():
    """
    Get a database connection for the current DB type.
    In Flask, call this once per request and store in g.
    """
    db_type = config.DB_TYPE

    if db_type == 'sqlite':
        conn = sqlite3.connect(config.SQLITE_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute('PRAGMA journal_mode=WAL')     # WAL for better concurrency
        conn.execute('PRAGMA foreign_keys=ON')       # enforce foreign keys
        return conn

    elif db_type == 'postgres':
        if not HAS_PSYCOPG2:
            raise RuntimeError('psycopg2 is not installed. Run: pip install psycopg2-binary')
        pool = _get_pg_pool()
        conn = pool.getconn()
        conn.autocommit = False
        return conn

    elif db_type == 'oracle':
        if not HAS_ORACLE:
            raise RuntimeError('oracledb is not installed. Run: pip install oracledb')
        oracledb.init_oracle_client()  # thin mode
        conn = oracledb.connect(
            user=config.ORACLE_USER,
            password=config.ORACLE_PASSWORD,
            dsn=config.ORACLE_DSN
        )
        return conn

    raise RuntimeError(f'Unknown DB_TYPE: {db_type}')


def close_connection(conn):
    """Return a connection to the pool or close it."""
    if conn is None:
        return
    db_type = config.DB_TYPE
    if db_type == 'postgres' and _pg_pool:
        _pg_pool.putconn(conn)
    else:
        conn.close()


def execute(conn, sql, params=None):
    """
    Execute a write query (INSERT/UPDATE/DELETE).
    Returns the cursor for further inspection if needed.
    """
    db_type = config.DB_TYPE
    converted = _convert_placeholders(sql, db_type)
    cursor = conn.cursor()
    cursor.execute(converted, params or ())
    conn.commit()
    return cursor


def fetch_one(conn, sql, params=None):
    """Fetch a single row as a dict, or None if not found."""
    db_type = config.DB_TYPE
    converted = _convert_placeholders(sql, db_type)
    cursor = conn.cursor()
    cursor.execute(converted, params or ())
    row = cursor.fetchone()
    return _row_to_dict(row, cursor, db_type)


def fetch_all(conn, sql, params=None):
    """Fetch all rows as a list of dicts."""
    db_type = config.DB_TYPE
    converted = _convert_placeholders(sql, db_type)
    cursor = conn.cursor()
    cursor.execute(converted, params or ())
    rows = cursor.fetchall()
    return [_row_to_dict(r, cursor, db_type) for r in rows]


def insert(conn, sql, params=None):
    """
    Execute an INSERT and return the new row's id.
    WHY different approaches:
    - SQLite: cursor.lastrowid works after INSERT
    - Postgres: append RETURNING id if not already present
    - Oracle: uses RETURNING ... INTO with a variable
    """
    db_type = config.DB_TYPE
    converted = _convert_placeholders(sql, db_type)

    if db_type == 'postgres':
        # Auto-append RETURNING id if not already present
        if 'returning' not in converted.lower():
            converted = converted.rstrip(';').rstrip() + ' RETURNING id'
        cursor = conn.cursor()
        cursor.execute(converted, params or ())
        row = cursor.fetchone()
        conn.commit()
        return row[0] if row else None

    elif db_type == 'oracle':
        # Oracle uses RETURNING ... INTO :out_id
        cursor = conn.cursor()
        out_id = cursor.var(oracledb.NUMBER)
        if 'returning' not in converted.lower():
            converted = converted.rstrip(';').rstrip() + ' RETURNING id INTO :out_id'
            all_params = list(params or ()) + [out_id]
        else:
            all_params = list(params or ())
        cursor.execute(converted, all_params)
        conn.commit()
        return int(out_id.getvalue()[0]) if out_id.getvalue() else None

    else:  # sqlite
        cursor = conn.cursor()
        cursor.execute(converted, params or ())
        conn.commit()
        return cursor.lastrowid


def execute_script(conn, sql_text):
    """
    Run a multi-statement SQL script (for schema creation).
    WHY: SQLite has executescript(), others need statement-by-statement execution.
    """
    db_type = config.DB_TYPE

    if db_type == 'sqlite':
        conn.executescript(sql_text)
    else:
        # Split on semicolons and execute each statement
        cursor = conn.cursor()
        statements = [s.strip() for s in sql_text.split(';') if s.strip()]
        for stmt in statements:
            try:
                cursor.execute(stmt)
            except Exception as e:
                # Skip "already exists" errors during schema creation
                err_msg = str(e).lower()
                if 'already exists' in err_msg or 'duplicate' in err_msg:
                    continue
                print(f'  Warning: {e}')
        conn.commit()


def init_db(conn=None):
    """
    Read and execute the appropriate schema file.
    Called once on first startup to create tables.
    """
    db_type = config.DB_TYPE
    own_conn = conn is None

    # Determine which schema file to use
    schema_map = {
        'sqlite': 'schema.sqlite.sql',
        'postgres': 'schema.postgres.sql',
        'oracle': 'schema.oracle.sql',
    }
    schema_file = os.path.join(
        config.BASE_DIR if hasattr(config, 'BASE_DIR') else os.path.abspath(os.path.join(os.path.dirname(__file__), '..')),
        'database',
        schema_map[db_type]
    )

    if not os.path.exists(schema_file):
        print(f'  Schema file not found: {schema_file}')
        return

    with open(schema_file, 'r', encoding='utf-8') as f:
        sql_text = f.read()

    if own_conn:
        conn = get_connection()
    try:
        execute_script(conn, sql_text)
        print(f'  Database schema applied ({db_type})')
    finally:
        if own_conn:
            close_connection(conn)


def check_tables_exist(conn):
    """Check if the users table exists (to decide whether to seed)."""
    db_type = config.DB_TYPE
    try:
        if db_type == 'sqlite':
            row = fetch_one(conn, "SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        elif db_type == 'postgres':
            row = fetch_one(conn, "SELECT tablename FROM pg_tables WHERE tablename='users' AND schemaname='public'")
        elif db_type == 'oracle':
            row = fetch_one(conn, "SELECT table_name FROM user_tables WHERE table_name='USERS'")
        return row is not None
    except Exception:
        return False


def count_users(conn):
    """Count total users in the database."""
    try:
        row = fetch_one(conn, 'SELECT COUNT(*) as cnt FROM users')
        return row['cnt'] if row else 0
    except Exception:
        return 0
