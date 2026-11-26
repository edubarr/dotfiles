---
name: agent-routing
description: >-
  Which Orca agent (claude, codex, opencode) gets each kind of work, and how to
  fall back when an agent is out of usage or rate-limited. Use whenever you are
  coordinating Orca workers (worker-start, task DAGs, reviews), when a worker
  stops or fails with a usage/rate limit, or when you are a coordinator other
  than Claude because Claude is out of usage.
---

# Agent routing for Orca workers

Use together with the `orchestration` skill (it owns the commands). This skill
only decides **which `--agent`** to pass and **what to do when one is out of usage**.

## Default roles

| Work | `--agent` | Notes |
|---|---|---|
| Planning, architecture, decomposition, integration | coordinator (you) | Normally `claude`. Do it yourself; don't dispatch it. |
| Implementation (features, fixes, refactors, tests) | `codex` | Use `--worktree new-child` when several write in parallel. |
| Code review of a diff/branch | `codex` | Read-only; `--worktree current` is fine. |
| Lint, formatting, codemods, renames, small bounded edits | `opencode` | Give exact files and the exact command to run. |
| Optional second review (different model family) | `opencode` | Only when the change is risky or the user asks. |

Rules:
- Do not pass `--model` unless the user named one; each agent uses its own config.
- Up to ~4 workers at once; prefer `opencode` for volume, `codex` for substance.
- Review always runs in a fresh worker, never in the session that implemented
  the change. Default reviewer is a new `codex` worker; add `opencode` as a
  second reviewer only for risky changes or when asked.

## Fallback chain

```
claude  <->  codex  <->  opencode
```

| Out of usage | Send its work to |
|---|---|
| `opencode` | `codex` |
| `codex` | `claude` (implementation and review) |
| `claude` (as worker) | `codex` |
| `claude` (as coordinator) | the user starts `codex` as coordinator; it follows this same skill |

If the fallback is also out of usage, try the remaining agent once; if all are
out, stop and tell the user which limits were hit and when they reset (if shown).

## Detecting "out of usage"

Treat an agent as out of usage for the rest of this Run when any of these happen:

- A worker escalates or finishes as failed, and
  `ORCA orchestration worker-read --dispatch <id>` shows text matching
  (case-insensitive): `usage limit`, `rate limit`, `hit your limit`,
  `limit reached`, `quota`, `429`, `too many requests`, `insufficient credits`,
  `try again (in|at)`, `resets? (at|in)`.
- `worker-start` for that agent fails at `agent_readiness` (CLI missing or
  broken) — treat it as unavailable the same way.

Do not treat ordinary task failures (tests failing, compile errors) as limits.

## Retrying on the fallback

1. If the worker may still be running, stop it first (see the orchestration
   skill's `references/recovery-and-cleanup.md`).
2. Retry the same Task on the fallback agent, repeating placement:
   `ORCA orchestration worker-start --environment local --task <task_id> --retry-of <dispatch_id> --agent <fallback> --worktree <same as before>`
3. Remember the exhausted agent for the rest of the Run and route its new work
   straight to the fallback.
4. In the final report, say which tasks ran on a fallback agent and why.

## When you are not Claude

If you are `codex` (or `opencode`) acting as coordinator because Claude is out
of usage: do the planning yourself, keep routing implementation/review to
`codex` workers and small tasks to `opencode`, and don't dispatch to `claude`
until the user says its limit has reset.
