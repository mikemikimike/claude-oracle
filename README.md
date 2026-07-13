# Claude Oracle

A **multi-tier research orchestrator** for [Claude Code](https://claude.com/claude-code). It fans a research question out across many cheap [Haiku](https://www.anthropic.com/claude/haiku) scouts running in parallel, has [Sonnet](https://www.anthropic.com/claude/sonnet) organize their findings, and delivers a single structured briefing back to your [Opus](https://www.anthropic.com/claude/opus) session — roughly **10× the research breadth at a fraction of Opus-only cost**.

The trick is tiering the work by how hard it is: breadth-first search is cheap and embarrassingly parallel (Haiku), synthesis needs judgment (Sonnet), and the final editorial call is yours (Opus, i.e. your live session).

```
You → Opus (decomposes) → 10–80 Haiku "Smiths" (parallel scout) → Sonnet "Anderson" (organize) → briefing
```

## What it does

- **Parallel breadth** — 1 chain (10 Smiths) up to 8 chains (80 Smiths), each Smith a Haiku agent with `WebSearch`, `WebFetch`, and optional GitHub MCP. Local file tools (`Read`/`Grep`/`Glob`) are opt-in via `--local` — see [Privacy](#privacy).
- **True isolation, enforced in Python** — in multi-chain mode each Sonnet "Anderson" sees **only** its own chain's Smith reports; the orchestrator groups the data by chain so no compressor ever sees another chain's firehose. The isolation is structural, not a prompt instruction.
- **Confidence-tagged findings** — every scout is told to tag numbers `HIGH` / `MEDIUM` / `LOW` and date its sources, so recency and provenance survive all the way to your briefing.
- **Resilient by design** — per-Smith and per-Anderson timeouts, a startup launch gate (or full config isolation — see [Concurrency safety](#concurrency-safety--fast-launches)) so parallel subprocesses never collide on shared startup state, a one-shot retry pass for failed Smiths, an all-scouts-failed guard, and a raw-Smith fallback so a failed Anderson never discards its chain's scout work.
- **Live GitHub data (optional)** — set a PAT and Smiths prefer GitHub MCP over web search for stars, commits, and issues.

## Requirements

- [Claude Code](https://claude.com/claude-code) with an active subscription (Oracle drives subagents through it)
- Python 3.10+
- Node.js — only if you want the optional GitHub MCP tools (`npx`)

## Install

```bash
pip install git+https://github.com/sushiHex/claude-oracle.git
claude-oracle-install
```

`claude-oracle-install` copies the `/oracle` skill into your own `~/.claude/skills/oracle/` so it's available in any Claude Code session on your machine.

> If `claude-oracle-install` isn't found (pip's Scripts directory is often not on PATH, especially on Windows user installs), the module forms work unconditionally:
>
> ```bash
> python -m claude_oracle.install     # same as claude-oracle-install
> python -m claude_oracle "question"  # same as claude-oracle
> ```

## Usage

In a Claude Code session, `/oracle` lets *your* session act as the Architect — it decomposes the question using full conversation context, then runs the fleet:

```
/oracle what open-source AI agent frameworks exist on GitHub
/oracle 4 compare cloud providers for LLM hosting
```

A leading number sets the chain count (default 1); more chains = wider coverage.

### Direct CLI

```bash
claude-oracle "your research question"          # Sonnet Architect decomposes for you
claude-oracle --chains 4 "your question"        # 4 chains → 40 Smiths
claude-oracle --verbose "your question"         # stream per-Smith tool activity
claude-oracle --report "your question"          # also save a dated report file
claude-oracle --local "audit my repo's tests"   # grant scouts local file tools (see Privacy)
```

You can also pipe a ready-made decomposition as JSON on stdin (this is what the `/oracle` skill does under the hood):

```bash
python -m claude_oracle --verbose <<'PROMPTS'
[{"dimension": "frameworks", "prompt": "Find the top 3 open-source agent frameworks on GitHub with stars and what each exposes."}]
PROMPTS
```

## How it works

1. **Decompose** — your Opus session (or the fallback Sonnet Architect) splits the question into `chains × 10` narrow sub-prompts, each a single dimension a Haiku agent can fully answer in ~1,500 tokens.
2. **Scout** — all Smiths run concurrently, each searching a different slice, reporting dense facts + confidence tags.
3. **Organize** — one Sonnet Anderson per chain dedups, reconciles conflicting/stale numbers, flags disputes and gaps, and preserves every unique signal (it organizes, it does not compress away findings).
4. **Synthesize** — the Anderson briefing(s) return to your session, where you (Opus) do the final editorial judgment.

## Concurrency safety & fast launches

Claude Code's shared `~/.claude.json` is written non-atomically, so many CLI subprocesses starting at once can tear it — a [long-reported upstream bug](https://github.com/anthropics/claude-code/issues/28847) (also [#28806](https://github.com/anthropics/claude-code/issues/28806), [#29051](https://github.com/anthropics/claude-code/issues/29051), [#40226](https://github.com/anthropics/claude-code/issues/40226)) that we have reproduced on current CLI versions at ~20-way concurrency. Oracle defends itself in one of two modes:

**Isolated mode (automatic — zero setup).** When your Claude Code login's current access token has at least an hour of life left (it usually does), every Smith/Anderson automatically gets its own throwaway `CLAUDE_CONFIG_DIR` authenticated with that short-lived token: no shared file, no race, no gate — the whole fleet launches instantly. Only the access token is passed to child processes; **the refresh token never leaves your primary credential store**, so children structurally cannot rotate or damage your login. Config dirs are deleted after the run (crash-safe).

**Gated mode (automatic fallback).** Near token expiry, or when no credentials file exists (e.g. macOS Keychain-only setups), Oracle falls back to a launch gate: one subprocess enters its startup window at a time, opening for the next as soon as the current one emits its first message. A few seconds of ramp per Smith; fully parallel once started; a retry pass relaunches any Smith that still fails.

**Optional override (CI / headless / Keychain setups).** A long-lived token forces isolated mode everywhere:

```bash
claude setup-token   # one-time browser approval; requires a Pro/Max/Team plan

# Windows
setx ORACLE_OAUTH_TOKEN "<token>"

# Linux / macOS
echo 'export ORACLE_OAUTH_TOKEN="<token>"' >> ~/.bashrc
```

`ORACLE_OAUTH_TOKEN` is preferred because it changes nothing about how your interactive `claude` sessions authenticate; a directly exported `CLAUDE_CODE_OAUTH_TOKEN` also works and takes priority over the automatic session token. Usage always counts against your subscription limits.

> **Treat the token like a password.** It is a ~1-year credential to your Claude subscription: don't commit it, don't paste it into shell commands that land in history (use your OS's env-var UI or a secrets manager if unsure), and revoke it from your Claude account settings if it leaks. Do **not** copy `.credentials.json` between config dirs as an alternative — parallel copies refresh OAuth tokens independently and can invalidate your primary login.

## Privacy

Oracle is an orchestrator, not a local tool — it works by making model and tool calls on your behalf. Be aware that:

- **Prompts go to Anthropic.** Your question and the generated sub-prompts are sent to Claude models through your Claude Code authentication, exactly like any other Claude Code session.
- **Scouts touch the open web.** Smiths use `WebSearch` / `WebFetch`, so sub-prompt search terms and fetched URLs reach search and web providers.
- **GitHub is opt-in.** If you set `GITHUB_PAT`, Smiths query the GitHub API with *your* token (`public_repo` scope, or `repo` for private repos) via a version-pinned MCP server. Unset, no GitHub calls are made.
- **Your credential store is read, never copied.** For automatic isolated mode the orchestrator reads `accessToken`/`expiresAt` from your own Claude Code credentials file — the same file the `claude` CLI itself reads — and passes only that short-lived access token to the subprocesses it spawns on your behalf. The refresh token is never read, never copied, and never leaves your machine's primary store.
- **Local file access is opt-in (`--local`).** By default scouts are web-only. With `--local` they can also `Read`/`Grep`/`Glob` your filesystem to research your own code — understand the trade-off: scouts process untrusted web content non-interactively, and combining local reads with web fetches creates a prompt-injection exfiltration surface (a malicious page could try to steer a scout into fetching a URL that embeds local file contents). Model safety training resists this, but it is not an architectural guarantee — use `--local` only for questions about your own codebase, and never in a checkout containing secrets.

The orchestration logic itself runs locally; only the model/tool calls above leave your machine. No separate telemetry is collected.

### GitHub MCP (optional)

```bash
# Windows
setx GITHUB_PAT "ghp_your_token_here"

# Linux / macOS
echo 'export GITHUB_PAT="ghp_your_token_here"' >> ~/.bashrc
```

## Cost

Rough order of magnitude for a single-chain run (10 Smiths + 1 Anderson): tens of thousands of Haiku-rate tokens plus a few thousand Sonnet-rate — a small fraction of what equivalent breadth would cost if every scout were an Opus agent. Actual figures depend on your plan; treat the in-tool percentages as approximate and unofficial.

## License

MIT — see [LICENSE](LICENSE).
