#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

TMP_VAULT="$(mktemp -d /tmp/tremotino-bib-mcp.XXXXXX)"

printf '%s\n' \
  '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' \
  '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"import_bibtex","arguments":{"source":"mcp-smoke","content":"@article{smith2026signal, title={Signal from messy archives}, author={Smith, Ada}, year={2026}, doi={10.1234/example}, journal={Journal of Test Workflows}}"}}}' \
  '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"list_bibliography","arguments":{}}}' \
  '{"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"validate_bibliography","arguments":{}}}' \
  | TREMOTINO_VAULT="$TMP_VAULT" python3 mcp/tremotino_mcp.py
