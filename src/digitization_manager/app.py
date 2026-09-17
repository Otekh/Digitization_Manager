"""Flask app: routes, session auth, validation, and workflow actions.

Run model: one lab machine runs this server; everyone connects over the LAN
with a browser. All state lives under the data root (see paths.py).
"""
import functools
import json
import re
import secrets
from datetime import datetime
from pathlib import Path

from flask import (
    Flask,
    abort,
    flash,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
)
from werkzeug.utils import secure_filename

from . import APP_NAME, __version__, auth, ocr, options, paths, safbuilder, store

DATE_FORMATS = {
    "year": ("Year only (YYYY)", re.compile(r"^\d{4}$")),
    "month_year": ("Month/Year (MM/YYYY)", re.compile(r"^\d{2}/\d{4}$")),
    "full": ("Full (DD/MM/YYYY)", re.compile(r"^\d{2}/\d{2}/\d{4}$")),
    "unknown": ("Unknown", None),
}

STATUS_LABELS = {
    "finalized": "Finalized",
    "inspection": "Further Inspection",
    "verified": "Verified",
    "returned": "Returned",
}


# ---------------------------------------------------------------- app setup

def create_app() -> Flask:
    app = Flask(__name__)
    paths.ensure_data_dirs()
    auth.seed_admin()
    store.init_db()
    app.secret_key = _secret_key()
    return app


def _secret_key() -> str:
    """Persistent session secret, generated once into the data root."""
    f = paths.data_root() / ".secret_key"
    if not f.exists():
        f.write_text(secrets.token_hex(32))
    return f.read_text().strip()


# ---------------------------------------------------------------- helpers

def current_user() -> dict | None:
    username = session.get("username")
    return auth.get_user(username) if username else None


def login_required(view):
    @functools.wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user():
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


def admin_required(view):
    @functools.wraps(view)
    def wrapped(*args, **kwargs):
        u = current_user()
        if not u:
            return redirect(url_for("login"))
        if u["level"] != "admin":
            abort(403)
        return view(*args, **kwargs)
    return wrapped


def knowledge_holder_required(view):
    @functools.wraps(view)
    def wrapped(*args, **kwargs):
        u = current_user()
        if not u:
            return redirect(url_for("login"))
        if u["type"] != "knowledge_holder":
            abort(403)
        return view(*args, **kwargs)
    return wrapped


def _valid_date(fmt: str, value: str) -> bool:
    if fmt == "unknown":
        return True
    pattern = DATE_FORMATS[fmt][1]
    if not pattern.match(value):
        return False
    try:
        if fmt == "year":
            datetime.strptime(value, "%Y")
        elif fmt == "month_year":
            datetime.strptime(value, "%m/%Y")
        else:
            datetime.strptime(value, "%d/%m/%Y")
    except ValueError:
        return False
    return True


