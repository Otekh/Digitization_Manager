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


# ------------------------------------------------------------- editing
#
# The CSV is column-oriented and ragged, so edits read the whole table,
# mutate one column, and rewrite. Columns are tracked by INDEX (the file
# has a duplicated "AI Trainable" header, so names aren't unique).

def _header_key(h: str) -> str:
    h = h.strip()
    if h.startswith("Sub") and "," in h:
        h = h.split(",", 1)[0].strip()
    return h


def _read_table() -> tuple[list[str], list[list[str]]]:
    """Return (raw_header, columns-by-index) with blanks stripped."""
    csv_path = paths.components_csv()
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))
    raw_header = [h.strip() for h in rows[0]]
    cols: list[list[str]] = [[] for _ in raw_header]
    for row in rows[1:]:
        for i in range(len(raw_header)):
            v = row[i].strip() if i < len(row) else ""
            if v:
                cols[i].append(v)
    return raw_header, cols


def _write_table(raw_header: list[str], cols: list[list[str]]) -> None:
    nrows = max((len(c) for c in cols), default=0)
    csv_path = paths.components_csv()
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(raw_header)
        for r in range(nrows):
            w.writerow([c[r] if r < len(c) else "" for c in cols])
    load_options.cache_clear()


def _col_index(raw_header: list[str], key: str) -> int:
    """First column whose header key matches (Sub headers key on 'SubN')."""
    for i, h in enumerate(raw_header):
        if _header_key(h) == key:
            return i
    raise ValueError(f"Unknown dropdown: {key}")


def code_length(field: str) -> int | None:
    """Required code length for a coded column (most common existing
    length). None when the column has no coded values yet."""
    if field not in CODED_COLUMNS:
        return None
    lengths = [
        len(o["code"]) for o in load_options()["fields"].get(field, [])
    ]
    if not lengths:
        return None
    return max(set(lengths), key=lengths.count)


def add_option(field: str, label: str, code: str = "") -> None:
    """Append an option to a simple dropdown column.

    Coded columns require a code matching the column's existing code
    length (e.g. Media Type codes are 2 chars, Location codes 4).
    """
    label = label.strip()
    if not label:
        raise ValueError("Option name is required.")
    raw_header, cols = _read_table()
    i = _col_index(raw_header, field)
    existing = [_split_code(v) for v in cols[i]]
    if any(o["label"].lower() == label.lower() or o["code"].lower() == label.lower()
           for o in existing):
        raise ValueError(f'"{label}" is already an option for {field}.')

    if field in CODED_COLUMNS:
        code = code.strip().upper()
        need = code_length(field)
        if not code:
            raise ValueError(f"{field} options need a code.")
        if not code.isalnum():
            raise ValueError("Codes may only contain letters and numbers.")
        if need is not None and len(code) != need:
            raise ValueError(
                f"{field} codes must be {need} characters "
                f'(e.g. "{existing[0]["code"]}").'
            )
        if any(o["code"].lower() == code.lower() for o in existing):
            raise ValueError(f'Code "{code}" is already used in {field}.')
        cols[i].append(f"{code}, {label}")
    else:
        cols[i].append(label)
    _write_table(raw_header, cols)


def delete_option(field: str, label: str) -> None:
    """Remove an option from a simple dropdown column (matches on the
    label or the code)."""
    raw_header, cols = _read_table()
    i = _col_index(raw_header, field)
    before = len(cols[i])
    cols[i] = [
        v for v in cols[i]
        if _split_code(v)["label"] != label and _split_code(v)["code"] != label
    ]
    if len(cols[i]) == before:
        raise ValueError(f'"{label}" is not an option for {field}.')
    _write_table(raw_header, cols)


def edit_option(field: str, old_label: str, new_label: str,
                new_code: str = "") -> None:
    """Rename an option (and its code for coded columns). Same code
    rules as add_option."""
    new_label = new_label.strip()
    if not new_label:
        raise ValueError("Option name is required.")
    raw_header, cols = _read_table()
    i = _col_index(raw_header, field)
    existing = [_split_code(v) for v in cols[i]]
    idx = next(
        (n for n, o in enumerate(existing)
         if o["label"] == old_label or o["code"] == old_label),
        None,
    )
    if idx is None:
        raise ValueError(f'"{old_label}" is not an option for {field}.')
    others = existing[:idx] + existing[idx + 1:]
    if any(o["label"].lower() == new_label.lower()
           or o["code"].lower() == new_label.lower() for o in others):
        raise ValueError(f'"{new_label}" is already an option for {field}.')

    if field in CODED_COLUMNS:
        new_code = new_code.strip().upper()
        need = code_length(field)
        if not new_code:
            raise ValueError(f"{field} options need a code.")
        if not new_code.isalnum():
            raise ValueError("Codes may only contain letters and numbers.")
        if need is not None and len(new_code) != need:
            raise ValueError(
                f"{field} codes must be {need} characters "
                f'(e.g. "{existing[0]["code"]}").'
            )
        if any(o["code"].lower() == new_code.lower() for o in others):
            raise ValueError(f'Code "{new_code}" is already used in {field}.')
        cols[i][idx] = f"{new_code}, {new_label}"
    else:
        cols[i][idx] = new_label
    _write_table(raw_header, cols)


