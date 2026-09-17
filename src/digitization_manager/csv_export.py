"""Write each workflow folder's data.csv in DSpace Dublin Core format.

Format matches data/bulk_csv_reference.csv: one header row of Dublin Core
field names, then one row per entry. Coded dropdowns export their code, not
the description. dc.subject is "Theme::Sub Theme::600" pairs joined by "||".
The trailing 'filename' column lists the entry's files joined by "||" (this
is what SAFBuilder uses to find bitstreams).
"""
import csv  # writing data.csv

from . import options, paths  # code lookups + folder locations

# Dublin Core columns, in the exact order SAFBuilder/DSpace expects.
HEADER = [
    "dc.coverage.spatial",
    "dc.date.issued",
    "dc.description.abstract",
    "dc.source",
    "dc.subject",
    "dc.title",
    "dc.type",
    "local.coverage.era",
    "local.description.lineage",
    "local.equipment",
    "local.rights.access",
    "local.rights.aitrainable",
    "filename",
]

# DSpace subject authority suffix appended to every Theme::Sub pair.
SUBJECT_SUFFIX = "600"


def _subject_value(subjects: list[dict]) -> str:
    """Flatten theme/sub pairs into one dc.subject cell:
    'Theme::Sub::600||Theme::Sub::600'."""
    parts = [
        f"{s['theme']}::{s['sub']}::{SUBJECT_SUFFIX}"
        for s in subjects
        if s.get("theme")
    ]
    return "||".join(parts)


def entry_to_row(entry: dict) -> list[str]:
    """Map an entry's metadata dict onto the HEADER columns. Coded
    dropdowns export their code (e.g. 'BK'), not the label."""
    m = entry["metadata"]
    return [
        options.code_for("Location", m.get("location", "")),
        m.get("date_value", ""),
        m.get("summary", ""),
        options.code_for("Collection, Source", m.get("collection_source", "")),
        _subject_value(m.get("subjects", [])),
        m.get("title", ""),
        options.code_for("Media Type", m.get("media_type", "")),
        m.get("era", ""),
        m.get("lineage", ""),
        options.code_for("Equipment ID", m.get("equipment_id", "")),
        m.get("access_control", ""),
        m.get("ai_trainable", ""),
        "||".join(entry["files"]),
    ]


def write_folder_csv(status: str, entries: list[dict]) -> None:
    """Rewrite data.csv for a folder. Deletes the file if the folder is empty."""
    csv_path = paths.folder(status) / "data.csv"
    if not entries:
        csv_path.unlink(missing_ok=True)
        return
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(HEADER)
        for e in entries:
            writer.writerow(entry_to_row(e))


# master.csv = HEADER + two bookkeeping columns: 'saf' is yes once the
# entry has been packaged for DSpace (no = still only on this machine),
# 'entry_id' links the row back to the live entry while it exists.
MASTER_HEADER = HEADER + ["saf", "entry_id"]


def _read_master() -> tuple[list[str], list[list[str]]]:
    """(header, data rows) from master.csv, padded to the header width.

    Migrates a pre-saf/entry_id master by appending the columns — those
    rows were all packaged entries, so saf defaults to yes."""
    master = paths.master_csv()
    if not master.exists():
        return MASTER_HEADER, []
    with master.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.reader(f))
    if not rows:
        return MASTER_HEADER, []
    header, data = rows[0], rows[1:]
    migrated = header != MASTER_HEADER
    if migrated:
        header = MASTER_HEADER
    width = len(header)
    padded = [(r + [""] * width)[:width] for r in data]
    if migrated:
        for r in padded:
            r[-2] = r[-2] or "yes"  # pre-existing rows were packaged
    return header, padded


def _write_master(header: list[str], data: list[list[str]]) -> None:
    with paths.master_csv().open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(header)
        w.writerows(data)


def append_master(entries: list[dict]) -> None:
    """Record newly created entries in master.csv (saf=no — not yet
    packaged). Skips ids already present."""
    if not entries:
        return
    header, data = _read_master()
    known = {r[-1] for r in data}
    for e in entries:
        if e["id"] not in known:
            data.append(entry_to_row(e) + ["no", e["id"]])
    _write_master(header, data)


def update_master_row(entry: dict) -> None:
    """Sync an entry's master row after a metadata/file edit, keeping
    its saf flag. Appends a row if the entry isn't recorded yet."""
    header, data = _read_master()
    for i, row in enumerate(data):
        if row[-1] == entry["id"]:
            data[i] = entry_to_row(entry) + [row[-2], entry["id"]]
            break
    else:
        data.append(entry_to_row(entry) + ["no", entry["id"]])
    _write_master(header, data)


def mark_packaged(entries: list[dict]) -> None:
    """Set saf=yes on each entry's master row after a SAF build
    (appending any that are missing, e.g. pre-master entries)."""
    ids = {e["id"] for e in entries}
    header, data = _read_master()
    found = set()
    for row in data:
        if row[-1] in ids:
            row[-2] = "yes"
            found.add(row[-1])
    for e in entries:
        if e["id"] not in found:
            data.append(entry_to_row(e) + ["yes", e["id"]])
    _write_master(header, data)


def read_master() -> tuple[list[str], list[list[str]]]:
    """(header, rows) for the View Master CSV admin page."""
    return _read_master()


def update_master_cells(index: int, values: list[str]) -> bool:
    """Replace data row `index` (0-based) with new cell values."""
    header, data = _read_master()
    if not 0 <= index < len(data):
        return False
    data[index] = (values + [""] * len(header))[: len(header)]
    _write_master(header, data)
    return True


def delete_master_row(index: int) -> bool:
    """Delete data row `index` (0-based) from master.csv."""
    header, data = _read_master()
    if not 0 <= index < len(data):
        return False
    del data[index]
    _write_master(header, data)
    return True


def find_duplicates(metadata: dict, exclude_id: str = "") -> list[dict]:
    """Master-CSV rows matching this entry on title + lineage + source
    (case-insensitive). Run when an entry is verified to warn that it
    may already exist — exclude_id skips the entry's own row."""
    master = paths.master_csv()
    if not master.exists():
        return []
    title = metadata.get("title", "").strip().casefold()
    lineage = metadata.get("lineage", "").strip().casefold()
    # Master stores the export code, so compare coded vs coded.
    source = options.code_for(
        "Collection, Source", metadata.get("collection_source", "")
    ).strip().casefold()
    matches = []
    with master.open("r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            if exclude_id and row.get("entry_id") == exclude_id:
                continue
            if (
                row.get("dc.title", "").strip().casefold() == title
                and row.get("local.description.lineage", "").strip().casefold()
                == lineage
                and row.get("dc.source", "").strip().casefold() == source
            ):
                matches.append(row)
    return matches
