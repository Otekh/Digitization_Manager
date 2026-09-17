"""Run SAFBuilder on 3_Verified to produce a zipped DSpace SAF package.

The bundled safbuilder.sh needs Maven to recompile each run; instead we call
the pre-built shaded jar directly:

    java -cp safbuilder-1.6.jar safbuilder.BatchProcess -c <csv> -o <name> -z

SAFBuilder writes <name>.zip next to the input CSV; we move it into
4_DSpace_Packages.
"""
import json        # manifest written beside each zip
import random      # package ID generation
import shutil      # moving the zip + checking for java
import string      # package ID alphabet
import subprocess  # running the SAFBuilder jar
from datetime import datetime  # package name timestamp + manifest
from pathlib import Path

from . import paths  # archive folders + jar location


def _package_id() -> str:
    """6-char unique ID: three digits + three lowercase letters, shuffled.
    e.g. '68fgh7'."""
    chars = random.sample(string.digits, 3) + random.sample(string.ascii_lowercase, 3)
    random.shuffle(chars)
    return "".join(chars)


def _java_bin() -> str:
    """Locate a real java binary.

    macOS ships a /usr/bin/java stub that passes shutil.which but errors
    at runtime when no JDK is installed, and brew's openjdk is keg-only
    (not on PATH) — so check the brew opt dirs first, then PATH.
    """
    candidates = [
        "/opt/homebrew/opt/openjdk/bin/java",  # brew, Apple Silicon
        "/usr/local/opt/openjdk/bin/java",     # brew, Intel
        shutil.which("java") or "",
    ]
    for c in candidates:
        if c and Path(c).exists():
            return c
    raise RuntimeError("java is not installed on the server.")


def run_safbuilder(dest_dir: Path | None = None) -> Path:
    """Build a SAF zip from 3_Verified into dest_dir (default: Folder 4).
    Returns the zip path."""
    jar = paths.safbuilder_jar()
    if not jar.exists():
        raise FileNotFoundError(f"SAFBuilder jar not found at {jar}")
    java = _java_bin()

    src = paths.folder("verified")
    csv_path = src / "data.csv"
    if not csv_path.exists():
        raise FileNotFoundError("3_Verified has no data.csv (no verified entries).")

    # Record which entries are going into this package (for the manifest).
    from . import csv_export, store  # lazy: store imports csv_export, keep cycles out
    verified = store.list_entries("verified")
    entry_titles = [e["metadata"].get("title", "") for e in verified]

    out_name = f"{_package_id()}_saf_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    result = subprocess.run(
        [
            java,
            "-cp",
            str(jar),
            "safbuilder.BatchProcess",
            "-c",
            str(csv_path.resolve()),
            "-o",
            out_name,
            "-z",
        ],
        cwd=str(jar.parent.parent),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"SAFBuilder failed (code {result.returncode}):\n"
            f"{result.stderr or result.stdout}"
        )

    # SAFBuilder drops the zip (and an unzipped dir) beside the input CSV.
    zip_path = src / f"{out_name}.zip"
    if not zip_path.exists():
        raise FileNotFoundError(
            f"SAFBuilder finished but {zip_path.name} was not created.\n"
            f"{result.stdout}"
        )

    if dest_dir is None:
        dest_dir = paths.folder("packages")
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / zip_path.name
    shutil.move(str(zip_path), str(dest))
    shutil.rmtree(src / out_name, ignore_errors=True)  # unzipped SAF dir

    # Master CSV: flip these entries' rows to saf=yes. The verified
    # rows are purged right after this returns; master.csv is the
    # lasting record that they were packaged.
    csv_export.mark_packaged(verified)

    # Manifest beside the zip: lets the SAF DSpace Folder tab list which
    # entries are inside each package.
    manifest = {
        "name": dest.name,
        "created": datetime.now().isoformat(timespec="seconds"),
        "entries": entry_titles,
    }
    (dest_dir / f"{dest.stem}.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    return dest