def validate_metadata(form) -> tuple[dict, list[str], set[str]]:
    """Read the entry form into a metadata dict.

    Returns (metadata, errors, error_fields) where error_fields holds the
    form field names that failed, so the template can flag them.
    """
    errors: list[str] = []
    error_fields: set[str] = set()
    opts = options.load_options()

    def field(name, label, required=True):
        v = form.get(name, "").strip()
        if required and not v:
            errors.append(f"{label} is required.")
            error_fields.add(name)
        return v

    def dropdown(name, label, column):
        v = field(name, label)
        if v and v != "Unknown":
            valid = {o["label"] for o in opts["fields"].get(column, [])}
            if v not in valid:
                errors.append(f"{label}: '{v}' is not a valid option.")
                error_fields.add(name)
        return v

    title = field("title", "Document Title")
    file_name = field("file_name", "File Name")
    if file_name and ("/" in file_name or "\\" in file_name or file_name.startswith(".")):
        errors.append("File Name must not contain slashes or start with a dot.")
        error_fields.add("file_name")

    location = dropdown("location", "Location", "Location")
    media_type = dropdown("media_type", "Media Type", "Media Type")
    equipment_id = dropdown("equipment_id", "Equipment ID", "Equipment ID")
    collection_source = dropdown(
        "collection_source", "Collection Source", "Collection, Source"
    )
    era = dropdown("era", "Era", "Era")
    access_control = dropdown("access_control", "Access Control", "Access Control")
    ai_trainable = dropdown("ai_trainable", "AI Trainable", "AI Trainable")

    lineage = field("lineage", "Lineage, Provenance")

    date_format = form.get("date_format", "")
    if date_format not in DATE_FORMATS:
        errors.append("Date Created: choose a date format.")
        error_fields.add("date_format")
        date_value = ""
    elif date_format == "unknown":
        date_value = "Unknown"
    else:
        date_value = form.get("date_value", "").strip()
        if not date_value:
            errors.append("Date Created: enter a date or choose Unknown.")
            error_fields.add("date_value")
        elif not _valid_date(date_format, date_value):
            errors.append(
                f"Date Created: '{date_value}' does not match "
                f"{DATE_FORMATS[date_format][0]}."
            )
            error_fields.add("date_value")

    # Theme/Sub-theme pairs (parallel form arrays).
    themes = form.getlist("theme")
    subs = form.getlist("sub")
    subjects = []
    valid_subs = opts["subthemes"]
    for t, s in zip(themes, subs):
        t, s = t.strip(), s.strip()
        if not t and not s:
            continue
        if t != "Unknown" and t not in opts["themes"]:
            errors.append(f"Theme: '{t}' is not a valid option.")
            error_fields.add("theme")
            continue
        if s and s != "Unknown" and t != "Unknown" and s not in valid_subs.get(t, []):
            errors.append(f"Sub Theme: '{s}' is not valid for theme '{t}'.")
            error_fields.add("sub")
            continue
        subjects.append({"theme": t, "sub": s})
    if not subjects:
        errors.append("Add at least one Theme.")
        error_fields.add("theme")

    summary = form.get("summary", "").strip()
    if len(summary) < 50:
        errors.append(
            f"Summary must be at least 50 characters (currently {len(summary)})."
        )
        error_fields.add("summary")

    metadata = {
        "title": title,
        "file_name": file_name,
        "location": location,
        "media_type": media_type,
        "equipment_id": equipment_id,
        "date_format": date_format,
        "date_value": date_value,
        "collection_source": collection_source,
        "lineage": lineage,
        "era": era,
        "subjects": subjects,
        "access_control": access_control,
        "ai_trainable": ai_trainable,
        "summary": summary,
    }
    return metadata, errors, error_fields


def save_uploads(file_storage_list, base_name: str, dest_dir: Path) -> list[str]:
    """Save uploaded files as base.ext, base_2.ext, ... avoiding collisions."""
    saved = []
    existing = {p.name for p in dest_dir.iterdir()} if dest_dir.exists() else set()
    n = 0
    for fs in file_storage_list:
        if not fs or not fs.filename:
            continue
        ext = Path(secure_filename(fs.filename)).suffix
        n += 1
        name = f"{base_name}{ext}" if n == 1 else f"{base_name}_{n}{ext}"
        while name in existing:
            n += 1
            name = f"{base_name}_{n}{ext}"
        fs.save(dest_dir / name)
        existing.add(name)
        saved.append(name)
    return saved


# Metadata fields that can be red-flagged on review (key, label).
FLAGGABLE_FIELDS = [
    ("title", "Document Title"),
    ("file_name", "File Name"),
    ("location", "Location"),
    ("media_type", "Media Type"),
    ("equipment_id", "Equipment ID"),
    ("date_value", "Date Created"),
    ("collection_source", "Collection Source"),
    ("lineage", "Lineage, Provenance"),
    ("era", "Era"),
    ("subjects", "Theme / Sub Theme"),
    ("access_control", "Access Control"),
    ("ai_trainable", "AI Trainable"),
    ("summary", "Summary"),
    ("files", "Files"),
]


