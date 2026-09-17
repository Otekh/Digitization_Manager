"""Entry point: `digitization_manager` command.

Starts the LAN server on the host machine and opens a browser. Other lab
machines connect to http://<this-machine-ip>:<port> over the wired network.
"""
import argparse    # CLI flags (--port, --update, --uninstall, ...)
import errno       # EADDRINUSE check for the port-in-use message
import subprocess  # running update.sh / uninstall.sh
import sys         # exit codes + stderr
import threading   # delayed browser open
import urllib.request  # probing whether the port already serves this app
import webbrowser  # opening the app URL on the host machine
from pathlib import Path

from . import APP_NAME, __version__, paths


def _open_browser_later(url: str) -> threading.Timer:
    """Open the app URL ~1s after startup so the server is listening
    first. Failures are ignored (headless / icon launches). Returns
    the timer so a failed startup can cancel it."""
    def _open():
        try:
            webbrowser.open(url)
        except Exception:
            pass

    timer = threading.Timer(1.0, _open)
    timer.start()
    return timer


def _app_alive(port: int) -> bool:
    """True if this app is already serving on the port — probes the
    login page. Used when the icon is clicked while the server is
    still running (browser closed but app not shut down)."""
    try:
        with urllib.request.urlopen(
            f"http://127.0.0.1:{port}/login", timeout=2
        ) as r:
            return r.status == 200
    except Exception:
        return False


def _install_config() -> dict:
    """Paths recorded by install.sh in ~/.digitization_manager/config."""
    config_path = Path.home() / ".digitization_manager" / "config"
    if not config_path.exists():
        return {}
    result = {}
    for line in config_path.read_text().splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            result[k.strip()] = v.strip()
    return result


def run_script(name: str, *script_args: str) -> int:
    """Run a project shell script (update.sh / uninstall.sh).

    Prefer the original project directory (recorded at install time) so
    update/uninstall run against the real source, not the installed copy.
    """
    candidates = []
    project_dir = _install_config().get("PROJECT_DIR")
    if project_dir:
        candidates.append(Path(project_dir) / name)
    candidates.append(paths.project_root() / name)
    for candidate in candidates:
        if candidate.exists():
            return subprocess.run([str(candidate), *script_args]).returncode
    print(f"{name} not found. Run it from the project directory.", file=sys.stderr)
    return 1


def main() -> int:
    """CLI entry: handle --version/--update/--uninstall, otherwise start
    the waitress server on the LAN and open a browser."""
    parser = argparse.ArgumentParser(
        prog="digitization_manager", description=APP_NAME
    )
    parser.add_argument("--version", action="store_true")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--update", action="store_true",
                        help="re-install from the project source")
    parser.add_argument("--uninstall", action="store_true",
                        help="full uninstall (keeps your archive folder)")
    parser.add_argument("--uninstall-partial", action="store_true",
                        help="remove only the command + desktop icon")
    args = parser.parse_args()

    if args.version:
        print(f"digitization_manager {__version__}")
        return 0
    if args.update:
        return run_script("update.sh")
    if args.uninstall:
        return run_script("uninstall.sh")
    if args.uninstall_partial:
        return run_script("uninstall.sh", "--partial")

    # Imported here (not at module top) so --version/--update stay fast
    # and don't build the Flask app / data dirs unnecessarily.
    from waitress import serve  # production WSGI server (threads, LAN-safe)

    from .app import app, lan_ip

    root = paths.ensure_data_dirs()
    lan = lan_ip()
    print(f"{APP_NAME} {__version__}")
    print(f"Archive folder: {root}")
    print(f"This machine:   http://localhost:{args.port}")
    print(f"Lab machines:   http://{lan}:{args.port}")
    print("Press Ctrl+C to stop.")

    browser_timer = None
    if not args.no_browser:
        browser_timer = _open_browser_later(f"http://localhost:{args.port}")

    try:
        serve(app, host=args.host, port=args.port)
    except OSError as exc:
        if exc.errno == errno.EADDRINUSE:
            if browser_timer:
                browser_timer.cancel()  # avoid a second tab
            url = f"http://localhost:{args.port}"
            if _app_alive(args.port):
                # Icon clicked while the server is still up: just
                # reopen the browser instead of dying silently.
                print(f"Already running — opening {url}")
                try:
                    webbrowser.open(url)
                except Exception:
                    pass
                return 0
            print(
                f"\nPort {args.port} is already in use by another program.\n"
                "Stop it, or pick another port with --port."
            )
            return 1
        raise
    return 0


if __name__ == "__main__":
    sys.exit(main())
