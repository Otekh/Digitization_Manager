#!/usr/bin/env bash
# Double-clickable installer for macOS users.
# Opens in Terminal and runs install.sh from this folder.
#
# If macOS blocks it ("cannot be opened because it is from an unidentified
# developer"), right-click the file and choose Open, then click Open again.

cd "$(dirname "$0")" || exit 1

echo "==============================================="
echo "  OTEKH Digitization Manager - macOS Installer"
echo "==============================================="
echo ""

if [[ ! -f install.sh ]]; then
  echo "install.sh not found in this folder."
  echo "Keep this file inside the Digitization_Manager project folder."
  read -r -p "Press Return to close..."
  exit 1
fi

bash install.sh

echo ""
echo "Done. You can close this window."
read -r -p "Press Return to close..."
