# agent.md

Project rules for agents working in this folder. Also see the root
`/home/zeegles/05_Projects/DEVIN_dir/agent.md` and the OTEKH design guide at
`/home/zeegles/05_Projects/DEVIN_dir/OTEKH_Apps_Design_2026/agent.md`.

## What this is

OTEKH Digitization Manager — a LAN web app (Python + Flask + Jinja + vanilla
JS, no build step) for digitization intake, admin review, and DSpace SAF
packaging. One lab machine runs the server; clients use a browser.

## Hard rules

- Human-readable source only; a human must be able to edit it unaided.
- Cross-OS: macOS + Linux priority; Windows only if the user asks.
- UI follows `shell/` (OTKEH App Shell) exactly — tokens, fonts, components.
  No redesign, recolour, or substitution.
- Use `nala` (not `apt`) for Linux package instructions.
- No git commit/push/pull unless the user asks.
- Passwords live only in `auth.json` (hashed) inside the data root — never
  in source.

## Key files

- `src/digitization_manager/app.py` — routes, validation, workflow actions
- `src/digitization_manager/store.py` — SQLite entry state + folder moves
- `src/digitization_manager/csv_export.py` — Dublin Core data.csv writer
- `src/digitization_manager/options.py` — components.csv dropdown parser
- `src/digitization_manager/auth.py` — users (hidden admin backdoor)
- `src/digitization_manager/ocr.py` — ocrmypdf on verify
- `src/digitization_manager/safbuilder.py` — SAFBuilder jar runner
- `data/components.csv` — dropdown source (Sub1..15 map to Theme by position)

## Run for development

```bash
uv venv && uv pip install -e .
uv run digitization_manager --no-browser
# or: .venv/bin/python -m digitization_manager.main
```

Data root defaults to `~/Documents/OTEKH Digitization Manager`; override
with `DIGIMGR_DATA=/some/path` for testing.
