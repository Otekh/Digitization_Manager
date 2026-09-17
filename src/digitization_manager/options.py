"""Dropdown options parsed from data/components.csv.

The CSV has one column per dropdown. Some columns hold "CODE, Description"
pairs (Media Type, Collection Source, Location, Equipment ID): the UI shows
the description, exports write the code. Other columns are plain values.

Theme <-> Sub-theme mapping is positional: the Theme column's Nth value owns
the "SubN" column. (Sub column headers name their parent theme loosely, so
position is more reliable than name matching.)
"""
import csv
from functools import lru_cache

from . import paths

# Columns whose values are "CODE, Description" pairs.
CODED_COLUMNS = {"Media Type", "Collection, Source", "Location", "Equipment ID"}


def _split_code(value: str) -> dict:
    """'BK, Book' -> {'code': 'BK', 'label': 'Book'}. Plain values use themselves."""
    value = value.strip()
    if "," in value:
        code, label = value.split(",", 1)
        return {"code": code.strip(), "label": label.strip()}
    return {"code": value, "label": value}


@lru_cache(maxsize=1)
def load_options() -> dict:
    """Parse components.csv into dropdown data.

    Returns:
        fields:   {column_name: [ {code, label}, ... ]} for the simple dropdowns
        themes:   [theme label, ...]
        subthemes: {theme label: [sub label, ...]}
    """
    csv_path = paths.components_csv()
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))

    # Sub column headers look like "Sub1, Haudenosaunee Foundations" — the
    # part before the comma is the key, the rest names the parent theme.
    header = []
    for h in rows[0]:
        h = h.strip()
        if h.startswith("Sub") and "," in h:
            h = h.split(",", 1)[0].strip()
        header.append(h)

    columns: dict[str, list[str]] = {h: [] for h in header}
    for row in rows[1:]:
        for i, h in enumerate(header):
            value = row[i].strip() if i < len(row) else ""
            if value:
                columns[h].append(value)

    fields: dict[str, list[dict]] = {}
    for name, values in columns.items():
        if name.startswith("Sub") or name == "Theme":
            continue
        if name in CODED_COLUMNS:
            fields[name] = [_split_code(v) for v in values]
        else:
            fields[name] = [{"code": v, "label": v} for v in values]

    themes = columns.get("Theme", [])
    subthemes: dict[str, list[str]] = {}
    for i, theme in enumerate(themes):
        sub_col = columns.get(f"Sub{i + 1}", [])
        subthemes[theme] = sub_col

    return {"fields": fields, "themes": themes, "subthemes": subthemes}


def code_for(field: str, label: str) -> str:
    """Look up the export code for a chosen dropdown label."""
    for opt in load_options()["fields"].get(field, []):
        if opt["label"] == label or opt["code"] == label:
            return opt["code"]
    return label