def _collect_flags(form) -> dict:
    """Read flag toggles + their per-field reasons (max 50 chars) from a form."""
    valid = dict(FLAGGABLE_FIELDS)
    return {
        k: form.get(f"flag_reason_{k}", "").strip()[:50]
        for k in form.getlist("flag")
        if k in valid
    }


def _form_context(entry: dict | None = None, error_fields: set | None = None) -> dict:
    opts = options.load_options()
    return {
        "opts": opts,
        "date_formats": DATE_FORMATS,
        "entry": entry,
        "m": entry["metadata"] if entry else {},
        "error_fields": error_fields or set(),
        "flaggable": FLAGGABLE_FIELDS,
        "flagged": dict(entry["flags"]) if entry else {},
        # Knowledge holders flag fields while editing an inspection entry.
        "can_flag": bool(
            entry and entry["status"] == "inspection"
            and current_user() and current_user()["type"] == "knowledge_holder"
        ),
    }


# ---------------------------------------------------------------- routes

app = create_app()


@app.context_processor
def inject_globals():
    u = current_user()
    c = store.counts() if u else {}
    my_returned = 0
    if u:
        my_returned = sum(
            1 for e in store.list_entries("returned")
            if e["created_by"] == u["username"]
        )
    return {
        "app_name": APP_NAME,
        "version": __version__,
        "user": u,
        "counts": c,
        "my_returned": my_returned,
        "status_labels": STATUS_LABELS,
        "flag_labels": dict(FLAGGABLE_FIELDS),
    }


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = auth.verify(
            request.form.get("username", ""), request.form.get("password", "")
        )
        if u:
            session["username"] = u["username"]
            return redirect(url_for("new_entry"))
        flash("Invalid username or password.", "error")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
@login_required
def index():
    return redirect(url_for("new_entry"))


# ------------------------------------------------------------- entry form

@app.route("/entry/new", methods=["GET", "POST"])
@login_required
def new_entry():
    if request.method == "POST":
        action = request.form.get("action")
        if action not in ("finalized", "inspection"):
            abort(400)
        metadata, errors, error_fields = validate_metadata(request.form)
        uploads = request.files.getlist("files")
        uploads = [f for f in uploads if f and f.filename]
        if not uploads:
            errors.append("Upload at least one file.")
            error_fields.add("files")
        if errors:
            for e in errors:
                flash(e, "error")
            ctx = _form_context(error_fields=error_fields)
            ctx["m"] = metadata  # keep everything the user typed
            return render_template("entry_form.html", **ctx), 400

        dest = paths.folder(action)
        files = save_uploads(uploads, metadata["file_name"], dest)
        store.create_entry(metadata, files, current_user()["username"], action)
        flash(f"Entry saved to {STATUS_LABELS[action]}.", "ok")
        return redirect(url_for("new_entry"))
    return render_template("entry_form.html", **_form_context())


