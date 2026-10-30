"""SQLite glabātuve rezultātiem."""
import os
import sqlite3
from contextlib import closing

DB_PATH = os.environ.get("RUSHJOB_DB", os.path.join(os.path.dirname(__file__), "scores.db"))


def _connect():
    return sqlite3.connect(DB_PATH)


def init_db():
    with closing(_connect()) as conn, conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS scores (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   name TEXT NOT NULL,
                   score INTEGER NOT NULL,
                   seconds REAL NOT NULL,
                   created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
               )""")


def add_score(name, score, seconds):
    with closing(_connect()) as conn, conn:
        conn.execute("INSERT INTO scores (name, score, seconds) VALUES (?, ?, ?)",
                     (name, score, seconds))


def top_scores(limit=10):
    with closing(_connect()) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT name, score, seconds, created_at FROM scores "
            "ORDER BY score DESC, seconds DESC LIMIT ?", (limit,)).fetchall()
    return [dict(r) for r in rows]
