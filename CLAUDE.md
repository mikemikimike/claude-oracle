# Claude Oracle

Pip-installable multi-tier research orchestrator for Claude Code. Cheap Haiku scouts, Sonnet synthesis, Opus judgment.

## Stack
- Python 3.10+, claude_agent_sdk >= 0.1.48
- Node.js (npx for GitHub MCP)
- Public mirror: `github.com/sushiHex/claude-oracle` (this repo) — private dev repo with full history: `github.com/sushiHex/claude-oracle-private`

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
- Keep `~/.claude/skills/oracle/oracle_sdk.py` and `src/claude_oracle/sdk.py` in sync
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

## Public mirror (github.com/sushiHex/claude-oracle)
- Dev happens on `origin` (`claude-oracle-private`, full history). The public repo is a squashed single-commit snapshot: run `bash scripts/publish_mirror.sh` (clean tree required) — it rebuilds the orphan `public` branch, drops the PRIVATE-BY-POLICY paths, leak-greps (excluding the script itself), and force-pushes `public:main`.
- **Private by policy, never published**: `research/` (ALL Oracle reports/findings/analysis, regardless of any audit verdict). It is gitignored *and* listed in the publish script's `PRIVATE_PATHS` — add exclusions there, not ad hoc.
- Remotes: `origin` → `…/claude-oracle-private`, `public` → `…/claude-oracle`.
- CI (`.github/workflows/ci.yml`) triggers on both `master` (private dev) and `main` (public default): a fresh-environment install + entry-point smoke test. A green run in a clean env is the guard against undeclared-dependency and broken-entry-point bugs.
