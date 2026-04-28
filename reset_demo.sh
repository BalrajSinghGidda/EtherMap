#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EVENTS_FILE="$ROOT_DIR/events.log"
STATE_FILE="$ROOT_DIR/state.json"
UPLOAD_DIR="$ROOT_DIR/uploads"

if [[ "${1:-}" != "--yes" ]]; then
  echo "This will clear events.log, state.json, and files in uploads/."
  read -r -p "Continue? [y/N] " reply
  if [[ ! "$reply" =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
  fi
fi

mkdir -p "$UPLOAD_DIR"
: > "$EVENTS_FILE"
printf '{"nodes":[]}\n' > "$STATE_FILE"
find "$UPLOAD_DIR" -mindepth 1 -maxdepth 1 -type f -delete

echo "Demo state reset complete."
