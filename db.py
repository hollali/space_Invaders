import sqlite3
from datetime import date
from constants import DB_FILE


class HighScoreDB:
    def __init__(self, db_path=None):
        self.path = db_path or DB_FILE
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.path) as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS scores ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "score INTEGER NOT NULL, "
                "name TEXT NOT NULL DEFAULT 'PLAYER', "
                "date TEXT NOT NULL)"
            )
            columns = [row[1] for row in conn.execute("PRAGMA table_info(scores)")]
            if "name" not in columns:
                conn.execute(
                    "ALTER TABLE scores ADD COLUMN name TEXT NOT NULL DEFAULT 'PLAYER'"
                )

    def add_score(self, score, name="PLAYER"):
        with sqlite3.connect(self.path) as conn:
            conn.execute(
                "INSERT INTO scores (score, name, date) VALUES (?, ?, ?)",
                (score, name, date.today().isoformat()),
            )

    def get_high_score(self):
        with sqlite3.connect(self.path) as conn:
            row = conn.execute("SELECT MAX(score) FROM scores").fetchone()
            return row[0] if row and row[0] is not None else 0

    def get_top_scores(self, limit=5):
        with sqlite3.connect(self.path) as conn:
            rows = conn.execute(
                "SELECT score, name, date FROM scores ORDER BY score DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return rows
