#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from pathlib import Path
from typing import Iterable

GENERATOR_REL = ".codex/scripts/sync-from-claude.py"
SYNC_ENTRY_REL = ".codex/sync.sh"
REPO_ROOT = Path(__file__).resolve().parents[2]
CODEX_ROOT = REPO_ROOT / ".codex"
CLAUDE_PLUGIN_ROOT = REPO_ROOT / ".claude-plugin"
CLAUDE_DOC_PATH = REPO_ROOT / "CLAUDE.md"
MANIFEST_PATH = CODEX_ROOT / "generated-manifest.json"

MANAGED_SKILLS = ["jicha", "juguo", "xieshang", "zhili", "zhixing"]
MANAGED_SHARED_AGENTS = [
    "buwei",
    "dangwei",
    "guowuyuan",
    "jiwei",
    "youpai",
    "zhengyanshi",
    "zhiku",
    "zhongban",
    "zhongjian",
    "zuopai",
]
INSTALL_COMPONENTS = [*MANAGED_SKILLS, "swcc"]
SKIPPED_CLAUDE_SKILLS = ["zhengyanshi", "zhiku"]
SKIPPED_CLAUDE_AGENTS: list[str] = []

AGENT_MODEL = "gpt-5.4"
SKILL_COMMAND_NAMES = MANAGED_SKILLS
ROLE_AGENT_TYPES = {
    "buwei": "worker",
    "dangwei": "default",
    "guowuyuan": "explorer",
    "jiwei": "default",
    "youpai": "default",
    "zhengyanshi": "default",
    "zhiku": "default",
    "zhongban": "explorer",
    "zhongjian": "default",
    "zuopai": "default",
}

SKILL_OPENAI = {
    "jicha": {
        "display_name": "监察 / Jicha",
        "short_description": "Review changes and run verification",
        "default_prompt": "Use $jicha to review the current code changes with SWCC inspection rules.",
    },
    "juguo": {
        "display_name": "举国 / Juguo",
        "short_description": "Emergency parallel SWCC execution",
        "default_prompt": "Use $juguo to fast-track this urgent task with SWCC emergency execution.",
    },
    "xieshang": {
        "display_name": "协商 / Xieshang",
        "short_description": "Debate options and issue a plan",
        "default_prompt": "Use $xieshang to generate an SWCC consultation plan for this task.",
    },
    "zhili": {
        "display_name": "治理 / Zhili",
        "short_description": "Run the full SWCC coding workflow",
        "default_prompt": "Use $zhili to run the full SWCC workflow for this coding task.",
    },
    "zhixing": {
        "display_name": "执行 / Zhixing",
        "short_description": "Execute an approved SWCC plan",
        "default_prompt": "Use $zhixing to execute the approved SWCC plan for this task.",
    },
}

FRONTMATTER_PATTERN = re.compile(r"\A---\n(.*?)\n---\n?", re.S)
SUBAGENT_PATTERN = re.compile(r'^(?P<indent>\s*)subagent_type:\s*"swcc:(?P<role>[a-z]+)"\s*$', re.M)


class SyncError(RuntimeError):
    pass


