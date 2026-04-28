#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

TMP_VAULT="$(mktemp -d /tmp/tremotino-rearch.XXXXXX)"
TMP_SUPPORT="$TMP_VAULT/.tremotino-support"

mkdir -p "$TMP_VAULT/Library/Packs/test-pack/vendor/sample-skill"
cat > "$TMP_VAULT/Library/Packs/test-pack/vendor/sample-skill/SKILL.md" <<'SKILL'
---
name: sample-skill
description: Sample migrated skill for Tremotino re-architecture smoke tests.
---

# Sample Skill

## When To Use
Use when testing vendored skill migration.
SKILL

export TREMOTINO_VAULT="$TMP_VAULT"
export TREMOTINO_SUPPORT="$TMP_SUPPORT"

python3 -m tremotino_core migrate_vault --json '{"dry_run": true}'
python3 -m tremotino_core bootstrap
python3 -m tremotino_core rebuild_index
python3 -m tremotino_core list_skills | grep -q sample-skill
python3 -m tremotino_core create_spin_job --json "{\"title\":\"Spin sample\",\"goal\":\"Extract signal from sample files\",\"source_paths\":[\"$TMP_VAULT/Library/Skills/sample-skill/SKILL.md\"]}"
test -f "$TMP_VAULT/Library/Skills/sample-skill/SKILL.md"
test -d "$TMP_VAULT/Work/Jobs"

echo "Tremotino re-architecture core smoke passed"
