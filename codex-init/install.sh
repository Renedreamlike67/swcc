#!/usr/bin/env bash
set -euo pipefail

INSTALL_ARGS=()
DRY_RUN=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)
      DRY_RUN=1
      INSTALL_ARGS+=("$1")
      ;;
    -h|--help)
      script_name="$(basename "${BASH_SOURCE[0]}")"
      cat <<USAGE
Usage: ${script_name} [install-options]

Runs:
  1. sync.sh to regenerate .codex/
  2. installs managed skill symlinks into the default global skills root or --target DIR

Install options are forwarded to the generated install script, such as:
  --target DIR
  --force
  --dry-run
USAGE
      exit 0
      ;;
    *)
      INSTALL_ARGS+=("$1")
      ;;
  esac
  shift
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SYNC_SCRIPT="$SCRIPT_DIR/sync.sh"
GENERATED_INSTALL_SCRIPT="$REPO_ROOT/.codex/skills/swcc/scripts/install.sh"

if [[ ! -f "$SYNC_SCRIPT" ]]; then
  echo "Sync script not found: $SYNC_SCRIPT" >&2
  exit 1
fi

printf '==> Syncing Codex files\n'
if [[ "$DRY_RUN" -eq 1 ]]; then
  bash "$SYNC_SCRIPT" --dry-run
else
  bash "$SYNC_SCRIPT"
fi

if [[ ! -f "$GENERATED_INSTALL_SCRIPT" ]]; then
  if [[ "$DRY_RUN" -eq 1 ]]; then
    printf '[dry-run] would run %s' "$GENERATED_INSTALL_SCRIPT"
    if [[ "${#INSTALL_ARGS[@]}" -gt 0 ]]; then
      printf ' %q' "${INSTALL_ARGS[@]}"
    fi
    printf '\n'
    exit 0
  fi
  echo "Generated install script not found after sync: $GENERATED_INSTALL_SCRIPT" >&2
  exit 1
fi

printf '\n==> Installing Codex skills\n'
exec bash "$GENERATED_INSTALL_SCRIPT" "${INSTALL_ARGS[@]}"
