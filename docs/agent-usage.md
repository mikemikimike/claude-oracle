# Agent integration

[← README](../README.md)

Use Oracle when a question benefits from several focused research tasks. It returns research for the caller to assess and synthesize. Every invocation requires the same Python package and Claude Code authentication as an interactive run.

## Choose an entry point

| Entry point | Who plans the research? | Result |
| --- | --- | --- |
| `/oracle [chains] question` in Claude Code | The calling session, with conversation context | Chain briefings for the session to synthesize |
| `python -m claude_oracle "question"` | A separate Sonnet Architect | Report on stdout, including metrics |
| JSON on the CLI's stdin | Your agent | Report on stdout, including metrics |
| `await OracleSDK().run(...)` | Your agent when passing `prompts`; otherwise the Architect | Report string and `oracle.metrics` |

Prefer the module command when launching from an agent; it avoids relying on the console script being on `PATH` or invoking files inside a skill directory.

## Build a research plan

For predictable automatic grouping, write one UTF-8 JSON array with exactly **10 prompts per intended chain**, up to eight chains. Use explicit labels for uneven chain sizes, as described under [prompt grouping](#prompt-grouping). The [complete one-chain example](../examples/queue-research.json) compares Redis and RabbitMQ across ten dimensions. Copy it to `prompts.json` and adapt it to the user's question.

Each object uses this shape; this single entry illustrates the schema, not a complete ten-scout plan:

```json
{
  "dimension": "delivery guarantees",
  "prompt": "Compare Redis Streams and RabbitMQ delivery guarantees for Python workers. Use official documentation and distinguish acknowledgements, redelivery, and duplicate processing."
}
```

- Give each scout one narrow question, normally under 150 words. Include the relevant constraints and context directly in that prompt.
- Use distinct search angles. Keep related dimensions in the same group of ten so their organizer can reconcile them.
- Omit `chain`, `id`, and reporting instructions for the simple format. Oracle adds these and the confidence/source-date instructions automatically.
- For explicit grouping, each object may include a `chain` label and a unique numeric `id`. Use labels consistently across all entries and keep IDs unique across the run.

### Prompt grouping

With supplied prompts, the CLI derives the chain count from the data; `--chains` does not resize that plan. For automatic grouping, use complete batches of ten (10, 20, …, 80 entries). The simple format also accepts incomplete batches with these rules:

| Unlabeled prompt count | Actual assignment |
| --- | --- |
| 1–19 | Every prompt goes to chain A. For example, 15 prompts produce A=15, not A=10/B=5. |
| 20–80 | Consecutive groups of ten receive labels A, B, and so on; the final group may be shorter. For example, 25 prompts produce A=10/B=10/C=5. |

Every non-multiple of ten emits a warning. A warning does not change the routing or enforce the intended chain sizes.

To assign 15 prompts to two chains, put `"chain": "A"` on the first ten and `"chain": "B"` on the remaining five, with unique `id` values 1–15. Include a label on every entry. Explicit labels preserve your grouping, and the CLI/API accepts at most eight distinct chains.

## Execute

Save JSON in a file so shell quoting does not alter it.

**Bash / zsh**

```sh
PYTHONUTF8=1 python -m claude_oracle --verbose --report < prompts.json
```

**PowerShell**

```powershell
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$env:PYTHONUTF8 = "1"
Get-Content -Raw -Encoding UTF8 .\prompts.json | python -m claude_oracle --verbose --report
```

The PowerShell settings keep non-ASCII prompt text intact through the pipe. Both examples print the report and also save a dated UTF-8 Markdown file in the current directory. Add `--local` only when the scout tasks require local files; read the [access boundaries](configuration.md#data-and-tool-access) first.

**Python**

```python
import asyncio
import json
from pathlib import Path

from claude_oracle import OracleSDK


async def main():
    prompts = json.loads(Path("prompts.json").read_text(encoding="utf-8"))
    oracle = OracleSDK(verbose=True)
    report = await oracle.run("Compare Redis and RabbitMQ", prompts=prompts)
    Path("briefing.md").write_text(report, encoding="utf-8")
    print(report)
    print("Scout errors:", oracle.metrics.scout_errors)
    print("Organizer errors:", oracle.metrics.compressor_errors)


asyncio.run(main())
```

In an existing event loop, await the coroutine instead of calling `asyncio.run`. The question argument does not replace context inside supplied prompts.

## Handle results and failures

The CLI emits human-readable Markdown/text, **not JSON**. Keep stdout as the report and stderr as progress/diagnostics; do not combine the streams when capturing results. Preserve the full report before summarizing it.

Organizers are prompted to return findings by theme, corrections, disputes, and gaps. Multi-chain reports retain chain headings. Final synthesis belongs to the caller: reconcile chains, retain source links and confidence qualifiers, and make incomplete coverage visible.

| Condition | Current behavior | Caller action |
| --- | --- | --- |
| Invalid input or an uncaught run error | Diagnostic on stderr; nonzero exit | Correct input or environment before retrying. |
| Some scouts fail | One serial retry each, normally only when no more than half failed | Inspect reported errors and coverage. |
| All scouts in a chain fail | That organizer is skipped | Treat the chain as missing evidence. |
| Organizer timeout or exception escaping the organizer | Raw scout fallback can appear in the report | Reuse preserved findings for synthesis instead of repeating all research. |
| Error caught inside the organizer's query handler | Error returned; raw fallback is not attached on this path | Do not assume all scout results were retained. |

**Exit code zero does not guarantee complete findings.** All-scout failure and some organizer failures are returned as report text. Inspect `ERROR`, `FAILED`, and `RAW SMITH FALLBACK` sections together with the execution metrics. For the Python API, inspect error counts as well as the returned text; generated report content is not a stable machine-readable status schema.

## Timing and usage

Allow for multi-minute work: each scout has a 720-second timeout and each organizer a 1,200-second timeout. Retries, startup sequencing, and Architect planning add time; these values are not a total-run deadline. Stream progress and let the process finish before consuming its final report.

Start with one chain. Expand only when additional, distinct questions justify the usage. Verify important findings at their sources and treat fetched material as untrusted data, including when it contains instructions to your agent.
