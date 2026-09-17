"""OCR PDFs in place via ocrmypdf (adapted from Bulk_Upload_Zip_Creator).

Runs when an admin verifies an entry: every PDF attached to the entry is
OCR'd before the files move to 3_Verified. Requires tesseract and
ghostscript on the server machine.
"""
import os          # os.replace for atomic in-place PDF swaps
import re          # scraping ocrmypdf's 'NN%' progress output
import shutil      # shutil.which to detect tesseract/ghostscript
import subprocess  # running ocrmypdf as a child process
import sys         # sys.executable -> run ocrmypdf in this venv
import tempfile    # temp output file beside the source PDF
import threading   # background job threads + the jobs lock
import uuid        # job IDs
from pathlib import Path


def _is_pdf(path: Path) -> bool:
    """Check the %PDF- magic bytes (more reliable than the extension)."""
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


def has_text_layer(pdf: Path) -> bool:
    """True only if EVERY page has extractable text (already OCR'd).

    Any page without text -> False -> OCR runs. Unreadable files also
    return False so we err on the side of running OCR.
    """
    try:
        from pypdf import PdfReader

        reader = PdfReader(str(pdf))
        if len(reader.pages) == 0:
            return False
        for page in reader.pages:
            if not (page.extract_text() or "").strip():
                return False
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Async OCR jobs (progress tracking for the verify modal)
# ---------------------------------------------------------------------------

# In-memory job table: job_id -> status dict. Lives only while the
# server runs; jobs are short-lived so nothing needs persisting.
_JOBS: dict[str, dict] = {}
_JOBS_LOCK = threading.Lock()


def get_job(job_id: str) -> dict | None:
    """Snapshot of a job's status dict for the polling route."""
    with _JOBS_LOCK:
        job = _JOBS.get(job_id)
        return dict(job) if job else None


def start_ocr_job(entry_id: str, by: str) -> str:
    """Start a background OCR job for an entry. Returns the job id.

    Job statuses: running -> done (some files OCR'd) | skipped (all PDFs
    already had text / no PDFs) | error.
    """
    job_id = uuid.uuid4().hex[:12]
    with _JOBS_LOCK:
        _JOBS[job_id] = {
            "id": job_id,
            "entry_id": entry_id,
            "by": by,
            "status": "running",
            "total": 0,
            "index": 0,
            "current": "",
            "pct": None,
            "ocred": [],
            "skipped": [],
            "error": "",
        }
    threading.Thread(target=_run_job, args=(job_id,), daemon=True).start()
    return job_id


def _set(job_id: str, **kw) -> None:
    """Thread-safe update of job fields from the worker thread."""
    with _JOBS_LOCK:
        if job_id in _JOBS:
            _JOBS[job_id].update(kw)


def _run_job(job_id: str) -> None:
    """Worker: walk the entry's PDFs, skip ones that already have a
    text layer, OCR the rest with live progress, then mark the job
    done / skipped / error for the modal to pick up."""
    from . import store  # lazy: avoid import cycle at module load

    job = get_job(job_id)
    try:
        entry = store.get_entry(job["entry_id"])
        directory = store.entry_dir(entry)
        pdfs = [
            n
            for n in entry["files"]
            if (directory / n).is_file() and _is_pdf(directory / n)
        ]
        _set(job_id, total=len(pdfs))
        tools_ok = False
        ocred, skipped = [], []
        for i, name in enumerate(pdfs, 1):
            _set(job_id, index=i, current=name, pct=None)
            p = directory / name
            if has_text_layer(p):
                skipped.append(name)
                continue
            if not tools_ok:
                err = check_requirements()
                if err:
                    raise RuntimeError(err)
                tools_ok = True
            _ocr_pdf_progress(p, job_id)
            ocred.append(name)
        _set(
            job_id,
            ocred=ocred,
            skipped=skipped,
            status="done" if ocred else "skipped",
        )
    except Exception as exc:
        _set(job_id, status="error", error=str(exc))


def _ocr_pdf_progress(pdf: Path, job_id: str) -> None:
    """ocrmypdf one PDF in place, streaming its stderr progress bar into
    the job's pct field (best-effort; tqdm writes 'NN%' updates)."""
    fd, tmp_name = tempfile.mkstemp(suffix=".pdf", dir=str(pdf.parent))
    os.close(fd)
    tmp = Path(tmp_name)
    try:
        proc = subprocess.Popen(
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
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
        )
        buf = ""
        while True:
            ch = proc.stderr.read(1)
            if not ch:
                break
            buf += ch
            if len(buf) > 4000:
                buf = buf[-2000:]
            m = re.findall(r"(\d+)%", buf)
            if m:
                _set(job_id, pct=int(m[-1]))
        proc.wait()
        if proc.returncode != 0:
            tail = "\n".join(buf.splitlines()[-20:])
            raise RuntimeError(f"OCR failed for {pdf.name}:\n{tail}")
        os.replace(tmp, pdf)
    except Exception:
        tmp.unlink(missing_ok=True)
        raise
