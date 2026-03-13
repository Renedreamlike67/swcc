# SWCC Codex Install

This repository keeps the editable Claude-side source in `CLAUDE.md` and `.claude-plugin/`, then regenerates the managed Codex files under `.codex/`.

## User Entry Scripts

- `codex-init/install.sh` — one-step sync + install entrypoint
- `codex-init/uninstall.sh` — one-step uninstall entrypoint

## Managed Codex Files

- `.codex/skills/*` — the 5 user-invocable Codex skills
- `.codex/skills/swcc/agents/*` — the 10 shared SWCC role prompts
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
- installs managed skill symlinks into `${CODEX_HOME}/skills` when `CODEX_HOME` is set, otherwise `~/.codex/skills`
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

- removes the managed skill symlinks from `${CODEX_HOME}/skills` when `CODEX_HOME` is set, otherwise `~/.codex/skills`
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

- `jicha`
- `juguo`
- `xieshang`
- `zhili`
- `zhixing`
- `swcc`

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

- `jicha`
- `juguo`
- `xieshang`
- `zhili`
- `zhixing`

## Notes

- Source of truth: `CLAUDE.md` and `.claude-plugin/`
- Managed Codex outputs live only under `.codex/`
- The runtime artifacts still live in `.tmp/swcc/`, just like the Claude version.
- The Codex adaptation preserves the same five workflow names and all ten shared political-role prompts.
- The orchestration backend is adapted to Codex sub-agents, so the coordinator skill dispatches `agent_prompt`-based role work instead of Claude's `swcc:agent-name` namespace.
- Project title source: `SWCC — Socialism With Chinese Characteristics (SW Claude Code)`