@app.route("/entry/<entry_id>/edit", methods=["GET", "POST"])
@login_required
def edit_entry(entry_id):
    u = current_user()
    entry = store.get_entry(entry_id)
    if not entry:
        abort(404)
    # Creator edits returned entries; knowledge holders edit inspection entries.
    can_edit = (entry["status"] == "returned" and entry["created_by"] == u["username"]) or (
        entry["status"] == "inspection" and u["type"] == "knowledge_holder"
    )
    if not can_edit:
        abort(403)

    if request.method == "POST":
        action = request.form.get("action")
        metadata, errors, error_fields = validate_metadata(request.form)

        # Files: keep existing (minus removals), add new uploads.
        kept = [
            f for f in entry["files"]
            if f not in request.form.getlist("remove_file")
        ]
        uploads = [f for f in request.files.getlist("files") if f and f.filename]
        if not kept and not uploads:
            errors.append("Entry must have at least one file.")
            error_fields.add("files")
        if errors:
            for e in errors:
                flash(e, "error")
            ctx = _form_context(entry, error_fields=error_fields)
            ctx["m"] = metadata
            return render_template("entry_form.html", **ctx), 400

        entry_dir = store.entry_dir(entry)
        # Delete removed files from disk.
        for name in entry["files"]:
            if name not in kept:
                (entry_dir / name).unlink(missing_ok=True)
        new_files = kept + save_uploads(
            uploads, metadata["file_name"], entry_dir
        )
        store.update_metadata(entry_id, metadata, new_files, u["username"])

        if entry["status"] == "inspection":
            # Expert review: any flag -> return to creator (keeping the
            # expert's edits); no flags -> finalize back to admin review.
            flags = _collect_flags(request.form)
            if flags:
                store.change_status(
                    entry_id, "returned", u["username"],
                    note=request.form.get("note", ""), flags=flags,
                )
                flash("Entry returned to its creator with your changes.", "ok")
            else:
                store.change_status(entry_id, "finalized", u["username"])
                flash("Entry finalized and sent back to Verify Entries.", "ok")
            return redirect(url_for("inspect"))

        if action in ("finalized", "inspection") and entry["status"] == "returned":
            store.change_status(entry_id, action, u["username"])
            flash(f"Entry resubmitted to {STATUS_LABELS[action]}.", "ok")
            return redirect(url_for("returned_entries"))
        flash("Entry updated.", "ok")
        return redirect(url_for("entry_detail", entry_id=entry_id))

    return render_template("entry_form.html", **_form_context(entry))


# ------------------------------------------------------------------ queues

@app.route("/returned")
@login_required
def returned_entries():
    u = current_user()
    entries = [
        e for e in store.list_entries("returned")
        if e["created_by"] == u["username"]
    ]
    for e in entries:
        e["return_note"] = store.return_note(e)
    return render_template(
        "list.html", title="Returned Entries", entries=entries, mode="returned"
    )


@app.route("/review")
@admin_required
def review():
    entries = store.list_entries("finalized")
    return render_template(
        "list.html", title="Review Entries", entries=entries, mode="review"
    )


@app.route("/inspect")
@knowledge_holder_required
def inspect():
    entries = store.list_entries("inspection")
    return render_template(
        "list.html", title="Inspect Existing Entries", entries=entries, mode="inspect"
    )


@app.route("/verified")
@admin_required
def verified_entries():
    entries = store.list_entries("verified")
    return render_template(
        "list.html", title="View Verified Entries", entries=entries, mode="verified"
    )


@app.route("/entry/<entry_id>")
@login_required
def entry_detail(entry_id):
    u = current_user()
    entry = store.get_entry(entry_id)
    if not entry:
        abort(404)
    # Folder 2 entries are restricted to knowledge holders.
    if entry["status"] == "inspection" and u["type"] != "knowledge_holder":
        abort(403)
    return render_template(
        "entry_detail.html", entry=entry,
        return_note=store.return_note(entry),
        flaggable=FLAGGABLE_FIELDS,
        flagged=entry["flags"],
        # Admins flag fields on the detail page before returning.
        can_flag=(
            u["level"] == "admin"
            and entry["status"] in ("finalized", "inspection", "verified")
        ),
    )


@app.route("/entry/<entry_id>/file/<path:filename>")
@login_required
def entry_file(entry_id, filename):
    u = current_user()
    entry = store.get_entry(entry_id)
    if not entry or filename not in entry["files"]:
        abort(404)
    if entry["status"] == "inspection" and u["type"] != "knowledge_holder":
        abort(403)
    return send_from_directory(
        store.entry_dir(entry), filename, as_attachment=False
    )


# ------------------------------------------------------------ admin actions

