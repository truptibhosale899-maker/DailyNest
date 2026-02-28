"""
DailyNest – Database Models
────────────────────────────
Helper functions for database operations.
Imported by app.py and the bot if needed.
"""

import sqlite3
import hashlib

DATABASE = "database.db"


def get_db():
    """Open a database connection with Row factory."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialise the database schema."""
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            username    TEXT UNIQUE NOT NULL,
            password    TEXT NOT NULL,
            preferences TEXT DEFAULT 'general',
            telegram_id TEXT DEFAULT '',
            created_at  TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def create_user(username: str, password: str) -> bool:
    """Create a new user. Returns True on success, False if username taken."""
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, hash_password(password))
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def authenticate_user(username: str, password: str):
    """Return user row if credentials are valid, else None."""
    conn = get_db()
    user = conn.execute(
        "SELECT * FROM users WHERE username = ? AND password = ?",
        (username, hash_password(password))
    ).fetchone()
    conn.close()
    return user


def update_preferences(user_id: int, preferences: str, telegram_id: str):
    """Update a user's preferences and telegram_id."""
    conn = get_db()
    conn.execute(
        "UPDATE users SET preferences = ?, telegram_id = ? WHERE id = ?",
        (preferences, telegram_id, user_id)
    )
    conn.commit()
    conn.close()


def get_all_users_with_telegram():
    """Fetch users with Telegram IDs (for the bot)."""
    conn = get_db()
    users = conn.execute(
        "SELECT * FROM users WHERE telegram_id != '' AND telegram_id IS NOT NULL"
    ).fetchall()
    conn.close()
    return [dict(u) for u in users]
