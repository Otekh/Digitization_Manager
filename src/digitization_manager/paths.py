"""Filesystem locations for the app's working archive.

Everything the app produces lives under one root so the whole archive can be
moved to another drive or machine without breaking anything.

Default root:  ~/Documents/OTEKH Digitization Manager/
Override with the DIGIMGR_DATA environment variable.
"""
import os
from pathlib import Path

APP_DIR_NAME = "OTEKH Digitization Manager"

# Status name -> folder name inside the data root.
FOLDERS = {
    "finalized": "1_Finalized",
    "inspection": "2_Further_Inspection",
    "verified": "3_Verified",
    "packages": "4_DSpace_Packages",
}


def data_root() -> Path:
    override = os.environ.get("DIGIMGR_DATA")
    if override:
        return Path(override).expanduser()
    return Path.home() / "Documents" / APP_DIR_NAME


def folder(status: str) -> Path:
    return data_root() / FOLDERS[status]


def auth_file() -> Path:
    return data_root() / "auth.json"


def db_file() -> Path:
    return data_root() / "entries.sqlite"


def ensure_data_dirs() -> Path:
    root = data_root()
    for name in FOLDERS.values():
        (root / name).mkdir(parents=True, exist_ok=True)
    return root


def package_root() -> Path:
    """Directory containing the installed/source package."""
    return Path(__file__).resolve().parent


def project_root() -> Path:
    """Project root when running from the source tree (src layout)."""
    return Path(__file__).resolve().parents[2]


def components_csv() -> Path:
    """Dropdown source data. Installed copy first, then source-tree copy."""
    installed = data_root() / "components.csv"
    if installed.exists():
        return installed
    return project_root() / "data" / "components.csv"


def safbuilder_jar() -> Path:
    return project_root() / "SAFBuilder" / "target" / "safbuilder-1.6.jar"
