# Claude Oracle

Pip-installable multi-tier research orchestrator for Claude Code. Cheap Haiku scouts, Sonnet synthesis, Opus judgment.

## Stack
- Python 3.10+, claude_agent_sdk >= 0.1.48
- Node.js (npx for GitHub MCP)
- Development repository: `github.com/sushiHex/claude-oracle` (public). `github.com/sushiHex/claude-oracle-private` is reserved for private data.

## Structure
```
src/claude_oracle/
  sdk.py        — the engine (OracleSDK class)
  install.py    — claude-oracle-install command
  __main__.py   — python -m claude_oracle
  data/SKILL.md — /oracle skill definition
pyproject.toml  — pip metadata, entry points
```

## Commands
- Install: `pip install git+https://github.com/sushiHex/claude-oracle.git`
- Setup skill: `claude-oracle-install`
- Run: `claude-oracle "question"` or `python -m claude_oracle "question"`

## Conventions
- Refresh the installed skill with `python -m claude_oracle.install`; `~/.claude/skills/oracle/oracle_sdk.py` is a launcher that delegates to the installed package.
- Version bump ALL of these together: `pyproject.toml`, `src/claude_oracle/__init__.py`,
  the `sdk.py` docstring + banner, `data/SKILL.md` header — then copy `data/SKILL.md`
  to `~/.claude/skills/oracle/SKILL.md` (the packaged copy is what external users get;
  it went stale at v4.3.1 once already)

## Gotchas (project-specific)
- HTTP MCP transport broken in SDK v0.1.48 — stdio only
- Smiths: no truncation — `_build_scout_data` sends full Smith outputs (Anderson runs on Sonnet's large context)
- Concurrent Claude subprocess startups race on the shared `~/.claude.json` and can corrupt it (upstream bug, reproduced on CLI 2.1.207). Defense: per-subprocess `CLAUDE_CONFIG_DIR` isolation whenever a token is available (`_oauth_token()` priority: ORACLE_OAUTH_TOKEN > CLAUDE_CODE_OAUTH_TOKEN > the session's own access token from `.credentials.json` when >1h remains — access token ONLY, never the refresh token, so children can't rotate credentials); otherwise a startup launch gate (`STARTUP_GATE_TIMEOUT_S`) plus a one-shot retry pass. Full run-parallelism in both modes. (The old `SCOUT_LAUNCH_STAGGER_S` fixed stagger is gone.)
- Scouts are web-only by default; `--local` (CLI) / `local_tools=True` (API) grants Read/Grep/Glob — keep it opt-in, it's a prompt-injection exfiltration surface when combined with web access
- GitHub MCP npx package is version-pinned in `_github_mcp()` — bump deliberately, never float to latest
- `_normalize_prompts` warns if prompt count isn't a multiple of 10
- Don't hardcode model names — use MODEL_WEIGHTS dict

## Repository workflow
- All code, documentation, issues, and pull requests belong in `sushiHex/claude-oracle`. Develop on feature branches and target the public repository's `main` branch.
- `origin` must point to `https://github.com/sushiHex/claude-oracle.git`. Confirm the repository and base branch before opening or merging a PR.
- Use `sushiHex/claude-oracle-private` only to preserve private reports, research, and other private data. It is not a development upstream or release source.
- **Private by policy, never published**: `research/` and Oracle report outputs. Keep these gitignored in the public checkout; preserve selected private artifacts in the private repository separately.
- Preserve public Git history. Do not merge private history into the public repository or replace public `main` with an orphan snapshot. When recovering misplaced work, transfer only the reviewed source/documentation files onto a branch based on public `main`.
- `scripts/publish_mirror.sh` is retired and exits without changing Git state. Use the normal public PR workflow.
- CI (`.github/workflows/ci.yml`) runs on public `main` pushes and pull requests: a fresh-environment install, unit tests, and entry-point smoke checks on Ubuntu and Windows.
