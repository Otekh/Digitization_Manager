"""Entry state store (SQLite) + file moves between workflow folders.

Statuses:
    finalized  - submitted, awaiting admin review   (files in 1_Finalized)
    inspection - needs further inspection           (files in 2_Further_Inspection)
    verified   - approved by admin                  (files in 3_Verified)
    returned   - sent back to creator for edits     (files stay in 1_Finalized,
                                                     no row in data.csv)

Each folder's data.csv is regenerated from this DB after every change, so the
CSV always matches the folder's current entries.
"""
import json
import shutil
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

from . import csv_export, paths

SCHEMA = """
CREATE TABLE IF NOT EXISTS entries (
    id          TEXT PRIMARY KEY,
    status      TEXT NOT NULL,
    created_by  TEXT NOT NULL,
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL,
    verified_by TEXT,
    metadata    TEXT NOT NULL,   -- JSON object: all form fields
    files       TEXT NOT NULL,   -- JSON list of saved filenames
    history     TEXT NOT NULL,   -- JSON list of {at, by, event, note}
    flags       TEXT NOT NULL DEFAULT '{}'  -- JSON object: field key -> reason
);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _connect() -> sqlite3.Connection:
    paths.ensure_data_dirs()
    conn = sqlite3.connect(paths.db_file())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db() -> None:
    with _connect() as conn:
        conn.executescript(SCHEMA)
        # Migrate DBs created before the flags column existed.
        try:
            conn.execute(
                "ALTER TABLE entries ADD COLUMN flags TEXT NOT NULL DEFAULT '{}'"
            )
        except sqlite3.OperationalError:
            pass  # column already exists


def _row_to_entry(row: sqlite3.Row) -> dict:
    e = dict(row)
    e["metadata"] = json.loads(e["metadata"])
    e["files"] = json.loads(e["files"])
    e["history"] = json.loads(e["history"])
    raw = json.loads(e.get("flags") or "{}")
    # Normalize to {field: reason}; older rows stored a plain list of keys.
    if isinstance(raw, dict):
        e["flags"] = {k: (v or "") for k, v in raw.items()}
    else:
        e["flags"] = {k: "" for k in raw}
    return e


def get_entry(entry_id: str) -> dict | None:
    with _connect() as conn:
        row = conn.execute("SELECT * FROM entries WHERE id = ?", (entry_id,)).fetchone()
    return _row_to_entry(row) if row else None


def list_entries(status: str) -> list[dict]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM entries WHERE status = ? ORDER BY created_at", (status,)
        ).fetchall()
    return [_row_to_entry(r) for r in rows]


def counts() -> dict:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT status, COUNT(*) AS n FROM entries GROUP BY status"
        ).fetchall()
    return {r["status"]: r["n"] for r in rows}


def _append_history(entry: dict, by: str, event: str, note: str = "") -> None:
    entry["history"].append({"at": _now(), "by": by, "event": event, "note": note})


def _save_entry(conn: sqlite3.Connection, entry: dict) -> None:
    entry["updated_at"] = _now()
    conn.execute(
        """UPDATE entries SET status=?, updated_at=?, verified_by=?,
           metadata=?, files=?, history=?, flags=? WHERE id=?""",
        (
            entry["status"],
            entry["updated_at"],
            entry.get("verified_by"),
            json.dumps(entry["metadata"]),
            json.dumps(entry["files"]),
            json.dumps(entry["history"]),
            json.dumps(entry.get("flags", {})),
            entry["id"],
        ),
    )


def _regen_csvs(*statuses: str) -> None:
    for status in set(statuses):
        csv_export.write_folder_csv(status, list_entries(status))


def create_entry(metadata: dict, files: list[str], username: str, status: str) -> dict:
    entry = {
        "id": uuid.uuid4().hex[:12],
        "status": status,
        "created_by": username,
        "created_at": _now(),
        "updated_at": _now(),
        "verified_by": None,
        "metadata": metadata,
        "files": files,
        "history": [],
        "flags": {},
    }
    _append_history(entry, username, f"submitted as {status}")
    with _connect() as conn:
        conn.execute(
            """INSERT INTO entries
               (id, status, created_by, created_at, updated_at, verified_by,
                metadata, files, history, flags)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (
                entry["id"],
                entry["status"],
                entry["created_by"],
                entry["created_at"],
                entry["updated_at"],
                None,
                json.dumps(metadata),
                json.dumps(files),
                json.dumps(entry["history"]),
                "{}",
            ),
        )
    _regen_csvs(status)
    return entry


def update_metadata(entry_id: str, metadata: dict, files: list[str], by: str) -> None:
    entry = get_entry(entry_id)
    entry["metadata"] = metadata
    entry["files"] = files
    _append_history(entry, by, "metadata edited")
    with _connect() as conn:
        _save_entry(conn, entry)
    # 'returned' entries have no CSV row; their files sit in 1_Finalized, so
    # regenerate that folder's CSV (the entry simply won't appear in it).
    _regen_csvs("finalized" if entry["status"] == "returned" else entry["status"])


def _move_files(entry: dict, from_status: str, to_status: str) -> None:
    src_dir = paths.folder(from_status)
    dst_dir = paths.folder(to_status)
    dst_dir.mkdir(parents=True, exist_ok=True)
    for name in entry["files"]:
        src = src_dir / name
        if src.exists():
            shutil.move(str(src), str(dst_dir / name))


def change_status(
    entry_id: str, to_status: str, by: str, note: str = "",
    verified_by: str | None = None, flags: dict | None = None,
) -> dict:
    """Move an entry between statuses, moving its files and updating CSVs.

    'returned' keeps files in 1_Finalized (no physical move).
    """
    entry = get_entry(entry_id)
    from_status = entry["status"]

    # Physical location before/after. 'returned' files stay in 1_Finalized.
    loc_before = "finalized" if from_status == "returned" else from_status
    loc_after = "finalized" if to_status == "returned" else to_status
    if loc_before != loc_after:
        _move_files(entry, loc_before, loc_after)

    entry["status"] = to_status
    if verified_by is not None:
        entry["verified_by"] = verified_by
    # Field flags only live on returned entries; cleared on any other move.
    entry["flags"] = dict(flags) if to_status == "returned" and flags else {}
    _append_history(entry, by, f"status -> {to_status}", note)
    with _connect() as conn:
        _save_entry(conn, entry)

    # Regenerate CSVs for every folder whose membership changed.
    affected = {s for s in (from_status, to_status) if s != "returned"}
    if from_status == "returned" or to_status == "returned":
        affected.add("finalized")
    _regen_csvs(*affected)
    return entry


def entry_dir(entry: dict) -> Path:
    """Folder currently holding the entry's files."""
    loc = "finalized" if entry["status"] == "returned" else entry["status"]
    return paths.folder(loc)


def return_note(entry: dict) -> str:
    """The note from the most recent 'returned' event (the flag reason)."""
    for h in reversed(entry["history"]):
        if h["event"] == "status -> returned" and h.get("note"):
            return h["note"]
    return ""
