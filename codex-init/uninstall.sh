#!/usr/bin/env bash
set -euo pipefail

DRY_RUN=0
TARGET_ROOT=""
COMPONENTS=(jicha juguo xieshang zhili zhixing swcc)

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)
      DRY_RUN=1
      ;;
    --target)
      shift
      if [[ $# -eq 0 ]]; then
        echo "--target requires a directory path" >&2
        exit 1
      fi
      TARGET_ROOT="$1"
      ;;
    -h|--help)
      script_name="$(basename "${BASH_SOURCE[0]}")"
      cat <<USAGE
Usage: ${script_name} [--target DIR] [--dry-run]

Options:
  --target DIR Remove managed symlinks from the specified Codex skills directory
  --dry-run    Print planned actions without changing the filesystem

Default target:
  \${CODEX_HOME}/skills when CODEX_HOME is set, otherwise ~/.codex/skills
USAGE
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      exit 1
      ;;
  esac
  shift
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SOURCE_ROOT="$REPO_ROOT/.codex/skills"

if [[ -z "$TARGET_ROOT" ]]; then
  if [[ -n "${CODEX_HOME:-}" ]]; then
    TARGET_ROOT="$CODEX_HOME/skills"
  else
    TARGET_ROOT="$HOME/.codex/skills"
  fi
fi
TARGET_ROOT="${TARGET_ROOT%/}"

run() {
  if [[ "$DRY_RUN" -eq 1 ]]; then
    printf '[dry-run] %s\n' "$*"
  else
    eval "$@"
  fi
}

done_msg() {
  if [[ "$DRY_RUN" -eq 1 ]]; then
    printf '\nDry run complete. No filesystem changes were made.\n'
  else
    printf '\nDone. Restart Codex or reopen the repository if the old skills are still cached.\n'
  fi
}

remove_one() {
  local name="$1"
  local source_path="$SOURCE_ROOT/$name"
  local destination_path="$TARGET_ROOT/$name"

  if [[ -L "$destination_path" ]]; then
    local current_target
    current_target="$(readlink "$destination_path")"
    if [[ "$current_target" == "$source_path" ]]; then
      run "rm -f \"$destination_path\""
      if [[ "$DRY_RUN" -eq 1 ]]; then
        printf '[dry-run] would remove: %s\n' "$destination_path"
      else
        printf 'Removed: %s\n' "$destination_path"
      fi
      return
    fi
    printf 'Skipped unmanaged symlink: %s -> %s\n' "$destination_path" "$current_target"
    return
  fi

  if [[ -e "$destination_path" ]]; then
    printf 'Skipped unmanaged path: %s\n' "$destination_path"
    return
  fi

  printf 'Not installed: %s\n' "$destination_path"
}

for name in "${COMPONENTS[@]}"; do
  remove_one "$name"
done
done_msg
