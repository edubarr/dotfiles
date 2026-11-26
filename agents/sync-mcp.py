#!/usr/bin/env python3
"""Apply ~/dotfiles/agents/mcp.json to Claude Code, Codex and OpenCode.

Idempotent. Only touches the servers listed in mcp.json; other servers each
tool has are left alone. Run with: python3 -I ~/dotfiles/agents/sync-mcp.py
"""
import json
import re
import subprocess
import sys
from pathlib import Path

HOME = Path.home()
SRC = Path(__file__).resolve().parent / "mcp.json"
CLAUDE_JSON = HOME / ".claude.json"
CODEX_TOML = HOME / ".codex" / "config.toml"
OPENCODE_JSON = HOME / ".config" / "opencode" / "opencode.json"
BEGIN, END = "# >>> dotfiles/agents/mcp.json (managed) >>>", "# <<< dotfiles/agents/mcp.json (managed) <<<"


def load_servers():
    return json.loads(SRC.read_text())


def sync_claude(servers):
    current = {}
    if CLAUDE_JSON.exists():
        current = json.loads(CLAUDE_JSON.read_text()).get("mcpServers", {})
    for name, s in servers.items():
        want = {"type": "http", "url": s["url"]}
        if s.get("headers"):
            want["headers"] = s["headers"]
        have = current.get(name)
        if have == want:
            print(f"claude:   {name} ok")
            continue
        if have is not None:
            subprocess.run(["claude", "mcp", "remove", "--scope", "user", name], check=True, capture_output=True)
        subprocess.run(["claude", "mcp", "add-json", "--scope", "user", name, json.dumps(want)], check=True, capture_output=True)
        print(f"claude:   {name} {'updated' if have else 'added'}")


def toml_str(v):
    return json.dumps(v)  # JSON string escaping is valid TOML basic-string escaping


def sync_codex(servers):
    if not CODEX_TOML.parent.exists():
        print("codex:    ~/.codex missing, skipped")
        return
    lines = CODEX_TOML.read_text().splitlines() if CODEX_TOML.exists() else []
    names = "|".join(re.escape(n) for n in servers)
    owned = re.compile(rf"^\[mcp_servers\.(\"?)({names})\1(\..*)?\]\s*$")
    out, skipping, in_block = [], False, False
    for line in lines:
        if line.strip() == BEGIN:
            in_block = True
            continue
        if line.strip() == END:
            in_block = False
            continue
        if in_block:
            continue
        if line.startswith("["):
            skipping = bool(owned.match(line.strip()))
        if not skipping:
            out.append(line)
    while out and not out[-1].strip():
        out.pop()
    block = ["", BEGIN]
    for name, s in servers.items():
        block += ["", f"[mcp_servers.{name}]", f"url = {toml_str(s['url'])}"]
        if s.get("headers"):
            pairs = ", ".join(f"{toml_str(k)} = {toml_str(v)}" for k, v in s["headers"].items())
            block.append(f"http_headers = {{ {pairs} }}")
    block += ["", END]
    CODEX_TOML.write_text("\n".join(out + block) + "\n")
    print(f"codex:    {', '.join(servers)} written")


def sync_opencode(servers):
    if not OPENCODE_JSON.exists():
        print("opencode: opencode.json missing, skipped")
        return
    data = json.loads(OPENCODE_JSON.read_text())
    target = data.setdefault("mcp", {}).setdefault("servers", {})
    changed = False
    for name, s in servers.items():
        want = {"type": "remote", "url": s["url"]}
        if s.get("headers"):
            want["headers"] = s["headers"]
        if target.get(name) != want:
            target[name] = want
            changed = True
    if changed:
        OPENCODE_JSON.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    print(f"opencode: {'updated' if changed else 'ok'}")


def main():
    servers = load_servers()
    ok = True
    for fn in (sync_claude, sync_codex, sync_opencode):
        try:
            fn(servers)
        except Exception as e:  # keep going so one broken tool doesn't block the rest
            ok = False
            print(f"{fn.__name__}: FAILED: {e}", file=sys.stderr)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
