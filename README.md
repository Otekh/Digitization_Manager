# OTEKH Digitization Manager

A lab-internal web app for digitization management: staff digitize physical
objects, enter metadata, attach files, and route entries through review to a
DSpace-ready archive.

Combines the old DSpace Manager (metadata intake + review) and the Bulk
Upload Zip Creator (SAF packaging) into one app.

## How it works

- One lab machine runs the server (`digitization_manager`). It holds the
  archive folders and user accounts.
- Everyone else opens a browser to `http://<server-ip>:8000` over the wired
  LAN. Nothing is installed on client machines; no internet is needed.

### Workflow

1. **New Entry** — fill metadata, upload file(s), then **Finalize** or
   **Further Inspection**. Validation runs on submit.
2. **Finalized** entries wait in `1_Finalized/` for an admin.
3. **Admin review** — Verify (OCRs PDFs, moves to `3_Verified/`),
   Further Inspection (moves to `2_Further_Inspection/`), or Return to User
   (stays put, shows up in the creator's **Returned Entry** tab).
   Admins cannot verify their own entries.
4. **Knowledge Holders** can open and edit entries in `2_Further_Inspection/`
   via **Inspect Existing Entries**.
5. **Prepare for DSpace** (admin) — runs SAFBuilder on `3_Verified/`, keeps a
   copy in `4_DSpace_Packages/`, and downloads the zip through the browser
   (to the client's Downloads folder by default).

Each of folders 1–3 keeps a `data.csv` in DSpace Dublin Core format —
dropdowns export their codes (e.g. `BK`), subjects export as
`Theme::Sub Theme::600` joined by `||`.

### Users

- **Levels**: `user` and `admin`. **Types**: `Lab Member` and
  `Knowledge Holder` (Knowledge Holders can see Folder 2 entries).
- A hidden permanent admin exists for recovery: username `admin`
  (recovery password is set in `src/digitization_manager/auth.py`).
  It cannot be edited or deleted.
- Admins add/delete users and reset passwords under **User Settings**.
  Users change their own username/password under **Profile Settings**.

## Install

### Linux

```bash
./install.sh
```

The installer checks for and installs everything it needs — `uv` (via the
official installer), plus `tesseract`, `ghostscript`, and `java` for OCR and
SAF packaging. On Linux it uses **nala** (a friendlier apt frontend —
coloured output, faster, same repositories) and falls back to `apt-get` if
nala isn't present. You may be asked for your `sudo` password.

This creates the `digitization_manager` command, a `.desktop` launcher with
the app icon, and installs into `~/.local/share/digitization_manager`.

### macOS

Easiest: download the folder, then **double-click
`Install OTEKH Digitization Manager.command`**. It opens Terminal and runs
the installer for you. If macOS blocks it ("unidentified developer"),
right-click the file → **Open** → **Open** again.

Or from Terminal:

```bash
./install.sh
```

The installer installs `uv`, `tesseract`, `ghostscript`, and `openjdk` via
Homebrew if they're missing (installs Homebrew-dependent packages only;
Homebrew itself must be present — get it from https://brew.sh).

Both create `digitization_manager` plus `OTEKH Digitization Manager.app` in
`/Applications` (or `~/Applications`).

### Windows

Not built yet — the code is structured for it (Python + browser UI), but
install scripts and testing are Linux/macOS only for now.

## Run

```bash
digitization_manager            # starts server on :8000, opens a browser
digitization_manager --port 8080 --no-browser
digitization_manager --help
```

On the server machine, turn it on each morning; lab machines browse to the
printed `http://<lan-ip>:8000` address.

## Update / Uninstall

```bash
./update.sh                  # re-install from this folder
digitization_manager --update

./uninstall.sh               # full uninstall (keeps your archive folder)
./uninstall.sh --partial     # remove only the command + desktop icon
./uninstall.sh --purge       # full uninstall AND delete the archive folder
digitization_manager --uninstall
digitization_manager --uninstall-partial
```

Every script and the `digitization_manager` command support `-h` / `--help`.

## Data layout

Everything lives in `~/Documents/OTEKH Digitization Manager/` (override with
the `DIGIMGR_DATA` env var) so the archive can be moved to another drive or
machine:

```
1_Finalized/           files + data.csv awaiting admin review
2_Further_Inspection/  files + data.csv for knowledge-holder inspection
3_Verified/            files + data.csv ready for DSpace
4_DSpace_Packages/     SAF zips from Prepare for DSpace
entries.sqlite         entry state/history (data.csv files are the archive record)
auth.json              user accounts (hashed passwords)
components.csv         dropdown source data — edit to change menus
```

## Editing dropdown options

Edit `components.csv` in the archive folder (or `data/components.csv` in the
project before install). Columns are dropdowns; `CODE, Description` values
show the description and export the code. `Sub1`–`Sub15` columns belong to
the Theme column by position.

## Project layout

```
src/digitization_manager/   Python package (Flask app, store, CSV, OCR, SAF)
  templates/                Jinja HTML (OTKEH shell markup)
  static/                   OTEKH tokens/components CSS, fonts, app.css/js
data/components.csv         dropdown source data
data/bulk_csv_reference.csv reference for the DSpace CSV format
SAFBuilder/                 bundled SAFBuilder (Java) for Prepare for DSpace
shell/                      copy of the OTEKH App Shell design system
install.sh / update.sh / uninstall.sh
```
