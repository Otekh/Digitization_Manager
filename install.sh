#!/usr/bin/env bash
# Installs OTEKH Digitization Manager on Linux or macOS.
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  echo "Usage: ./install.sh"
  echo "Installs the digitization_manager command, dependencies, and app icon."
  exit 0
fi

OS="$(uname -s)"

# --- macOS: install Homebrew if missing ---
# Needed for tesseract/ghostscript/openjdk (and uv below). The official
# installer also handles Xcode Command Line Tools. It needs sudo, so it
# only runs interactively.
if [[ "$OS" == "Darwin" ]] && ! command -v brew >/dev/null 2>&1; then
  echo "Homebrew not found - installing it now..."
  if [[ ! -t 0 ]]; then
    echo "Homebrew is required on macOS but this installer has no terminal." >&2
    echo "Install it from https://brew.sh then re-run this script." >&2
    exit 1
  fi
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  # Put brew on PATH for the rest of this script (Apple Silicon vs Intel).
  if [[ -x /opt/homebrew/bin/brew ]]; then
    eval "$(/opt/homebrew/bin/brew shellenv)"
  elif [[ -x /usr/local/bin/brew ]]; then
    eval "$(/usr/local/bin/brew shellenv)"
  fi
  if ! command -v brew >/dev/null 2>&1; then
    echo "Homebrew installation failed. See https://brew.sh" >&2
    exit 1
  fi
fi

# --- install uv if missing (needed to build the Python environment) ---
if ! command -v uv >/dev/null 2>&1; then
  echo "uv not found - installing it now..."
  if [[ "$OS" == "Darwin" ]] && command -v brew >/dev/null 2>&1; then
    brew install uv
  else
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
  fi
  if ! command -v uv >/dev/null 2>&1; then
    echo "Could not install uv. Install it from https://docs.astral.sh/uv" >&2
    exit 1
  fi
fi

# --- system packages: tesseract + ghostscript (OCR), java (SAFBuilder) ---
# Collect whatever is missing and install it in one shot.
missing_pkgs=()
command -v tesseract >/dev/null 2>&1 || missing_pkgs+=("tesseract")
{ command -v gs >/dev/null 2>&1 || command -v ghostscript >/dev/null 2>&1; } || missing_pkgs+=("ghostscript")
# macOS ships a /usr/bin/java STUB that passes 'command -v' but errors
# with "Unable to locate a Java Runtime" when no JDK is installed — so
# probe with -version (the stub exits non-zero) instead of just which.
java -version >/dev/null 2>&1 || missing_pkgs+=("java")

if [[ ${#missing_pkgs[@]} -gt 0 ]]; then
  echo "Missing packages: ${missing_pkgs[*]}"
  if [[ "$OS" == "Linux" ]]; then
    # Map generic names to Debian/Ubuntu package names.
    deb_pkgs=()
    for p in "${missing_pkgs[@]}"; do
      case "$p" in
        tesseract)   deb_pkgs+=("tesseract-ocr") ;;
        ghostscript) deb_pkgs+=("ghostscript") ;;
        java)        deb_pkgs+=("default-jre") ;;
      esac
    done
    # Prefer nala (friendlier apt frontend); fall back to apt-get.
    if command -v nala >/dev/null 2>&1; then
      PKG_MGR="sudo nala"
    else
      PKG_MGR="sudo apt-get"
    fi
    echo "Installing with: $PKG_MGR install ${deb_pkgs[*]}"
    $PKG_MGR install -y "${deb_pkgs[@]}"
  elif [[ "$OS" == "Darwin" ]]; then
    brew_pkgs=()
    for p in "${missing_pkgs[@]}"; do
      case "$p" in
        tesseract)   brew_pkgs+=("tesseract") ;;
        ghostscript) brew_pkgs+=("ghostscript") ;;
        java)        brew_pkgs+=("openjdk") ;;
      esac
    done
    if ! command -v brew >/dev/null 2>&1; then
      echo "Homebrew is required on macOS. Install it from https://brew.sh" >&2
      exit 1
    fi
    brew install "${brew_pkgs[@]}"
    # openjdk is keg-only: brew won't put it on PATH. The proper fix is
    # linking the .jdk bundle into /Library/Java/JavaVirtualMachines so
    # the system /usr/bin/java wrapper finds it (needs sudo). The app
    # also checks brew's opt dir directly, so this is belt-and-suspenders.
    if [[ " ${brew_pkgs[*]} " =~ " openjdk " ]]; then
      JDK="$(brew --prefix openjdk 2>/dev/null)/libexec/openjdk.jdk"
      if [[ -d "$JDK" && -t 0 ]]; then
        sudo ln -sfn "$JDK" /Library/Java/JavaVirtualMachines/openjdk.jdk || true
      fi
    fi
  fi
