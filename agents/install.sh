#!/usr/bin/env bash
# Link shared agent config from ~/dotfiles/agents into Claude Code, Codex and
# OpenCode, then sync MCP servers. Idempotent; existing real files are moved to
# <file>.bak-<timestamp> before being replaced by a symlink.
set -euo pipefail

DOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TS="$(date +%Y%m%d%H%M%S)"

link() { # link <target> <linkpath>
  local target="$1" path="$2"
  mkdir -p "$(dirname "$path")"
  if [ -L "$path" ] && [ "$(readlink -f "$path")" = "$(readlink -f "$target")" ]; then
    echo "ok      $path"; return
  fi
  if [ -e "$path" ] || [ -L "$path" ]; then
    mv "$path" "$path.bak-$TS"; echo "backup  $path -> $path.bak-$TS"
  fi
  ln -s "$target" "$path"; echo "linked  $path -> $target"
}

# Shared global instructions
link "$DOT/agents/AGENTS.md" "$HOME/.claude/CLAUDE.md"
link "$DOT/agents/AGENTS.md" "$HOME/.codex/AGENTS.md"
link "$DOT/agents/AGENTS.md" "$HOME/.config/opencode/AGENTS.md"

# Skills: ~/.agents (Codex, OpenCode) -> dotfiles/opencode/.agents; Claude needs per-skill links
link "$DOT/opencode/.agents" "$HOME/.agents"
for skill in "$DOT"/opencode/.agents/skills/*/; do
  name="$(basename "$skill")"
  link "${skill%/}" "$HOME/.claude/skills/$name"
done

# MCP servers (single list in agents/mcp.json)
python3 -I "$DOT/agents/sync-mcp.py"
