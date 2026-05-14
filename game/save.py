import sqlite3
import json
import os
import datetime

SAVES_DIR = os.path.join(os.path.dirname(__file__), "..", "saves")
os.makedirs(SAVES_DIR, exist_ok=True)
DB_PATH = os.path.join(SAVES_DIR, "saves.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS saves (
            slot INTEGER PRIMARY KEY,
            name TEXT,
            game_state TEXT,
            timestamp TEXT,
            play_time INTEGER
        )
    """)
    conn.commit()
    conn.close()


def save_game(slot, name, game_state, play_time=0):
    conn = get_connection()
    state_json = json.dumps(game_state)
    timestamp = datetime.datetime.now().isoformat()
    conn.execute("""
        INSERT OR REPLACE INTO saves (slot, name, game_state, timestamp, play_time)
        VALUES (?, ?, ?, ?, ?)
    """, (slot, name, state_json, timestamp, play_time))
    conn.commit()
    conn.close()


def load_game(slot):
    conn = get_connection()
    row = conn.execute("SELECT * FROM saves WHERE slot = ?", (slot,)).fetchone()
    conn.close()
    if row is None:
        return None
    return {
        "slot": row["slot"],
        "name": row["name"],
        "game_state": json.loads(row["game_state"]),
        "timestamp": row["timestamp"],
        "play_time": row["play_time"],
    }


def delete_save(slot):
    conn = get_connection()
    conn.execute("DELETE FROM saves WHERE slot = ?", (slot,))
    conn.commit()
    conn.close()


def get_all_saves():
    conn = get_connection()
    rows = conn.execute("SELECT slot, name, timestamp, play_time FROM saves ORDER BY slot").fetchall()
    conn.close()
    return [dict(row) for row in rows]


def has_save(slot):
    conn = get_connection()
    row = conn.execute("SELECT slot FROM saves WHERE slot = ?", (slot,)).fetchone()
    conn.close()
    return row is not None