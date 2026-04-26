import sqlite3
import hashlib
import os
from kivy.app import App
from datetime import datetime

def get_base_dir():
    app = App.get_running_app()
    base = app.user_data_dir
    os.makedirs(base, exist_ok=True)
    return base


def get_db_path():
    return os.path.join(get_base_dir(), "products.db")


def get_json_path():
    date_str = datetime.now().strftime("%d_%m_%Y")
    return os.path.join(get_base_dir(), f".bk_{date_str}.json")


# =========================
# DATABASE FUNCTIONS
# =========================
def hash_password(p):
    return hashlib.sha256(p.encode()).hexdigest()


def db():
    return sqlite3.connect(get_db_path())


def init_db():
    conn = db()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        case_size INTEGER,
        price REAL
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS admin (
        id INTEGER PRIMARY KEY,
        password TEXT
    )
    """)

    c.execute("SELECT * FROM admin WHERE id=1")
    if not c.fetchone():
        c.execute(
            "INSERT INTO admin VALUES(1, ?)",
            (hash_password("1234"),)
        )

    conn.commit()
    conn.close()


def check_password(p):
    conn = db()
    c = conn.cursor()
    c.execute("SELECT password FROM admin WHERE id=1")
    row = c.fetchone()
    conn.close()

    if not row:
        return False

    return row[0] == hash_password(p)


def update_password(p):
    conn = db()
    c = conn.cursor()
    c.execute(
        "UPDATE admin SET password=? WHERE id=1",
        (hash_password(p),)
    )
    conn.commit()
    conn.close()


def get_products():
    conn = db()
    c = conn.cursor()
    c.execute("SELECT id,name,case_size,price FROM products")
    data = c.fetchall()
    conn.close()
    return data


def add_product(name, case_size, price):
    conn = db()
    c = conn.cursor()
    c.execute(
        "INSERT INTO products(name,case_size,price) VALUES(?,?,?)",
        (name, case_size, price)
    )
    conn.commit()
    conn.close()


def update_product(pid, name, case_size, price):
    conn = db()
    c = conn.cursor()
    c.execute(
        "UPDATE products SET name=?,case_size=?,price=? WHERE id=?",
        (name, case_size, price, pid)
    )
    conn.commit()
    conn.close()


def delete_product_db(pid):
    conn = db()
    c = conn.cursor()
    c.execute("DELETE FROM products WHERE id=?", (pid,))
    conn.commit()
    conn.close()


# =========================
# HELPERS
# =========================
def safe_int(v):
    try:
        return int(v)
    except:
        return 0

def get_theme_path():
    return os.path.join(get_base_dir(), "theme.json")