def json_quote(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def split_frontmatter(text: str) -> tuple[dict[str, str], str]:
    match = FRONTMATTER_PATTERN.match(text)
    if not match:
        raise SyncError("Missing YAML frontmatter")
    block = match.group(1)
    body = text[match.end() :]
    data: dict[str, str] = {}
    for raw_line in block.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            raise SyncError(f"Unsupported frontmatter line: {raw_line!r}")
        key, value = line.split(":", 1)
        value = value.strip()
        if value.startswith(('"', "'")) and value.endswith(('"', "'")):
            value = value[1:-1]
        data[key.strip()] = value
    return data, body


def dump_frontmatter(pairs: Iterable[tuple[str, str]]) -> str:
    lines = ["---"]
    for key, value in pairs:
        lines.append(f"{key}: {value}")
    lines.append("---")
    return "\n".join(lines) + "\n\n"


def replace_skill_commands(text: str) -> str:
    pattern = re.compile(rf'(?<![\w$])/(?P<name>{"|".join(SKILL_COMMAND_NAMES)})\b')
    return pattern.sub(lambda match: f'${match.group("name")}', text)


def replace_subagent_refs(text: str) -> str:
    def repl(match: re.Match[str]) -> str:
        indent = match.group("indent")
        role = match.group("role")
        agent_type = ROLE_AGENT_TYPES.get(role, "default")
        return (
            f'{indent}agent_type: "{agent_type}"\n'
            f'{indent}agent_prompt: "../swcc/agents/{role}.md"'
        )

    return SUBAGENT_PATTERN.sub(repl, text)


def transform_skill_text(text: str) -> str:
    text = replace_skill_commands(text)
    text = replace_subagent_refs(text)
    return text if text.endswith("\n") else text + "\n"


def render_agent(agent_name: str) -> str:
    source_path = CLAUDE_PLUGIN_ROOT / "agents" / f"{agent_name}.md"
    frontmatter, body = split_frontmatter(source_path.read_text())
    pairs: list[tuple[str, str]] = []
    for key, value in frontmatter.items():
        if key == "model":
            pairs.append((key, AGENT_MODEL))
        elif key == "description":
            pairs.append((key, json_quote(value)))
        else:
            pairs.append((key, value))

    if not any(key == "model" for key, _ in pairs):
        pairs.append(("model", AGENT_MODEL))

    return dump_frontmatter(pairs) + body.strip() + "\n"


def render_skill(skill_name: str) -> str:
    source_path = CLAUDE_PLUGIN_ROOT / "skills" / skill_name / "SKILL.md"
    return transform_skill_text(source_path.read_text())


def render_openai_yaml(skill_name: str) -> str:
    spec = SKILL_OPENAI[skill_name]
    return (
        "interface:\n"
        f"  display_name: {json_quote(spec['display_name'])}\n"
        f"  short_description: {json_quote(spec['short_description'])}\n"
        f"  default_prompt: {json_quote(spec['default_prompt'])}\n"
        "policy:\n"
        "  allow_implicit_invocation: false\n"
    )


def parse_claude_title() -> tuple[str, str]:
    text = CLAUDE_DOC_PATH.read_text()
    first_heading = next((line.strip() for line in text.splitlines() if line.startswith("# ")), "# SWCC")
    heading = first_heading.removeprefix("# ").strip()
    short_name = heading.split("—", 1)[0].strip()
    return short_name, heading


def render_runtime_md() -> str:
    skill_count = len(MANAGED_SKILLS)
    return f"""# SWCC Codex Runtime

This folder provides the shared runtime rules for the {skill_count} user-invocable Codex skills plus the shared `swcc/` runtime directory installed into the same skills root.

## Core Rules

- Treat the invoking skill as the **coordinator**. Its job is to parse arguments, dispatch roles, persist artifacts, integrate accepted code changes, and report status.
- Treat `../agents/*.md` as the source-of-truth role prompts. Read the relevant file before spawning each role.
- Keep all intermediate artifacts under `.tmp/swcc/`. Create the directory if it does not exist.
- Save every completed role output to disk before moving to the next phase.
- Preserve the Chinese political-role voice from the bundled role prompts.

## Recommended Codex Agent Types

| Role | Recommended `agent_type` | Why |
|------|--------------------------|-----|
| `zhongban` | `explorer` | Fast repository scan and scale triage |
| `zhengyanshi` | `default` | Problem framing and approach exploration |
| `zuopai` | `default` | SOTA exploration and proposal writing |
| `youpai` | `default` | Conservative proposal writing |
| `zhongjian` | `default` | Synthesis and trade-off analysis |
| `dangwei` | `default` | Final decision writing |
| `guowuyuan` | `explorer` | Dependency-aware task decomposition |
| `buwei` | `worker` | Concrete code-change implementation |
| `jiwei` | `default` | Review plus verification reasoning |
| `zhiku` | `default` | On-demand research support |

## Spawning Pattern

1. Read the relevant role file from `../agents/<role>.md`.
2. Prepend that role prompt to the sub-agent task.
3. Append the phase-specific context: user task, previous reports, constraints, and expected output file.
4. Spawn all roles that can run in parallel before waiting.
5. After completion, persist the returned markdown report to the matching file in `.tmp/swcc/`.

## Buwei Integration Rule

Codex worker agents operate in their own delegated workspace context. When a `buwei` worker returns:

- Review the changed-file summary or patch guidance it produced.
- Integrate the accepted changes into the coordinator workspace before moving on.
- Prefer task batches with disjoint file sets so integration is mechanical.
- If a `buwei` report is too vague to apply, send it back for precise file-level edits or diff-quality instructions before continuing.

## Artifact Conventions

Write these filenames exactly when the corresponding phase runs:

- `.tmp/swcc/zhongban-report.md`
- `.tmp/swcc/zhengyanshi-report.md`
- `.tmp/swcc/zuopai-proposal.md`
- `.tmp/swcc/youpai-proposal.md`
- `.tmp/swcc/zhongjian-proposal.md`
- `.tmp/swcc/dangwei-decision.md`
- `.tmp/swcc/guowuyuan-tasks.md`
- `.tmp/swcc/buwei-<n>-result.md`
- `.tmp/swcc/jiwei-verdict.md`

Use a sequential integer for `buwei-<n>-result.md` across all ministry tasks in the current run.

## Parsing Guidance

- Prefer a user-specified `--scale 小|中|大` override when present.
- Otherwise, extract scale from the explicit `规模判定：[小/中|大]` heading in the `zhongban` report.
- When reading the `guowuyuan` report, derive execution batches from headings such as `### 第一批` and tasks from `#### 任务 N`.
- If the report format drifts, use the most explicit dependency statement available and keep file sets disjoint.

## Research Guidance

The `zuopai` and `zhiku` roles may benefit from live web search. Use it only when the current Codex session has web access. If web search is unavailable, still produce the strongest local-first proposal and explicitly note that the proposal is based on repository context plus existing model knowledge.

## Retry Rules

- `zhili` and `zhixing`: retry ministry execution up to **2** times after a `jiwei` rejection.
- `juguo`: retry ministry execution up to **1** time after a fast-verification rejection.
- Pass the latest `jiwei` rejection report back into the retried `buwei` tasks.

## Completion

In the final user-facing response, summarize:

- final status
- chosen scale or execution mode
- files changed
- whether verification passed
- where the `.tmp/swcc/` artifacts were written
"""


def render_install_md() -> str:
    short_name, heading = parse_claude_title()
    skill_count = len(MANAGED_SKILLS)
    agent_count = len(MANAGED_SHARED_AGENTS)
    skill_list = "\n".join(f"- `{name}`" for name in MANAGED_SKILLS)
    install_list = "\n".join(f"- `{name}`" for name in INSTALL_COMPONENTS)
    return f"""# {short_name} Codex Install

This repository keeps the editable Claude-side source in `CLAUDE.md` and `.claude-plugin/`, then regenerates the managed Codex files under `.codex/`.

## User Entry Scripts

- `codex-init/install.sh` — one-step sync + install entrypoint
- `codex-init/uninstall.sh` — one-step uninstall entrypoint

## Managed Codex Files

- `.codex/skills/*` — the {skill_count} user-invocable Codex skills
- `.codex/skills/swcc/agents/*` — the {agent_count} shared SWCC role prompts
- `.codex/skills/swcc/scripts/*` — internal install and uninstall helpers
- `.codex/scripts/sync-from-claude.py` — the generator
- `.codex/generated-manifest.json` — the managed file manifest

## One-Step Install

From the repository root:

```bash
bash codex-init/install.sh
```

Install into a custom skills directory:

```bash
bash codex-init/install.sh --target /path/to/codex/skills
```

What it does:

- runs `sync.sh` to regenerate `.codex/`
- installs managed skill symlinks into `${{CODEX_HOME}}/skills` when `CODEX_HOME` is set, otherwise `~/.codex/skills`
- forwards install options such as `--target DIR`, `--force`, and `--dry-run`

## One-Step Uninstall

From the repository root:

```bash
bash codex-init/uninstall.sh
```

Remove from a custom skills directory:

```bash
bash codex-init/uninstall.sh --target /path/to/codex/skills
```

What it does:

- removes the managed skill symlinks from `${{CODEX_HOME}}/skills` when `CODEX_HOME` is set, otherwise `~/.codex/skills`
- supports `--target DIR` and `--dry-run`
- skips unmanaged paths instead of deleting them

## Sync From Claude

Run from the repository root:

```bash
bash .codex/sync.sh
```

Helpful modes:

```bash
bash .codex/sync.sh --dry-run
bash .codex/sync.sh --check
```

What it does:

- reads `CLAUDE.md` and `.claude-plugin/`
- regenerates all managed files under `.codex/`
- keeps skill and agent content close to the Claude source, with only Codex-specific path and invocation rewrites
- does **not** modify any file outside `.codex/`

## Internal Helpers

If you want to call the generated helpers directly after syncing:

```bash
bash .codex/skills/swcc/scripts/install.sh
bash .codex/skills/swcc/scripts/uninstall.sh
```

They support `--target /path/to/codex/skills`, and the install helper links these managed directories:

{install_list}

## Verify

1. Restart Codex or reopen the project.
2. Open this repository in Codex.
3. Invoke one of the skills explicitly, for example:

```text
$zhili 给这个项目加 JWT 认证
$xieshang 只给我这个功能的实施方案
$jicha 重点关注安全问题和测试覆盖
```

Expected skill names:

{skill_list}

## Notes

- Source of truth: `CLAUDE.md` and `.claude-plugin/`
- Managed Codex outputs live only under `.codex/`
- The runtime artifacts still live in `.tmp/swcc/`, just like the Claude version.
- The Codex adaptation preserves the same five workflow names and all ten shared political-role prompts.
- The orchestration backend is adapted to Codex sub-agents, so the coordinator skill dispatches `agent_prompt`-based role work instead of Claude's `swcc:agent-name` namespace.
- Project title source: `{heading}`
"""


def render_install_script() -> str:
    components = " ".join(INSTALL_COMPONENTS)
    template = """#!/usr/bin/env bash
set -euo pipefail

DRY_RUN=0
FORCE=0
TARGET_ROOT=""
COMPONENTS=(__COMPONENTS__)

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)
      DRY_RUN=1
      ;;
    --force)
      FORCE=1
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
      cat <<'USAGE'
Usage: .codex/skills/swcc/scripts/install.sh [--target DIR] [--force] [--dry-run]

Options:
  --target DIR Install into the specified Codex skills directory
  --force      Replace existing destinations that are not the expected symlink
  --dry-run    Print planned actions without changing the filesystem

Default target:
  ${CODEX_HOME}/skills when CODEX_HOME is set, otherwise ~/.codex/skills
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
REPO_ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
SOURCE_ROOT="$REPO_ROOT/.codex/skills"

if [[ ! -d "$SOURCE_ROOT" ]]; then
  echo "Skill source directory not found: $SOURCE_ROOT" >&2
  exit 1
fi

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
    printf '\nDone. Managed skills are installed in %s\n' "$TARGET_ROOT"
    printf 'Restart Codex or reopen the repository so it can discover the linked skills.\n'
  fi
}

installed_msg() {
  local destination_path="$1"
  local source_path="$2"
  if [[ "$DRY_RUN" -eq 1 ]]; then
    printf '[dry-run] would install: %s -> %s\n' "$destination_path" "$source_path"
  else
    printf 'Installed: %s -> %s\n' "$destination_path" "$source_path"
  fi
}

install_one() {
  local name="$1"
  local source_path="$SOURCE_ROOT/$name"
  local destination_path="$TARGET_ROOT/$name"

  if [[ ! -d "$source_path" ]]; then
    echo "Managed source directory not found: $source_path" >&2
    exit 1
  fi

  if [[ -L "$destination_path" ]]; then
    local current_target
    current_target="$(readlink "$destination_path")"
    if [[ "$current_target" == "$source_path" ]]; then
      printf 'Already installed: %s -> %s\n' "$destination_path" "$current_target"
      return
    fi
    if [[ "$FORCE" -ne 1 ]]; then
      echo "Destination exists with different symlink target: $destination_path -> $current_target" >&2
      echo "Re-run with --force to replace it." >&2
      exit 1
    fi
    run "rm -f \"$destination_path\""
  elif [[ -e "$destination_path" ]]; then
    if [[ "$FORCE" -ne 1 ]]; then
      echo "Destination already exists and is not a symlink: $destination_path" >&2
      echo "Re-run with --force to replace it." >&2
      exit 1
    fi
    run "rm -rf \"$destination_path\""
  fi

  run "ln -s \"$source_path\" \"$destination_path\""
  installed_msg "$destination_path" "$source_path"
}

run "mkdir -p \"$TARGET_ROOT\""
for name in "${COMPONENTS[@]}"; do
  install_one "$name"
done
done_msg
"""
    return template.replace("__COMPONENTS__", components)


def render_uninstall_script() -> str:
    components = " ".join(INSTALL_COMPONENTS)
    template = """#!/usr/bin/env bash
set -euo pipefail

DRY_RUN=0
TARGET_ROOT=""
COMPONENTS=(__COMPONENTS__)

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
      cat <<'USAGE'
Usage: .codex/skills/swcc/scripts/uninstall.sh [--target DIR] [--dry-run]

Options:
  --target DIR Remove managed symlinks from the specified Codex skills directory
  --dry-run    Print planned actions without changing the filesystem

Default target:
  ${CODEX_HOME}/skills when CODEX_HOME is set, otherwise ~/.codex/skills
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
REPO_ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
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
"""
    return template.replace("__COMPONENTS__", components)


def gather_source_inputs() -> list[str]:
    inputs = [str(CLAUDE_DOC_PATH.relative_to(REPO_ROOT)), str((CLAUDE_PLUGIN_ROOT / "marketplace.json").relative_to(REPO_ROOT))]
    for path in sorted((CLAUDE_PLUGIN_ROOT / "agents").glob("*.md")):
        inputs.append(str(path.relative_to(REPO_ROOT)))
    for path in sorted((CLAUDE_PLUGIN_ROOT / "skills").glob("*/SKILL.md")):
        inputs.append(str(path.relative_to(REPO_ROOT)))
    return inputs


def build_outputs() -> dict[Path, str]:
    outputs: dict[Path, str] = {}

    for skill_name in MANAGED_SKILLS:
        outputs[CODEX_ROOT / "skills" / skill_name / "SKILL.md"] = render_skill(skill_name)
        outputs[CODEX_ROOT / "skills" / skill_name / "agents" / "openai.yaml"] = render_openai_yaml(skill_name)

    for agent_name in MANAGED_SHARED_AGENTS:
        outputs[CODEX_ROOT / "skills" / "swcc" / "agents" / f"{agent_name}.md"] = render_agent(agent_name)

    outputs[CODEX_ROOT / "skills" / "swcc" / "references" / "runtime.md"] = render_runtime_md()
    outputs[CODEX_ROOT / "skills" / "swcc" / "scripts" / "install.sh"] = render_install_script()
    outputs[CODEX_ROOT / "skills" / "swcc" / "scripts" / "uninstall.sh"] = render_uninstall_script()
    outputs[CODEX_ROOT / "INSTALL.md"] = render_install_md()

    manifest = {
        "generator": GENERATOR_REL,
        "entrypoint": SYNC_ENTRY_REL,
        "managed_outputs": sorted(str(path.relative_to(REPO_ROOT)) for path in outputs),
        "source_inputs": gather_source_inputs(),
        "managed_skills": MANAGED_SKILLS,
        "managed_shared_agents": MANAGED_SHARED_AGENTS,
        "skipped_claude_skills": SKIPPED_CLAUDE_SKILLS,
        "skipped_claude_agents": SKIPPED_CLAUDE_AGENTS,
    }
    outputs[MANIFEST_PATH] = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    return outputs


def write_atomic(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        handle.write(content)
        tmp_path = Path(handle.name)
    tmp_path.replace(path)
    if path.suffix == ".sh" or path.name == "sync.sh":
        path.chmod(0o755)


def load_previous_manifest() -> dict[str, object] | None:
    if not MANIFEST_PATH.exists():
        return None
    try:
        return json.loads(MANIFEST_PATH.read_text())
    except json.JSONDecodeError as exc:
        raise SyncError(f"Failed to parse existing manifest: {exc}") from exc


def list_previous_generated_files() -> list[Path]:
    manifest = load_previous_manifest()
    if not manifest:
        return []
    files = manifest.get("managed_outputs", [])
    if not isinstance(files, list):
        return []
    return [REPO_ROOT / rel for rel in files if isinstance(rel, str)]


def summarize_actions(outputs: dict[Path, str]) -> tuple[list[Path], list[Path], list[Path]]:
    writes: list[Path] = []
    unchanged: list[Path] = []
    previous_files = list_previous_generated_files()
    current_targets = set(outputs)
    deletes = [path for path in previous_files if path not in current_targets and path.exists()]

    for path, content in outputs.items():
        if path.exists() and path.read_text() == content:
            unchanged.append(path)
        else:
            writes.append(path)
    return writes, deletes, unchanged


def remove_empty_parents(path: Path) -> None:
    parent = path.parent
    while parent != REPO_ROOT and parent.exists() and not any(parent.iterdir()):
        parent.rmdir()
        parent = parent.parent


def print_summary(writes: list[Path], deletes: list[Path], unchanged: list[Path], *, mode: str) -> None:
    print(f"[{mode}] write {len(writes)} file(s), delete {len(deletes)} file(s), unchanged {len(unchanged)} file(s)")
    for label, items in (("WRITE", writes), ("DELETE", deletes)):
        for path in items:
            print(f"{label} {path.relative_to(REPO_ROOT)}")


def validate_sources() -> None:
    required = [CLAUDE_DOC_PATH, CLAUDE_PLUGIN_ROOT / "marketplace.json"]
    required += [CLAUDE_PLUGIN_ROOT / "agents" / f"{name}.md" for name in MANAGED_SHARED_AGENTS]
    required += [CLAUDE_PLUGIN_ROOT / "skills" / name / "SKILL.md" for name in MANAGED_SKILLS]
    missing = [path for path in required if not path.exists()]
    if missing:
        missing_list = "\n".join(str(path.relative_to(REPO_ROOT)) for path in missing)
        raise SyncError(f"Missing required source/template files:\n{missing_list}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Regenerate managed Codex files from Claude-side sources")
    parser.add_argument("--dry-run", action="store_true", help="Show planned writes/deletes without touching the filesystem")
    parser.add_argument("--check", action="store_true", help="Exit non-zero if managed Codex files are out of date")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    validate_sources()
    outputs = build_outputs()
    writes, deletes, unchanged = summarize_actions(outputs)

    if args.check:
        print_summary(writes, deletes, unchanged, mode="check")
        return 1 if writes or deletes else 0

    if args.dry_run:
        print_summary(writes, deletes, unchanged, mode="dry-run")
        return 0

    for path in deletes:
        path.unlink()
        remove_empty_parents(path)

    for path, content in outputs.items():
        if path in writes:
            write_atomic(path, content)

    print_summary(writes, deletes, unchanged, mode="sync")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SyncError as exc:
        print(f"sync-from-claude: {exc}", file=sys.stderr)
        raise SystemExit(1)
