"""End-to-end regression tests: Stage A (generation fixture assertions).

Each .txt file under examples/ (excluding examples/infrastructure/ which
contains no .txt files) is run through ``txt2tex --tex-only -o <tmp_path>``
and the generated .tex is compared byte-for-byte against the committed
.tex fixture using ``read_bytes()``.  This catches accidental encoding
changes, CRLF/LF drift, and trailing-whitespace differences that
``read_text()`` would silently normalize away.

Path collection is at module level so pytest-xdist can distribute tests
across workers correctly. A lazy generator inside the test function body
would not parallelize under xdist.

Scope: Phase 1 only (Stage A). Stage B (latexmk compilation) and Stage C
(fuzz type-check) are NOT implemented here — see docs/development/TEST_PLAN.md.

To regenerate committed fixtures after a legitimate generator change::

    make regen-e2e

Then inspect ``git diff examples/`` before committing.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Module-level path collection
# ---------------------------------------------------------------------------
# Resolve the repository root relative to this file. Avoids subprocess
# overhead at collection time and works regardless of cwd when pytest runs.
_REPO_ROOT = Path(__file__).parent.parent.resolve()
_EXAMPLES_DIR = _REPO_ROOT / "examples"

# Excluded subtrees — infrastructure/ contains no .txt files; listed
# explicitly so the exclusion is documented and robust against future additions.
_EXCLUDED_DIRS = {
    _EXAMPLES_DIR / "infrastructure",
}


def _collect_example_paths() -> list[tuple[Path, Path]]:
    """Return [(source.txt, fixture.tex), ...] for every participating example.

    Sorted for deterministic parametrize order across platforms.
    """
    pairs: list[tuple[Path, Path]] = []
    for txt_path in sorted(_EXAMPLES_DIR.rglob("*.txt")):
        # Skip excluded subtrees.
        if any(txt_path.is_relative_to(excluded) for excluded in _EXCLUDED_DIRS):
            continue
        tex_path = txt_path.with_suffix(".tex")
        pairs.append((txt_path, tex_path))
    return pairs


# Collected once at import time — required for correct xdist work distribution.
_EXAMPLE_PAIRS: list[tuple[Path, Path]] = _collect_example_paths()

# Parametrize IDs: relative path from examples/ root, POSIX separators.
# e.g. "01_propositional_logic/basic_operators"
_EXAMPLE_IDS: list[str] = [
    txt.relative_to(_EXAMPLES_DIR).with_suffix("").as_posix()
    for txt, _ in _EXAMPLE_PAIRS
]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.e2e
@pytest.mark.parametrize(("txt_path", "tex_fixture"), _EXAMPLE_PAIRS, ids=_EXAMPLE_IDS)
def test_generation(txt_path: Path, tex_fixture: Path, tmp_path: Path) -> None:
    """Stage A: generated .tex must match the committed fixture exactly.

    Invocation: ``uv run txt2tex <source.txt> --tex-only -o <tmp_path/stem.tex>``

    The ``-o`` flag writes the output to tmp_path, keeping the source directory
    clean and making parallel runs under pytest-xdist safe.
    """
    uv = shutil.which("uv")
    if uv is None:
        pytest.skip("uv not found on PATH — cannot invoke txt2tex")

    # Each test gets its own tmp_path from pytest; the .tex goes here.
    generated_tex = tmp_path / txt_path.with_suffix(".tex").name

    result = subprocess.run(  # noqa: S603
        [
            uv,
            "run",
            "txt2tex",
            str(txt_path),
            "--tex-only",
            "-o",
            str(generated_tex),
        ],
        capture_output=True,
        text=True,
        check=False,
        cwd=str(_REPO_ROOT),
    )

    # Stage A asserts only on .tex content. Non-zero exit codes from fuzz
    # type-checking (Stage C) are not a Stage A failure — the .tex file is
    # generated before fuzz runs. Fail only if the .tex was not written at all.
    if not generated_tex.exists():
        pytest.fail(
            f"txt2tex did not produce output at {generated_tex} "
            f"for {txt_path.relative_to(_REPO_ROOT)}\n"
            f"exit code: {result.returncode}\n"
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}"
        )

    # Fixture must exist — if missing, collection logic or fixture state is broken.
    assert tex_fixture.exists(), (
        f"Committed fixture not found: {tex_fixture}. "
        "Run 'make regen-e2e' to generate it."
    )

    generated = generated_tex.read_bytes()
    fixture = tex_fixture.read_bytes()

    if generated != fixture:
        # Surface a contextual diff to pinpoint the regression.
        # Decode for display only — the byte comparison above is the gate.
        gen_text = generated.decode("utf-8", errors="replace")
        fix_text = fixture.decode("utf-8", errors="replace")
        gen_lines = gen_text.splitlines(keepends=True)
        fix_lines = fix_text.splitlines(keepends=True)

        diff_lines: list[str] = []
        shown = 0
        pairs = enumerate(zip(gen_lines, fix_lines, strict=False), start=1)
        for i, (gen_line, fix_line) in pairs:
            if gen_line != fix_line:
                diff_lines.append(f"  line {i}:")
                diff_lines.append(f"    fixture:   {fix_line.rstrip()!r}")
                diff_lines.append(f"    generated: {gen_line.rstrip()!r}")
                shown += 1
                if shown >= 10:
                    diff_lines.append("  ... (truncated after 10 differing lines)")
                    break

        if len(gen_lines) != len(fix_lines):
            diff_lines.append(
                f"  line count: fixture={len(fix_lines)}, generated={len(gen_lines)}"
            )

        rel = txt_path.relative_to(_REPO_ROOT)
        pytest.fail(
            f"Generated .tex differs from fixture for {rel}\n"
            f"Fixture:   {tex_fixture}\n"
            f"Generated: {generated_tex}\n"
            f"Regenerate with: make regen-e2e\n\n" + "\n".join(diff_lines)
        )
