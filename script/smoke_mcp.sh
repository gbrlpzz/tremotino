#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

printf '%s\n' \
  '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' \
  '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' \
  '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"run_runbook_dry_run","arguments":{"id":"rebuild-index"}}}' \
  '{"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"assemble_context_pack","arguments":{"id":"codex-default","client":"codex","task":"smoke test"}}}' \
  '{"jsonrpc":"2.0","id":5,"method":"tools/call","params":{"name":"list_skills","arguments":{}}}' \
  | python3 mcp/tremotino_mcp.py
