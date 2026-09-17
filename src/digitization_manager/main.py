"""Entry point: `digitization_manager` command.

Starts the LAN server on the host machine and opens a browser. Other lab
machines connect to http://<this-machine-ip>:<port> over the wired network.
"""
import argparse    # CLI flags (--port, --update, --uninstall, ...)
import errno       # EADDRINUSE check for the port-in-use message
import subprocess  # running update.sh / uninstall.sh
import sys         # exit codes + stderr
import threading   # delayed browser open
import webbrowser  # opening the app URL on the host machine
from pathlib import Path

from . import APP_NAME, __version__, paths


def _open_browser_later(url: str) -> None:
    """Open the app URL ~1s after startup so the server is listening
    first. Failures are ignored (headless / icon launches)."""
    def _open():
        try:
            webbrowser.open(url)
        except Exception:
            pass

    threading.Timer(1.0, _open).start()


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

    if not args.no_browser:
        _open_browser_later(f"http://localhost:{args.port}")

    try:
        serve(app, host=args.host, port=args.port)
    except OSError as exc:
        if exc.errno == errno.EADDRINUSE:
            print(
                f"\nPort {args.port} is already in use — the app is probably "
                "already running.\n"
                f"Open http://localhost:{args.port} in your browser, or stop "
                "the other instance first\n"
                "(admins: user menu → Shutdown App)."
            )
            return 1
        raise
    return 0


if __name__ == "__main__":
    sys.exit(main())
