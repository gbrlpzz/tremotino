#!/usr/bin/env bash
set -euo pipefail

MODE="${1:---print}"
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SERVER="$ROOT_DIR/mcp/tremotino_mcp.py"
VAULT="${TREMOTINO_VAULT:-$HOME/Documents/Tremotino/Vault}"
SUPPORT="${TREMOTINO_SUPPORT:-$HOME/Library/Application Support/Tremotino}"
CONFIG="${CODEX_CONFIG:-$HOME/.codex/config.toml}"

BLOCK="$(cat <<EOF

[mcp_servers.tremotino]
command = "python3"
args = ["$SERVER"]
env = { TREMOTINO_VAULT = "$VAULT", TREMOTINO_SUPPORT = "$SUPPORT" }
EOF
)"

case "$MODE" in
  --print)
    printf '%s\n' "$BLOCK"
    ;;
  --apply)
    mkdir -p "$(dirname "$CONFIG")"
    touch "$CONFIG"
    cp "$CONFIG" "$CONFIG.tremotino-backup"
    if grep -q '^\[mcp_servers\.tremotino\]' "$CONFIG"; then
      TMP_CONFIG="$(mktemp)"
      TMP_BLOCK="$(mktemp)"
      printf '%s\n' "$BLOCK" > "$TMP_BLOCK"
      awk -v block_file="$TMP_BLOCK" '
        function print_block() {
          while ((getline line < block_file) > 0) {
            print line
          }
          close(block_file)
        }
        BEGIN { in_block = 0; replaced = 0 }
        /^\[mcp_servers\.tremotino\]$/ {
          if (!replaced) {
            print_block()
            replaced = 1
          }
          in_block = 1
          next
        }
        /^\[/ && in_block {
          in_block = 0
        }
        !in_block {
          print
        }
        END {
          if (!replaced) {
            print_block()
          }
        }
      ' "$CONFIG" > "$TMP_CONFIG"
      mv "$TMP_CONFIG" "$CONFIG"
      rm -f "$TMP_BLOCK"
      printf 'Updated Tremotino MCP config in %s\nBackup: %s.tremotino-backup\n' "$CONFIG" "$CONFIG"
      exit 0
    fi
    printf '%s\n' "$BLOCK" >> "$CONFIG"
    printf 'Added Tremotino MCP config to %s\nBackup: %s.tremotino-backup\n' "$CONFIG" "$CONFIG"
    ;;
  *)
    printf 'Usage: %s [--print|--apply]\n' "$0" >&2
    exit 2
    ;;
esac