def _theme_col(raw_header: list[str]) -> int:
    return _col_index(raw_header, "Theme")


def add_theme(theme: str, subthemes: list[str]) -> None:
    """Add a theme plus its own Sub column. A theme needs at least one
    sub-theme."""
    theme = theme.strip()
    subs = [s.strip() for s in subthemes if s.strip()]
    if not theme:
        raise ValueError("Theme name is required.")
    if not subs:
        raise ValueError("Add at least one sub-theme for the new theme.")
    raw_header, cols = _read_table()
    ti = _theme_col(raw_header)
    if any(t.lower() == theme.lower() for t in cols[ti]):
        raise ValueError(f'"{theme}" is already a theme.')
    cols[ti].append(theme)
    n = len(cols[ti])  # new theme's position -> Sub{n}
    raw_header.append(f"Sub{n}, {theme}")
    cols.append(subs)
    _write_table(raw_header, cols)


def delete_theme(theme: str) -> None:
    """Remove a theme and its whole Sub column, renumbering the rest."""
    raw_header, cols = _read_table()
    ti = _theme_col(raw_header)
    if theme not in cols[ti]:
        raise ValueError(f'"{theme}" is not a theme.')
    pos = cols[ti].index(theme)  # 0-based -> Sub{pos+1}
    cols[ti].pop(pos)
    si = _col_index(raw_header, f"Sub{pos + 1}")
    raw_header.pop(si)
    cols.pop(si)
    # Renumber remaining Sub headers to stay aligned with theme positions.
    sub_n = 0
    for i, h in enumerate(raw_header):
        if _header_key(h).startswith("Sub"):
            sub_n += 1
            raw_header[i] = f"Sub{sub_n}, {cols[ti][sub_n - 1]}"
    _write_table(raw_header, cols)


def edit_theme(old: str, new: str) -> None:
    """Rename a theme; its Sub column header is updated to match."""
    new = new.strip()
    if not new:
        raise ValueError("Theme name is required.")
    raw_header, cols = _read_table()
    ti = _theme_col(raw_header)
    if old not in cols[ti]:
        raise ValueError(f'"{old}" is not a theme.')
    if any(t.lower() == new.lower() for t in cols[ti] if t != old):
        raise ValueError(f'"{new}" is already a theme.')
    pos = cols[ti].index(old)
    cols[ti][pos] = new
    si = _col_index(raw_header, f"Sub{pos + 1}")
    raw_header[si] = f"Sub{pos + 1}, {new}"
    _write_table(raw_header, cols)


def add_subtheme(theme: str, label: str) -> None:
    label = label.strip()
    if not label:
        raise ValueError("Sub-theme name is required.")
    raw_header, cols = _read_table()
    ti = _theme_col(raw_header)
    if theme not in cols[ti]:
        raise ValueError(f'"{theme}" is not a theme.')
    si = _col_index(raw_header, f"Sub{cols[ti].index(theme) + 1}")
    if any(s.lower() == label.lower() for s in cols[si]):
        raise ValueError(f'"{label}" is already a sub-theme of {theme}.')
    cols[si].append(label)
    _write_table(raw_header, cols)


def delete_subtheme(theme: str, label: str) -> None:
    raw_header, cols = _read_table()
    ti = _theme_col(raw_header)
    if theme not in cols[ti]:
        raise ValueError(f'"{theme}" is not a theme.')
    si = _col_index(raw_header, f"Sub{cols[ti].index(theme) + 1}")
    if label not in cols[si]:
        raise ValueError(f'"{label}" is not a sub-theme of {theme}.')
    cols[si].remove(label)
    _write_table(raw_header, cols)


def edit_subtheme(theme: str, old: str, new: str) -> None:
    new = new.strip()
    if not new:
        raise ValueError("Sub-theme name is required.")
    raw_header, cols = _read_table()
    ti = _theme_col(raw_header)
    if theme not in cols[ti]:
        raise ValueError(f'"{theme}" is not a theme.')
    si = _col_index(raw_header, f"Sub{cols[ti].index(theme) + 1}")
    if old not in cols[si]:
        raise ValueError(f'"{old}" is not a sub-theme of {theme}.')
    if any(s.lower() == new.lower() for s in cols[si] if s != old):
        raise ValueError(f'"{new}" is already a sub-theme of {theme}.')
    cols[si][cols[si].index(old)] = new
    _write_table(raw_header, cols)
