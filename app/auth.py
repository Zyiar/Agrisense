# app/auth.py
import sqlite3
import os
import hashlib
import binascii
import time

# Path: ../data/users.db (relative to project root)
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "users.db")

def _ensure_db_dir():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

def get_conn():
    _ensure_db_dir()
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    return conn

def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            username TEXT UNIQUE,
            email TEXT UNIQUE,
            password_hash TEXT,
            created_at REAL
        )
        """
    )
    conn.commit()
    return conn

# PBKDF2 password hashing helpers (stdlib, no extra deps)
def hash_password(password: str, iterations: int = 100_000) -> str:
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return f"{binascii.hexlify(salt).decode()}${iterations}${binascii.hexlify(dk).decode()}"

def verify_password(stored: str, password: str) -> bool:
    try:
        salt_hex, iter_str, dk_hex = stored.split("$")
        salt = binascii.unhexlify(salt_hex)
        iterations = int(iter_str)
        dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
        return binascii.hexlify(dk).decode() == dk_hex
    except Exception:
        return False

# User functions
def create_user(name: str, username: str, email: str, password: str):
    conn = init_db()
    c = conn.cursor()
    pw = hash_password(password)
    try:
        c.execute(
            "INSERT INTO users (name, username, email, password_hash, created_at) VALUES (?, ?, ?, ?, ?)",
            (name, username, email, pw, time.time()),
        )
        conn.commit()
        return True, None
    except sqlite3.IntegrityError as e:
        return False, str(e)

def get_user_by_username(username: str):
    conn = init_db()
    c = conn.cursor()
    c.execute(
        "SELECT id, name, username, email, password_hash, created_at FROM users WHERE username = ?",
        (username,),
    )
    row = c.fetchone()
    if row:
        keys = ["id", "name", "username", "email", "password_hash", "created_at"]
        return dict(zip(keys, row))
    return None

def verify_user(username: str, password: str):
    user = get_user_by_username(username)
    if not user:
        return False, None
    ok = verify_password(user["password_hash"], password)
    return (ok, user if ok else None)
