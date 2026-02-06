# app/db_utils.py
import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "users.db"

def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    """Initialize the database and create logs table if it doesn't exist."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        action TEXT,
        timestamp TEXT
    )
    """)
    conn.commit()
    conn.close()

def log_action(username, action):
    """Insert a log entry into the logs table."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO logs (username, action, timestamp) VALUES (?, ?, ?)",
        (username, action, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()
