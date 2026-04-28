#!/usr/bin/env bash
set -euo pipefail

REPO="${1:-tremotino-vault}"
VAULT="${TREMOTINO_VAULT:-$HOME/Documents/Tremotino/Vault}"

if ! command -v gh >/dev/null 2>&1; then
  printf 'GitHub CLI `gh` is required to create a private repo.\n' >&2
  exit 1
fi

if ! gh auth status >/dev/null 2>&1; then
  printf 'Run `gh auth login` before creating the private vault repo.\n' >&2
  exit 1
fi

REMOTE="$(gh repo create "$REPO" --private --source "$VAULT" --remote origin --push 2>&1)"
printf '%s\n' "$REMOTE"