@app.route("/entry/<entry_id>/verify", methods=["POST"])
@admin_required
def verify_entry(entry_id):
    u = current_user()
    entry = store.get_entry(entry_id)
    if not entry or entry["status"] not in ("finalized", "inspection"):
        abort(404)
    if entry["created_by"] == u["username"]:
        flash("You cannot verify your own entry. Another admin must do it.", "error")
        return redirect(url_for("entry_detail", entry_id=entry_id))

    err = ocr.check_requirements()
    if err:
        flash(err, "error")
        return redirect(url_for("entry_detail", entry_id=entry_id))
    try:
        done = ocr.ocr_entry_files(store.entry_dir(entry), entry["files"])
    except RuntimeError as exc:
        flash(str(exc), "error")
        return redirect(url_for("entry_detail", entry_id=entry_id))
    if done:
        flash(f"OCR complete: {', '.join(done)}", "ok")

    store.change_status(entry_id, "verified", u["username"], verified_by=u["username"])
    flash("Entry verified and moved to 3_Verified.", "ok")
    return redirect(url_for("review"))


@app.route("/entry/<entry_id>/verify_start", methods=["POST"])
@admin_required
def verify_start(entry_id):
    """Start a background OCR job; the detail page polls ocr_status."""
    u = current_user()
    entry = store.get_entry(entry_id)
    if not entry or entry["status"] not in ("finalized", "inspection"):
        abort(404)
    if entry["created_by"] == u["username"]:
        return {"error": "You cannot verify your own entry. Another admin must do it."}, 403
    return {"job_id": ocr.start_ocr_job(entry_id, u["username"])}


@app.route("/ocr_status/<job_id>")
@admin_required
def ocr_status(job_id):
    job = ocr.get_job(job_id)
    if not job:
        abort(404)
    return job


@app.route("/entry/<entry_id>/verify_commit/<job_id>", methods=["POST"])
@admin_required
def verify_commit(entry_id, job_id):
    """Finish verification after the OCR job completes (or was skipped)."""
    u = current_user()
    job = ocr.get_job(job_id)
    if not job or job["entry_id"] != entry_id or job["status"] not in ("done", "skipped"):
        abort(400)
    entry = store.get_entry(entry_id)
    if not entry or entry["status"] not in ("finalized", "inspection"):
        abort(404)
    store.change_status(entry_id, "verified", u["username"], verified_by=u["username"])
    if job["ocred"]:
        flash(f"OCR complete: {', '.join(job['ocred'])}", "ok")
    if job["skipped"]:
        flash(f"Already had a text layer (OCR skipped): {', '.join(job['skipped'])}", "ok")
    flash("Entry verified and moved to 3_Verified.", "ok")
    return {"ok": True, "redirect": url_for("review")}


@app.route("/entry/<entry_id>/inspect_move", methods=["POST"])
@admin_required
def inspect_move(entry_id):
    entry = store.get_entry(entry_id)
    if not entry or entry["status"] != "finalized":
        abort(404)
    store.change_status(
        entry_id, "inspection", current_user()["username"],
        note=request.form.get("note", ""),
    )
    flash("Entry moved to 2_Further_Inspection.", "ok")
    return redirect(url_for("review"))


@app.route("/entry/<entry_id>/return", methods=["POST"])
@admin_required
def return_entry(entry_id):
    entry = store.get_entry(entry_id)
    if not entry or entry["status"] not in ("finalized", "inspection", "verified"):
        abort(404)
    was_verified = entry["status"] == "verified"
    flags = _collect_flags(request.form)
    store.change_status(
        entry_id, "returned", current_user()["username"],
        note=request.form.get("note", ""), flags=flags,
    )
    flash("Entry returned to its creator.", "ok")
    return redirect(url_for("verified_entries") if was_verified else url_for("review"))


# -------------------------------------------------------- prepare for dspace

