"""User accounts, stored in auth.json inside the data root.

Passwords are stored as salted hashes (werkzeug). The hidden 'admin' account
is a permanent backdoor: it is seeded on first run, never shown in the user
list, and cannot be edited or deleted from the UI.

User shape:
    {"username": str, "password_hash": str,
     "level": "user" | "admin",
     "type": "lab_member" | "knowledge_holder",
     "hidden": bool}
"""
import json
import secrets

from werkzeug.security import check_password_hash, generate_password_hash

from . import paths

# Permanent backdoor account (per spec: not changeable).
ADMIN_USERNAME = "admin"


def _admin_password() -> str:
    """Recovery-admin password, kept outside the repo in the data root.

    install.sh prompts for it on first install and writes
    admin_password.txt. If the file is missing (dev checkout, or an
    install that predates the prompt), a random password is generated
    and written there — no secret ever lives in source control.
    Editing the file and restarting the app resets the password.
    """
    f = paths.data_root() / "admin_password.txt"
    if f.exists():
        pw = f.read_text().strip()
        if pw:
            return pw
    pw = secrets.token_urlsafe(12)
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(pw + "\n")
    try:
        f.chmod(0o600)
    except OSError:
        pass
    print(f"[auth] generated recovery admin password -> {f}")
    return pw


def _load() -> dict:
    f = paths.auth_file()
    if not f.exists():
        return {"users": []}
    return json.loads(f.read_text())


def _save(data: dict) -> None:
    f = paths.auth_file()
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(data, indent=2))


def seed_admin() -> None:
    """Create the hidden admin account if missing; keep its password in sync.

    The account can't be edited through the UI, so its stored hash should
    always match the password in admin_password.txt — editing that file
    and restarting resets the password on existing installs.
    """
    password = _admin_password()
    data = _load()
    for u in data["users"]:
        if u["username"] == ADMIN_USERNAME:
            if not check_password_hash(u["password_hash"], password):
                u["password_hash"] = generate_password_hash(password)
                _save(data)
            return
    data["users"].append(
        {
            "username": ADMIN_USERNAME,
            "password_hash": generate_password_hash(password),
            "level": "admin",
            "type": "knowledge_holder",
            "hidden": True,
        }
    )
    _save(data)


def get_user(username: str) -> dict | None:
    for u in _load()["users"]:
        if u["username"] == username:
            return u
    return None


def verify(username: str, password: str) -> dict | None:
    u = get_user(username)
    if u and check_password_hash(u["password_hash"], password):
        return u
    return None


def list_users() -> list[dict]:
    """All non-hidden users (for the admin user-settings screen)."""
    return [u for u in _load()["users"] if not u.get("hidden")]


def add_user(username: str, password: str, level: str, utype: str) -> str | None:
    """Returns an error string, or None on success."""
    username = username.strip()
    if not username:
        return "Username is required."
    if not password:
        return "Password is required."
    if level not in ("user", "admin"):
        return "Level must be 'user' or 'admin'."
    if utype not in ("lab_member", "knowledge_holder"):
        return "Type must be 'lab_member' or 'knowledge_holder'."
    data = _load()
    if any(u["username"] == username for u in data["users"]):
        return "That username is already taken."
    data["users"].append(
        {
            "username": username,
            "password_hash": generate_password_hash(password),
            "level": level,
            "type": utype,
            "hidden": False,
        }
    )
    _save(data)
    return None


def delete_user(username: str) -> None:
    data = _load()
    data["users"] = [
        u for u in data["users"] if u["username"] != username or u.get("hidden")
    ]
    _save(data)


def update_user(
    username: str,
    new_username: str | None = None,
    new_password: str | None = None,
    level: str | None = None,
    utype: str | None = None,
) -> str | None:
    """Edit a user. Hidden accounts refuse all changes. Returns error or None."""
    data = _load()
    for u in data["users"]:
        if u["username"] != username:
            continue
        if u.get("hidden"):
            return "This account cannot be modified."
        if new_username and new_username.strip() != username:
            new_username = new_username.strip()
            if any(x["username"] == new_username for x in data["users"]):
                return "That username is already taken."
            u["username"] = new_username
        if new_password:
            u["password_hash"] = generate_password_hash(new_password)
        if level in ("user", "admin"):
            u["level"] = level
        if utype in ("lab_member", "knowledge_holder"):
            u["type"] = utype
        _save(data)
        return None
    return "User not found."
