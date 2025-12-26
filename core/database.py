import sqlite3
import json
from datetime import datetime

# Keeping it simple with SQLite for the prototype
DB_FILE = "pulse_history.db"

def init_db():
    try:
        conn = sqlite3.connect(DB_FILE)
        # Create table if it doesn't exist yet
        conn.execute('''
            CREATE TABLE IF NOT EXISTS scan_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                target_url TEXT, 
                scan_date TEXT, 
                result_json TEXT
            )
        ''')
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"DB Init Error: {e}")

def save_result(url, data_obj):
    conn = sqlite3.connect(DB_FILE)
    # Dump Pydantic models to a JSON string for storage
    raw_json = json.dumps([item.dict() for item in data_obj])
    conn.execute(
        "INSERT INTO scan_history (target_url, scan_date, result_json) VALUES (?, ?, ?)",
        (url, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), raw_json)
    )
    conn.commit()
    conn.close()

def fetch_logs():
    conn = sqlite3.connect(DB_FILE)
    # Get last 10 scans
    cursor = conn.execute("SELECT target_url, scan_date, result_json FROM scan_history ORDER BY id DESC LIMIT 10")
    rows = cursor.fetchall()
    conn.close()
    return rows