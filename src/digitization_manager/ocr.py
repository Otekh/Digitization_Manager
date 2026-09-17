"""OCR PDFs in place via ocrmypdf (adapted from Bulk_Upload_Zip_Creator).

Runs when an admin verifies an entry: every PDF attached to the entry is
OCR'd before the files move to 3_Verified. Requires tesseract and
ghostscript on the server machine.
"""
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def _is_pdf(path: Path) -> bool:
    try:
        with path.open("rb") as f:
            return f.read(5) == b"%PDF-"
    except OSError:
        return False


def check_requirements() -> str | None:
    """Returns an error string if OCR tools are missing, else None."""
    if not shutil.which("tesseract"):
        return "tesseract is not installed on the server."
    if not shutil.which("gs") and not shutil.which("ghostscript"):
        return "ghostscript is not installed on the server."
    return None


def ocr_pdf(pdf: Path) -> None:
    """OCR one PDF in place, keeping the original file name."""
    fd, tmp_name = tempfile.mkstemp(suffix=".pdf", dir=str(pdf.parent))
    os.close(fd)
    tmp = Path(tmp_name)
    try:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "ocrmypdf",
                "--force-ocr",
                "--continue-on-soft-render-error",
                "--language",
                "eng",
                str(pdf),
                str(tmp),
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            tail = "\n".join((result.stdout or "").splitlines()[-20:])
            raise RuntimeError(f"OCR failed for {pdf.name}:\n{tail}")
        os.replace(tmp, pdf)
    except Exception:
        tmp.unlink(missing_ok=True)
        raise


def ocr_entry_files(directory: Path, filenames: list[str]) -> list[str]:
    """OCR every PDF in the list. Returns names of files that were OCR'd."""
    done = []
    for name in filenames:
        p = directory / name
        if p.is_file() and _is_pdf(p):
            ocr_pdf(p)
            done.append(name)
    return done
