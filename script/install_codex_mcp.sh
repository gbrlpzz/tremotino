#!/usr/bin/env bash
set -euo pipefail

MODE="${1:---print}"
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SERVER="$ROOT_DIR/mcp/tremotino_mcp.py"
VAULT="${TREMOTINO_VAULT:-$HOME/Documents/Tremotino/Vault}"
CONFIG="${CODEX_CONFIG:-$HOME/.codex/config.toml}"

BLOCK="$(cat <<EOF

[mcp_servers.tremotino]
command = "python3"
args = ["$SERVER"]
env = { TREMOTINO_VAULT = "$VAULT" }
EOF
)"

case "$MODE" in
  --print)
    printf '%s\n' "$BLOCK"
    ;;
  --apply)
    mkdir -p "$(dirname "$CONFIG")"
    touch "$CONFIG"
    if grep -q '^\[mcp_servers\.tremotino\]' "$CONFIG"; then
      printf 'Tremotino MCP config already exists in %s\n' "$CONFIG"
      exit 0
    fi
    cp "$CONFIG" "$CONFIG.tremotino-backup"
    printf '%s\n' "$BLOCK" >> "$CONFIG"
    printf 'Added Tremotino MCP config to %s\nBackup: %s.tremotino-backup\n' "$CONFIG" "$CONFIG"
    ;;
  *)
    printf 'Usage: %s [--print|--apply]\n' "$0" >&2
    exit 2
    ;;
esac
