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


def _seed_demo_market(conn):
    from ai.demo_products import iter_demo_products

    seller_specs = (
        ("demo-farmer-1@agriconnect.co.zw", "Mbare Growers Cooperative", "farmer"),
        ("demo-farmer-2@agriconnect.co.zw", "Highveld Family Farm", "farmer"),
        ("demo-supplier@agriconnect.co.zw", "GreenFields Inputs", "supplier"),
    )
    seller_ids = []
    for email, name, role in seller_specs:
        row = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if row is None:
            conn.execute(
                "INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, ?)",
                (name, email, generate_password_hash(os.urandom(32).hex()), role),
            )
            row = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        seller_ids.append(row[0])

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS demo_listing_seed (
            seed_key TEXT PRIMARY KEY,
            listing_id INTEGER NOT NULL UNIQUE,
            FOREIGN KEY (listing_id) REFERENCES listings(id) ON DELETE CASCADE
        )
        """
    )

    for product in iter_demo_products():
        existing = conn.execute(
            "SELECT listing_id FROM demo_listing_seed WHERE seed_key = ?", (product["key"],)
        ).fetchone()
        if existing:
            conn.execute(
                "UPDATE listings SET seller_id = ? WHERE id = ?",
                (seller_ids[product["seller_index"]], existing[0]),
            )
            continue
        cursor = conn.execute(
            """
            INSERT INTO listings (
                seller_id, title, crop, category, description, quantity,
                unit, price, location, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'active')
            """,
            (
                seller_ids[product["seller_index"]],
                product["title"],
                product["crop"],
                product["category"],
                product["description"],
                product["quantity"],
                product["unit"],
                product["price"],
                product["location"],
            ),
        )
        conn.execute(
            "INSERT INTO demo_listing_seed (seed_key, listing_id) VALUES (?, ?)",
            (product["key"], cursor.lastrowid),
        )


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

        CREATE TABLE IF NOT EXISTS login_attempts (
            email TEXT PRIMARY KEY,
            attempts INTEGER NOT NULL DEFAULT 0,
            locked_until INTEGER
        );
        """
    )

    admin_email = "admin@agriconnect.co.zw"
    if not conn.execute("SELECT 1 FROM users WHERE email = ?", (admin_email,)).fetchone():
        conn.execute(
            "INSERT INTO users (name, email, password_hash, role, phone) VALUES (?, ?, ?, ?, ?)",
            ("Admin User", admin_email, generate_password_hash("admin123"), "admin", "+263000000000"),
        )

    _seed_demo_market(conn)
    conn.commit()
    conn.close()
