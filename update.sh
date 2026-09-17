#!/usr/bin/env bash
# Re-installs OTEKH Digitization Manager from the current project folder.
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  echo "Usage: ./update.sh"
  echo "Re-installs the app from the current project directory."
  exit 0
fi

if [[ ! -f install.sh ]]; then
  echo "install.sh not found in $PROJECT_DIR" >&2
  exit 1
fi

./install.sh
