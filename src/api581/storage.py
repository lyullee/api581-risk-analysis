"""Local immutable result archive; create one repository per application instance."""
import json
from pathlib import Path
try:
    import sqlite3
except ImportError as exc:  # pragma: no cover - exercised on stripped HPC images
    # Some cluster Python builds ship the sqlite3 stdlib wrapper without the
    # compiled `_sqlite3` extension.  A staged pysqlite3-binary wheel can
    # provide the same DB-API surface without changing the public RunStore API.
    if getattr(exc, "name", None) != "_sqlite3":
        raise
    try:
        import pysqlite3 as sqlite3
    except ImportError:
        raise exc


class RunStore:
    def __init__(self, path: str):
        self.path = path
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.execute("CREATE TABLE IF NOT EXISTS runs (run_id TEXT PRIMARY KEY, asset_id TEXT, calculated_at TEXT NOT NULL, payload TEXT NOT NULL)")
            db.execute("CREATE INDEX IF NOT EXISTS runs_asset ON runs(asset_id, calculated_at)")

    def connect(self):
        return sqlite3.connect(self.path, timeout=30)

    def save(self, result):
        with self.connect() as db:
            db.execute("INSERT INTO runs VALUES (?, ?, ?, ?)", (result["run_id"], result["context"].get("asset_id"),
                       result["calculated_at"], json.dumps(result, allow_nan=False)))

    def get(self, run_id):
        with self.connect() as db:
            row = db.execute("SELECT payload FROM runs WHERE run_id = ?", (run_id,)).fetchone()
        return json.loads(row[0]) if row else None

    def list(self, asset_id, limit):
        with self.connect() as db:
            rows = db.execute("SELECT payload FROM runs WHERE asset_id = ? ORDER BY calculated_at DESC LIMIT ?", (asset_id, limit)).fetchall()
        return [json.loads(row[0]) for row in rows]
