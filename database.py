# database.py
import sqlite3
from datetime import datetime

def init_db():
    conn = sqlite3.connect("chat_history.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS conversations
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id TEXT,
                  character TEXT,
                  role TEXT,
                  content TEXT,
                  anger INTEGER,
                  sadness INTEGER,
                  timestamp TEXT)''')
    conn.commit()
    conn.close()

def save_message(user_id, character, role, content, anger, sadness):
    conn = sqlite3.connect("chat_history.db")
    c = conn.cursor()
    timestamp = datetime.now().isoformat()
    c.execute("INSERT INTO conversations (user_id, character, role, content, anger, sadness, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)",
              (user_id, character, role, content, anger, sadness, timestamp))
    conn.commit()
    conn.close()

def search_user_history(search_term):
    conn = sqlite3.connect("chat_history.db")
    c = conn.cursor()
    c.execute("SELECT user_id, character, content, timestamp FROM conversations WHERE user_id LIKE ? OR content LIKE ? ORDER BY timestamp",
              (f"%{search_term}%", f"%{search_term}%"))
    results = c.fetchall()
    conn.close()
    return [{"user_id": row[0], "character": row[1], "content": row[2], "timestamp": row[3]} for row in results]