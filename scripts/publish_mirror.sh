#!/usr/bin/env bash
# Refresh the public mirror (github.com/sushiHex/claude-oracle) from master.
#
# The public repo is a squashed single-commit snapshot of the sanitized tree.
# Development history stays in the private repo (origin = claude-oracle-private).
# PRIVATE-BY-POLICY paths below are excluded even when they are tracked in
# master — research and internal logs never publish, regardless of the verdict
# of any content audit. Policy, not safety.
#
# Prereqs (one-time, see CLAUDE.md "Public mirror"):
#   git remote -v  ->  origin = ...claude-oracle-private, public = ...claude-oracle
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

# Everything tracked in master that must NOT ship publicly:
PRIVATE_PATHS=(
  research                # ALL research / Oracle reports stay private (owner policy)
)

test -z "$(git status --porcelain)" || { echo "working tree not clean"; exit 1; }
git branch -D public 2>/dev/null || true
git checkout --orphan public
git rm -rq --cached .
git add -A
for p in "${PRIVATE_PATHS[@]}"; do git rm -rq --cached "$p" 2>/dev/null || true; done
git commit -q -m "Public release snapshot

Squashed snapshot of the sanitized tree; development history and
research stay in the private repository."
COUNT=$(git ls-files | wc -l)
# ':!scripts/...' — this script carries the very pattern it hunts; don't self-match.
LEAKS=$(git grep -lE "kfaim|prepped|nbatopshot|Red.?[Pp]ill" -- . ':!scripts/publish_mirror.sh' | wc -l || true)
git checkout -f master
echo "public snapshot: ${COUNT} files, leak-grep hits: ${LEAKS}"
[ "${LEAKS}" = "0" ] || { echo "LEAK CHECK FAILED — not pushing"; exit 1; }
git push --force public public:main
echo "mirror refreshed: https://github.com/sushiHex/claude-oracle"
