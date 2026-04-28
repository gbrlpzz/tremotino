#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

export TREMOTINO_VAULT="${TREMOTINO_VAULT:-$HOME/Documents/Tremotino/Vault}"
export TREMOTINO_SUPPORT="${TREMOTINO_SUPPORT:-$HOME/Library/Application Support/Tremotino}"

printf '%s\n' \
  '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' \
  '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' \
  '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"assemble_context_pack","arguments":{"id":"codex-default","client":"codex","task":"live Codex MCP smoke"}}}' \
  | python3 mcp/tremotino_mcp.py
