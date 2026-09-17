"""Write each workflow folder's data.csv in DSpace Dublin Core format.

Format matches data/bulk_csv_reference.csv: one header row of Dublin Core
field names, then one row per entry. Coded dropdowns export their code, not
the description. dc.subject is "Theme::Sub Theme::600" pairs joined by "||".
The trailing 'filename' column lists the entry's files joined by "||" (this
is what SAFBuilder uses to find bitstreams).
"""
import csv

from . import options, paths

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

SUBJECT_SUFFIX = "600"


def _subject_value(subjects: list[dict]) -> str:
    parts = [
        f"{s['theme']}::{s['sub']}::{SUBJECT_SUFFIX}"
        for s in subjects
        if s.get("theme")
    ]
    return "||".join(parts)


def entry_to_row(entry: dict) -> list[str]:
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
