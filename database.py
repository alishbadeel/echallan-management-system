import sqlite3

def init_db():
    conn = sqlite3.connect("challan.db")
    conn.execute("""
    CREATE TABLE IF NOT EXISTS challan(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        vehicle TEXT,
        fine INTEGER,
        violation TEXT,
        issued_at TEXT,
        paid INTEGER DEFAULT 0
                 
    )
    """)
    conn.close()

def get_db():
    return sqlite3.connect("challan.db")



