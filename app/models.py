import os
import sqlite3
from pathlib import Path

from flask import current_app, g, has_app_context
from werkzeug.security import generate_password_hash


def get_database_path():
    if has_app_context():
        return current_app.config["DATABASE"]
    return os.environ.get(
        "AGRICONNECT_DB",
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "agriconnect.db"),
    )


def get_db():
    if "db" not in g:
        conn = sqlite3.connect(get_database_path())
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        g.db = conn
    return g.db


def close_db(_error):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db_path = Path(get_database_path())
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('buyer','farmer','supplier','admin')),
            phone TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS listings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            seller_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            crop TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT,
            quantity INTEGER NOT NULL CHECK(quantity >= 0),
            unit TEXT NOT NULL,
            price REAL NOT NULL CHECK(price >= 0),
            location TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active','paused','sold')),
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (seller_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            buyer_id INTEGER NOT NULL,
            listing_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL CHECK(quantity > 0),
            note TEXT,
            status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','accepted','rejected')),
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (buyer_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (listing_id) REFERENCES listings(id) ON DELETE CASCADE
        );
        """
    )

    admin_email = "admin@agriconnect.co.zw"
    if not conn.execute(
        "SELECT 1 FROM users WHERE email = ?",
        (admin_email,),
    ).fetchone():
        conn.execute(
            "INSERT INTO users (name, email, password_hash, role, phone) VALUES (?, ?, ?, ?, ?)",
            (
                "Admin User",
                admin_email,
                generate_password_hash("admin123"),
                "admin",
                "+263000000000",
            ),
        )

    conn.commit()
    conn.close()