@app.route("/prepare", methods=["GET", "POST"])
@admin_required
def prepare():
    if request.method == "POST":
        try:
            # Build into 4_DSpace_Packages (a copy stays in the archive),
            # then send it to the browser - it downloads to the client's
            # Downloads folder via the normal browser save dialog.
            result = safbuilder.run_safbuilder()
            return send_from_directory(
                result.parent, result.name, as_attachment=True
            )
        except Exception as exc:
            flash(str(exc), "error")

    entries = store.list_entries("verified")
    packages = sorted(paths.folder("packages").glob("*.zip"))
    return render_template(
        "prepare.html", entries=entries, packages=packages
    )


# --------------------------------------------------------- saf dspace folder

def _list_packages() -> list[dict]:
    """SAF zips in 4_DSpace_Packages with their manifests (if present)."""
    out = []
    for z in sorted(paths.folder("packages").glob("*.zip")):
        manifest_path = z.with_suffix(".json")
        entries, created = [], None
        if manifest_path.exists():
            try:
                m = json.loads(manifest_path.read_text(encoding="utf-8"))
                entries = m.get("entries", [])
                created = m.get("created")
            except Exception:
                pass
        if not created:
            created = datetime.fromtimestamp(z.stat().st_mtime).isoformat(timespec="seconds")
        out.append({"name": z.name, "created": created, "entries": entries})
    return out


@app.route("/saf-packages")
@admin_required
def saf_packages():
    return render_template("saf_packages.html", packages=_list_packages())


@app.route("/saf-packages/download/<path:name>")
@admin_required
def saf_package_download(name):
    """Re-download a SAF zip from Folder 4 through the browser."""
    target = (paths.folder("packages") / name).resolve()
    if target.parent != paths.folder("packages").resolve() or target.suffix != ".zip":
        abort(400)
    if not target.exists():
        abort(404)
    return send_from_directory(target.parent, target.name, as_attachment=True)


@app.route("/saf-packages/delete", methods=["POST"])
@admin_required
def saf_package_delete():
    name = request.form.get("name", "")
    # Guard: only allow deleting zips that live directly in Folder 4.
    target = (paths.folder("packages") / name).resolve()
    if target.parent != paths.folder("packages").resolve() or target.suffix != ".zip":
        abort(400)
    if not target.exists():
        abort(404)
    target.unlink()
    manifest = target.with_suffix(".json")
    if manifest.exists():
        manifest.unlink()
    flash(f"Deleted {name}.", "ok")
    return redirect(url_for("saf_packages"))


# ------------------------------------------------------------------ account

@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    u = current_user()
    if request.method == "POST":
        new_username = request.form.get("username", "").strip()
        current_pw = request.form.get("current_password", "")
        new_pw = request.form.get("new_password", "")
        if not auth.verify(u["username"], current_pw):
            flash("Current password is incorrect.", "error")
        else:
            err = auth.update_user(
                u["username"],
                new_username=new_username or None,
                new_password=new_pw or None,
            )
            if err:
                flash(err, "error")
            else:
                if new_username:
                    session["username"] = new_username
                flash("Profile updated.", "ok")
                return redirect(url_for("profile"))
    return render_template("profile.html")


@app.route("/users", methods=["GET", "POST"])
@admin_required
def users():
    if request.method == "POST":
        action = request.form.get("action")
        username = request.form.get("username", "")
        if action == "add":
            err = auth.add_user(
                username,
                request.form.get("password", ""),
                request.form.get("level", "user"),
                request.form.get("type", "lab_member"),
            )
            flash(err or f"User '{username}' added.", "error" if err else "ok")
        elif action == "delete":
            auth.delete_user(username)
            flash(f"User '{username}' deleted.", "ok")
        elif action == "reset":
            err = auth.update_user(
                username, new_password=request.form.get("new_password", "")
            )
            flash(err or f"Password reset for '{username}'.", "error" if err else "ok")
        elif action == "edit":
            err = auth.update_user(
                username,
                level=request.form.get("level"),
                utype=request.form.get("type"),
            )
            flash(err or f"User '{username}' updated.", "error" if err else "ok")
        return redirect(url_for("users"))
    return render_template("users.html", users=auth.list_users())
