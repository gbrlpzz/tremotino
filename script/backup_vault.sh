#!/usr/bin/env bash
set -euo pipefail

VAULT="${TREMOTINO_VAULT:-$HOME/Documents/Tremotino/Vault}"
REMOTE="${TREMOTINO_VAULT_REMOTE:-}"
MESSAGE="${1:-Tremotino vault snapshot}"

mkdir -p "$VAULT"
cd "$VAULT"

if [ ! -d .git ]; then
  git init
  git branch -M main
fi

if [ ! -f .gitignore ]; then
  cat > .gitignore <<'EOF'
.DS_Store
*.tmp
.tremotino-backup
EOF
fi

if [ -n "$REMOTE" ]; then
  if git remote get-url origin >/dev/null 2>&1; then
    git remote set-url origin "$REMOTE"
  else
    git remote add origin "$REMOTE"
  fi
fi

git add -A

if git diff --cached --quiet; then
  printf 'No vault changes to commit in %s\n' "$VAULT"
else
  git commit -m "$MESSAGE"
fi

if git remote get-url origin >/dev/null 2>&1; then
  git push -u origin main
else
  printf 'No origin remote configured. Set TREMOTINO_VAULT_REMOTE or use Settings.\n'
fi
