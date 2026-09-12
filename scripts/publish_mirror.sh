#!/usr/bin/env bash
# Retired: development now happens directly in the public repository.
set -euo pipefail

cat >&2 <<'MESSAGE'
Mirror publishing has been retired. This command makes no Git changes.

Develop in https://github.com/sushiHex/claude-oracle and open a PR against main.
Use claude-oracle-private only to preserve private data.
See CLAUDE.md, Repository workflow.
MESSAGE
exit 1
