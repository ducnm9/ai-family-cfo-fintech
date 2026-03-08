import os
import psycopg2
import psycopg2.extras

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://cfo_user:cfo_secret_2026@localhost:5434/family_cfo",
)


def get_db():
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = False
    return conn


def row_to_dict(cursor, row):
    if row is None:
        return None
    return {desc[0]: row[idx] for idx, desc in enumerate(cursor.description)}


class DBWrapper:
    """Thin wrapper to provide dict-like row access similar to sqlite3.Row."""

    def __init__(self):
        self.conn = get_db()
        self.cur = self.conn.cursor()

    def execute(self, sql, params=None):
        self.cur.execute(sql, params or ())
        return self

    def fetchone(self):
        row = self.cur.fetchone()
        return row_to_dict(self.cur, row)

    def fetchall(self):
        rows = self.cur.fetchall()
        return [row_to_dict(self.cur, r) for r in rows]

    @property
    def lastrowid(self):
        return self.cur.fetchone()[0] if self.cur.description else None

    def commit(self):
        self.conn.commit()

    def close(self):
        self.cur.close()
        self.conn.close()


def get_wrapped_db() -> DBWrapper:
    return DBWrapper()


def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            full_name TEXT NOT NULL,
            hashed_password TEXT NOT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS profiles (
            id SERIAL PRIMARY KEY,
            user_id INTEGER UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            data JSONB NOT NULL DEFAULT '{}',
            updated_at TIMESTAMP DEFAULT NOW()
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS family_members (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            name TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'member',
            created_at TIMESTAMP DEFAULT NOW()
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS monthly_snapshots (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            month TEXT NOT NULL,
            data JSONB NOT NULL,
            summary JSONB NOT NULL DEFAULT '{}',
            notes TEXT DEFAULT '',
            closed_at TIMESTAMP DEFAULT NOW(),
            UNIQUE(user_id, month)
        );
    """)
    # V2 tables for intelligence layer
    cur.execute("""
        CREATE TABLE IF NOT EXISTS income_history (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            month TEXT NOT NULL,
            source_name TEXT NOT NULL,
            amount NUMERIC NOT NULL,
            recorded_at TIMESTAMP DEFAULT NOW(),
            UNIQUE(user_id, month, source_name)
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS expense_history (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            month TEXT NOT NULL,
            category TEXT NOT NULL,
            amount NUMERIC NOT NULL,
            recorded_at TIMESTAMP DEFAULT NOW(),
            UNIQUE(user_id, month, category)
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS financial_scores (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            month TEXT NOT NULL,
            score INTEGER NOT NULL,
            grade TEXT NOT NULL,
            breakdown JSONB NOT NULL DEFAULT '{}',
            recorded_at TIMESTAMP DEFAULT NOW(),
            UNIQUE(user_id, month)
        );
    """)
    conn.commit()
    cur.close()
    conn.close()
