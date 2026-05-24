#!/usr/bin/env bash
# refactor_diff_vs_ref.sh — verify .tex byte-equality vs a git reference.
#
# Captures a baseline by checking out <ref> in a temporary worktree,
# running scripts/refactor_diff.py from that worktree, then verifying
# the current branch's output against that baseline.  The worktree is
# torn down whether the script succeeds or fails.
#
# Usage:
#     scripts/refactor_diff_vs_ref.sh                # compare HEAD to main
#     scripts/refactor_diff_vs_ref.sh origin/main    # compare HEAD to origin/main
#     scripts/refactor_diff_vs_ref.sh d97bb88        # compare HEAD to a specific commit
#
# Exit status mirrors scripts/refactor_diff.py verify (0 on byte-match).

set -euo pipefail

REF="${1:-main}"
ROOT="$(git rev-parse --show-toplevel)"
WT="$ROOT/.tmp/refactor-baseline-wt"
BASELINE_DIR="$ROOT/.tmp/refactor-baseline-${REF//\//_}"

cleanup() {
    if [ -d "$WT" ]; then
        git worktree remove --force "$WT" >/dev/null 2>&1 || true
    fi
}
trap cleanup EXIT

# Fresh worktree at <ref>.
rm -rf "$WT"
git worktree add --detach "$WT" "$REF" >/dev/null

# Capture from the worktree so txt2tex resolves to <ref>'s source tree.
echo "Capturing baseline from $REF ..."
(cd "$WT" && uv run python "$ROOT/scripts/refactor_diff.py" capture "$BASELINE_DIR")

# Verify current working tree (this branch / HEAD with uncommitted edits) against baseline.
echo "Verifying current working tree against baseline ..."
uv run python "$ROOT/scripts/refactor_diff.py" verify "$BASELINE_DIR"