fi

# --- install locations ---
if [[ -w "/usr/local" ]]; then
  INSTALL_DIR="/usr/local/share/digitization_manager"
  BIN_DIR="/usr/local/bin"
else
  INSTALL_DIR="$HOME/.local/share/digitization_manager"
  BIN_DIR="$HOME/.local/bin"
fi

# Guard: never install over the directory this script is running from
# (happens if the installed copy of install.sh/update.sh is run directly).
if [[ "$PROJECT_DIR" == "$INSTALL_DIR" ]]; then
  echo "Cannot install over the installed copy of the app." >&2
  echo "Run ./install.sh from the project source folder, or use 'digitization_manager --update'." >&2
  exit 1
fi

mkdir -p "$INSTALL_DIR" "$BIN_DIR"
rm -rf "${INSTALL_DIR:?}"/*

# Copy project (excluding venv/git/archive) into the install dir.
find . -mindepth 1 -maxdepth 1 \
  -not -name '.venv' -not -name '.git' -not -name '__pycache__' \
  -not -name 'archive' \
  -exec cp -R {} "$INSTALL_DIR/" \;

cd "$INSTALL_DIR"
if [[ ! -d .venv ]]; then
  uv venv
fi
uv pip install -e .

# --- run-anywhere command ---
cat > "$BIN_DIR/digitization_manager" <<'EOF'
#!/usr/bin/env bash
set -e
INSTALL_DIR=__INSTALL_DIR__
if [[ ! -d "$INSTALL_DIR" ]]; then
  echo "Digitization Manager is not installed." >&2
  exit 1
fi
exec "$INSTALL_DIR/.venv/bin/python" -m digitization_manager.main "$@"
EOF
sed -i.bak "s|__INSTALL_DIR__|$INSTALL_DIR|g" "$BIN_DIR/digitization_manager"
rm -f "$BIN_DIR/digitization_manager.bak"
chmod +x "$BIN_DIR/digitization_manager"

# --- make sure BIN_DIR is on PATH ---
# ~/.local/bin isn't in the default PATH on macOS (or minimal Linux
# setups); append it to the user's shell profile so the command works
# in new terminals.
case ":$PATH:" in
  *":$BIN_DIR:"*) ;;  # already on PATH
  *)
    if [[ "$OS" == "Darwin" ]]; then PROFILE="$HOME/.zshrc"; else PROFILE="$HOME/.profile"; fi
    if ! grep -qsF "$BIN_DIR" "$PROFILE" 2>/dev/null; then
      echo "export PATH=\"$BIN_DIR:\$PATH\"" >> "$PROFILE"
      echo "Added $BIN_DIR to PATH in $PROFILE (open a new terminal to use it)."
    fi
    ;;
esac

# --- recovery admin password ---
# The hidden 'admin' account's password lives in the data root, never in
# the repo. Prompt for it on first install; skip if already set or if
# there's no terminal (the app will generate a random one on first run).
DATA_ROOT="$HOME/Documents/OTEKH Digitization Manager"
PW_FILE="$DATA_ROOT/admin_password.txt"
if [[ ! -s "$PW_FILE" && -t 0 ]]; then
  mkdir -p "$DATA_ROOT"
  echo ""
  echo "Set the password for the hidden recovery admin account ('admin')."
  echo "It is stored in: $PW_FILE"
  while true; do
    read -r -s -p "Admin password: " pw1; echo ""
    read -r -s -p "Confirm password: " pw2; echo ""
    if [[ -z "$pw1" ]]; then
      echo "Password cannot be empty."
    elif [[ "$pw1" != "$pw2" ]]; then
      echo "Passwords do not match - try again."
    else
      printf '%s\n' "$pw1" > "$PW_FILE"
      chmod 600 "$PW_FILE"
      unset pw1 pw2
      break
    fi
  done
fi

# --- record install paths for update/uninstall ---
CONFIG_DIR="$HOME/.digitization_manager"
mkdir -p "$CONFIG_DIR"
cat > "$CONFIG_DIR/config" <<EOF
INSTALL_DIR=$INSTALL_DIR
BIN_DIR=$BIN_DIR
PROJECT_DIR=$PROJECT_DIR
EOF

# --- desktop integration ---
if [[ "$OS" == "Linux" ]]; then
  APPS_DIR="$HOME/.local/share/applications"
  ICON_DIR="$HOME/.local/share/icons"
  mkdir -p "$APPS_DIR" "$ICON_DIR"
  cp "$INSTALL_DIR/assets/icon.png" "$ICON_DIR/digitization_manager.png"
  cat > "$APPS_DIR/digitization_manager.desktop" <<EOF
[Desktop Entry]
Name=OTEKH Digitization Manager
Comment=Digitization intake, review, and DSpace prep
Exec=$BIN_DIR/digitization_manager
Icon=$ICON_DIR/digitization_manager.png
Terminal=false
Type=Application
Categories=Office;
EOF
  echo "APP_DIR=$APPS_DIR" >> "$CONFIG_DIR/config"
elif [[ "$OS" == "Darwin" ]]; then
  if [[ -w "/Applications" ]]; then APP_DIR="/Applications"; else APP_DIR="$HOME/Applications"; fi
  APP_PATH="$APP_DIR/OTEKH Digitization Manager.app"
  mkdir -p "$APP_PATH/Contents/MacOS" "$APP_PATH/Contents/Resources"
  cat > "$APP_PATH/Contents/Info.plist" <<'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key><string>OTEKH Digitization Manager</string>
    <key>CFBundleDisplayName</key><string>OTEKH Digitization Manager</string>
    <key>CFBundleIdentifier</key><string>ca.otekh.digitization-manager</string>
    <key>CFBundleVersion</key><string>0.1.0</string>
    <key>CFBundlePackageType</key><string>APPL</string>
    <key>CFBundleExecutable</key><string>launcher</string>
    <key>CFBundleIconFile</key><string>icon</string>
    <key>LSMinimumSystemVersion</key><string>10.15</string>
    <key>NSHighResolutionCapable</key><true/>
</dict>
</plist>
EOF
  cat > "$APP_PATH/Contents/MacOS/launcher" <<EOF
#!/usr/bin/env bash
# Brew's keg-only openjdk isn't on PATH; include its bin dir directly
# (Apple Silicon + Intel prefixes) so SAFBuilder can always find java.
export PATH="\$HOME/.local/bin:\$HOME/.cargo/bin:/opt/homebrew/opt/openjdk/bin:/usr/local/opt/openjdk/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:\$PATH"
# Server already up? Just reopen the browser and exit — dock clicks
# stay instant and we never boot a second python.
if curl -sf -m 1 -o /dev/null "http://127.0.0.1:8000/login"; then
  open "http://localhost:8000"
  exit 0
fi
# Run detached so this launcher exits immediately: the icon is a
# launcher, not the server, so every click either starts the server
# or — via main.py's port-in-use check — reopens the browser.
mkdir -p "\$HOME/.digitization_manager"
nohup "$INSTALL_DIR/.venv/bin/python" -m digitization_manager.main >>"\$HOME/.digitization_manager/server.log" 2>&1 &
EOF
  chmod +x "$APP_PATH/Contents/MacOS/launcher"
  # Build .icns from the PNG if macOS tools exist.
  if command -v sips >/dev/null 2>&1 && command -v iconutil >/dev/null 2>&1; then
    ICONSET_DIR="$(mktemp -d)/icon.iconset"
    mkdir -p "$ICONSET_DIR"
    for size in 16 32 64 128 256 512 1024; do
      sips -z "$size" "$size" "$INSTALL_DIR/assets/icon.png" --out "$ICONSET_DIR/icon_${size}x${size}.png" >/dev/null 2>&1 || true
      if [[ "$size" -ne 1024 ]]; then
        sips -z $((size * 2)) $((size * 2)) "$INSTALL_DIR/assets/icon.png" --out "$ICONSET_DIR/icon_${size}x${size}@2x.png" >/dev/null 2>&1 || true
      fi
    done
    iconutil -c icns "$ICONSET_DIR" -o "$APP_PATH/Contents/Resources/icon.icns" >/dev/null 2>&1 || true
    rm -rf "$ICONSET_DIR"
  fi
  # Register with Launch Services so it appears in Launchpad / can be pinned
  # to the Dock immediately, and refresh Finder's icon cache.
  touch "$APP_PATH"
  LSREGISTER="/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister"
  if [[ -x "$LSREGISTER" ]]; then
    "$LSREGISTER" -f "$APP_PATH" >/dev/null 2>&1 || true
  fi
  echo "APP_DIR=$APP_DIR" >> "$CONFIG_DIR/config"
fi

echo ""
echo "Installed OTEKH Digitization Manager."
echo "  Run from terminal: digitization_manager"
echo "  Archive folder:    ~/Documents/OTEKH Digitization Manager/"
if [[ "$OS" == "Linux" ]]; then
  echo "  App launcher:      $APPS_DIR/digitization_manager.desktop"
else
  echo "  App bundle:        $APP_PATH"
fi
