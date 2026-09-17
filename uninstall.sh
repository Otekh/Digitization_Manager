#!/usr/bin/env bash
# Uninstalls OTEKH Digitization Manager.
#
# Tiers:
#   ./uninstall.sh             Prompts you to choose partial or full.
#   ./uninstall.sh --partial   Remove the command + desktop icon only.
#                              Keeps installed files so you can re-link later.
#   ./uninstall.sh --full      Full uninstall: command, icon, installed files,
#                              and install config. Your archive folder
#                              (~/Documents/OTEKH Digitization Manager) is kept.
#   ./uninstall.sh --purge     Full uninstall AND delete the archive folder
#                              (all entries, files, users). Cannot be undone.
set -euo pipefail

MODE=""
case "${1:-}" in
  --help|-h)
    echo "Usage: ./uninstall.sh [--partial | --full | --purge]"
    echo ""
    echo "  (no flag)   Prompts you to choose partial or full"
    echo "  --partial   Remove only the command + desktop icon (keeps installed files)"
    echo "  --full      Full uninstall of the app; keeps your archive folder"
    echo "  --purge     Full uninstall AND deletes ~/Documents/OTEKH Digitization Manager"
    exit 0
    ;;
  --partial|-p|p|partial) MODE="partial" ;;
  --full|-f|f|full)       MODE="full" ;;
  --purge)                MODE="purge" ;;
  "")                     MODE="" ;;
  *) echo "Unknown option: $1 (try --help)" >&2; exit 1 ;;
esac

# No flag given -> ask the user which tier they want.
if [[ -z "$MODE" ]]; then
  echo "Uninstall OTEKH Digitization Manager"
  echo ""
  echo "  Partial (p): removes the 'digitization_manager' command and the"
  echo "               desktop icon only. The installed app files stay in place"
  echo "               so you can re-link or reinstall later without downloading."
  echo ""
  echo "  Full (f):    removes the command, desktop icon, and all installed app"
  echo "               files. Your archive folder (entries, files, users) is kept."
  echo ""
  read -r -p "Do you want full uninstall (f, full) or partial (p, partial)? [f/p] " ans
  case "$ans" in
    f|F|full|Full|FULL)       MODE="full" ;;
    p|P|partial|Partial|PARTIAL) MODE="partial" ;;
    *) echo "Cancelled."; exit 0 ;;
  esac
fi

CONFIG="$HOME/.digitization_manager/config"
if [[ -f "$CONFIG" ]]; then
  # shellcheck source=/dev/null
  source "$CONFIG"
else
  INSTALL_DIR="$HOME/.local/share/digitization_manager"
  BIN_DIR="$HOME/.local/bin"
fi

# --- partial: command + desktop integration only ---
if [[ -n "${BIN_DIR:-}" && -f "$BIN_DIR/digitization_manager" ]]; then
  rm -f "$BIN_DIR/digitization_manager"
fi
rm -f "$HOME/.local/share/applications/digitization_manager.desktop"
rm -f "$HOME/.local/share/icons/digitization_manager.png"
rm -rf "$HOME/Applications/OTEKH Digitization Manager.app"
rm -rf "/Applications/OTEKH Digitization Manager.app"

if [[ "$MODE" == "partial" ]]; then
  echo "Partial uninstall done (command + icon removed)."
  echo "Installed files kept at: ${INSTALL_DIR:-$HOME/.local/share/digitization_manager}"
  exit 0
fi

# --- full: also remove installed files + config ---
rm -rf "${INSTALL_DIR:-$HOME/.local/share/digitization_manager}"
rm -rf "$HOME/.digitization_manager"
echo "Uninstalled OTEKH Digitization Manager."

# --- purge: also delete the archive/data folder ---
DATA_ROOT="${DIGIMGR_DATA:-$HOME/Documents/OTEKH Digitization Manager}"
if [[ "$MODE" == "purge" ]]; then
  if [[ -d "$DATA_ROOT" ]]; then
    read -r -p "Delete archive folder '$DATA_ROOT' and ALL its data? [y/N] " ans
    if [[ "$ans" =~ ^[Yy]$ ]]; then
      rm -rf "$DATA_ROOT"
      echo "Deleted $DATA_ROOT"
    else
      echo "Archive folder kept: $DATA_ROOT"
    fi
  fi
else
  echo "Your archive folder was kept: $DATA_ROOT"
fi
