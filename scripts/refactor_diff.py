"""Verify the txt2tex IO contract during refactors.

Generates `.tex` from a corpus of `.txt` inputs in either capture or verify
mode.  The contract is byte-equality of the generated `.tex`; anything else
is a refactor that did not preserve observable behaviour.

Usage::

    # 1. Capture a baseline from the *current* working tree:
    python scripts/refactor_diff.py capture .tmp/refactor-baseline

    # 2. Make refactoring changes.

    # 3. Verify the current working tree against the baseline:
    python scripts/refactor_diff.py verify .tmp/refactor-baseline

The corpus is `examples/**/*.txt` plus `tests/bugs/*.txt`.  Inputs that
the parser deliberately rejects (some bug fixtures are negative
regressions) are tolerated: their generation failure is recorded as a
sentinel file so that "now succeeds" and "still rejected" are both
visible across runs.

Exit status:
    0 — all generated `.tex` files match the baseline byte-for-byte.
    1 — at least one difference, or baseline coverage gap.
    2 — usage error.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# Resolve the project root from the current working directory, not from
# the script's __file__ location.  refactor_diff_vs_ref.sh runs this
# script from inside a temporary worktree
# (``cd $WT && python $REPO/scripts/refactor_diff.py capture ...``),
# and we want both the corpus enumeration and the ``txt2tex``
# subprocess invocation to be relative to that worktree — otherwise
# the "baseline" capture is taken from the current branch's checkout
# and the gate compares the tree against itself.
ROOT = Path.cwd().resolve()
EXAMPLES_DIR = ROOT / "examples"
BUGS_DIR = ROOT / "tests" / "bugs"
EXCLUDED_DIRS = {EXAMPLES_DIR / "infrastructure"}

# Sentinel file written when txt2tex exits non-zero or produces no .tex.
# A capture run that *succeeded* writes the actual .tex; a capture run that
# *failed* writes this marker.  Verify compares the two sets element-wise.
FAILURE_SENTINEL = "<<txt2tex did not produce .tex output>>\n"


def collect_corpus() -> list[Path]:
    """Return all .txt inputs in deterministic order."""
    paths: list[Path] = []
    for txt in sorted(EXAMPLES_DIR.rglob("*.txt")):
        if any(txt.is_relative_to(d) for d in EXCLUDED_DIRS):
            continue
        paths.append(txt)
    paths.extend(sorted(BUGS_DIR.glob("*.txt")))
    return paths


def out_key(txt: Path) -> str:
    """Flat, filesystem-safe key for the input file (basename in baseline dir).

    Use POSIX separators in the key so capture and verify produce the
    same key on Windows and POSIX hosts.
    """
    rel = txt.relative_to(ROOT)
    return rel.as_posix().replace("/", "__").removesuffix(".txt") + ".tex"


def generate_one(txt: Path, dst: Path) -> tuple[Path, bool]:
    """Run txt2tex on `txt`, write output to `dst`.  Return (dst, ok)."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    uv = shutil.which("uv")
    if uv is None:
        print("ERROR: uv not found on PATH", file=sys.stderr)
        sys.exit(2)
    result = subprocess.run(
        [
            uv,
            "run",
            "txt2tex",
            str(txt),
            "--tex-only",
            "-o",
            str(dst),
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=str(ROOT),
    )
    if result.returncode != 0 or not dst.exists():
        # Record the failure so verify can detect a *change* in failure status.
        dst.write_text(FAILURE_SENTINEL)
        return dst, False
    return dst, True


def capture(target: Path) -> int:
    """Run txt2tex on every corpus input; write outputs into `target/`."""
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True)
    corpus = collect_corpus()
    ok = 0
    fail = 0
    for txt in corpus:
        dst = target / out_key(txt)
        _, success = generate_one(txt, dst)
        if success:
            ok += 1
        else:
            fail += 1
    print(f"capture: {ok} ok, {fail} failed/rejected, total {len(corpus)} → {target}")
    return 0


def verify(baseline: Path) -> int:
    """Regenerate, diff each .tex against `baseline/`."""
    if not baseline.is_dir():
        print(f"ERROR: baseline not found: {baseline}", file=sys.stderr)
        return 2
    corpus = collect_corpus()
    mismatches: list[tuple[Path, str]] = []
    missing_baseline: list[Path] = []
    for txt in corpus:
        key = out_key(txt)
        base = baseline / key
        if not base.exists():
            missing_baseline.append(txt)
            continue
        # Generate to a sibling temp area
        with tempfile.TemporaryDirectory() as tmp:
            dst = Path(tmp) / key
            generate_one(txt, dst)
            base_bytes = base.read_bytes()
            new_bytes = dst.read_bytes()
            if base_bytes != new_bytes:
                # Categorize: failure → success, success → failure, content change
                base_was_failure = base_bytes == FAILURE_SENTINEL.encode()
                new_is_failure = new_bytes == FAILURE_SENTINEL.encode()
                if base_was_failure and not new_is_failure:
                    reason = "now succeeds (baseline rejected)"
                elif new_is_failure and not base_was_failure:
                    reason = "now rejected (baseline succeeded)"
                else:
                    reason = "content differs"
                mismatches.append((txt, reason))
    if mismatches:
        print(f"FAIL: {len(mismatches)} mismatches:")
        for txt, reason in mismatches:
            print(f"  {txt.relative_to(ROOT)}: {reason}")
        if missing_baseline:
            print(
                f"FAIL: {len(missing_baseline)} inputs are missing from the "
                f"baseline (baseline coverage gap; rerun capture).",
                file=sys.stderr,
            )
        return 1
    if missing_baseline:
        # No mismatches among compared inputs, but the baseline does not
        # cover the current corpus.  This is a coverage gap: the gate has
        # not actually verified those inputs.  Per the module docstring,
        # exit 1.
        print(
            f"FAIL: {len(missing_baseline)} inputs are missing from the "
            f"baseline (baseline coverage gap; rerun capture).",
            file=sys.stderr,
        )
        for txt in missing_baseline:
            print(f"  {txt.relative_to(ROOT)}: missing baseline", file=sys.stderr)
        return 1
    print(f"PASS: {len(corpus)} inputs match baseline")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    cap = sub.add_parser("capture", help="snapshot .tex outputs to a directory")
    cap.add_argument("target", type=Path)
    ver = sub.add_parser("verify", help="diff current outputs against a baseline")
    ver.add_argument("baseline", type=Path)
    args = parser.parse_args()
    if args.cmd == "capture":
        return capture(args.target)
    return verify(args.baseline)


if __name__ == "__main__":
    raise SystemExit(main())
