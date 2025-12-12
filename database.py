import sqlite3
DB_NAME = "challan.db"
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    # Create users table for login/signup
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    """)
    # Create challan table with user_id to link challan to the user
    cur.execute("""
    CREATE TABLE IF NOT EXISTS challan(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,          -- NEW: user who created the challan
        name TEXT NOT NULL,
        vehicle TEXT NOT NULL,
        violation TEXT NOT NULL,
        fine INTEGER NOT NULL,
        issued_at TEXT NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)
    conn.commit()
    conn.close()
def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # Access columns by name
    return conn




