# Global agent instructions

Shared by Claude Code (`~/.claude/CLAUDE.md`), Codex (`~/.codex/AGENTS.md`) and
OpenCode (`~/.config/opencode/AGENTS.md`). Source of truth:
`~/dotfiles/agents/AGENTS.md`. Project `AGENTS.md`/`CLAUDE.md` files override this.

## Agent roles (Orca)

When work is split across Orca workers, follow the `agent-routing` skill. Summary:

| Role | Primary | Fallback when out of usage |
|---|---|---|
| Planning, architecture, orchestration (coordinator) | `claude` | `codex` |
| Implementation, code review | `codex` | `claude` |
| Lint, formatting, small/mechanical tasks, optional second review | `opencode` | `codex` |

- Coordinators plan and integrate; they do not implement large changes themselves
  when a worker can.
- A worker that hits a usage/rate limit is retried on its fallback agent, never on
  the same agent in a loop.

## General

- Reply in the user's language (usually Portuguese).
- Never commit or push unless asked.
