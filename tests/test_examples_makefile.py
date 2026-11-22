"""Guard the per-directory build targets in examples/Makefile.

``make <subdir>`` builds every .txt file in one example directory by calling
``uv run txt2tex examples/<subdir>/<file>.txt`` from the repository root.  A
fake ``uv`` on PATH records the working directory and arguments of each call,
so the tests check the recipe without compiling anything.

Two properties are pinned:

* every call runs from the repository root (a bare ``cd ..`` inside the loop
  walks up one more directory on each iteration), and
* a failing file stops the loop and fails the make run.
"""

from __future__ import annotations

import os
import shutil
import stat
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"
# Directory with several .txt files, so a second iteration exists.
SUBDIR = "01_propositional_logic"
MARKER_ENV = "FAKE_UV_FAIL_MARKER"
FAKE_UV = """#!/bin/bash
echo "$PWD $*" >> "$FAKE_UV_LOG"
case "$*" in
  *"$FAKE_UV_FAIL_MARKER"*) exit 1 ;;
esac
exit 0
"""


def _make_in_examples(
    tmp_path: Path, fail_marker: str
) -> tuple[subprocess.CompletedProcess[str], list[str]]:
    """Run ``make <SUBDIR>`` in examples/ with a fake uv; return result and log."""
    make = shutil.which("make")
    if make is None:
        pytest.skip("make not found on PATH")
    bash = shutil.which("bash")
    if bash is None:
        pytest.skip("bash not found on PATH")

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    fake_uv = bin_dir / "uv"
    fake_uv.write_text(FAKE_UV, encoding="utf-8")
    fake_uv.chmod(fake_uv.stat().st_mode | stat.S_IXUSR)
    log = tmp_path / "uv.log"

    env = dict(os.environ)
    env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
    env["FAKE_UV_LOG"] = str(log)
    env[MARKER_ENV] = fail_marker
    result = subprocess.run(  # noqa: S603
        [make, "-C", str(EXAMPLES), SUBDIR],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    lines = log.read_text(encoding="utf-8").splitlines() if log.exists() else []
    return result, lines


def _subdir_files() -> list[str]:
    return sorted(p.name for p in (EXAMPLES / SUBDIR).glob("*.txt"))


def test_every_file_is_built_from_repo_root(tmp_path: Path) -> None:
    """All .txt files in the directory are built, each from the repo root."""
    files = _subdir_files()
    assert len(files) >= 2
    result, lines = _make_in_examples(tmp_path, "no-such-file-marker")
    assert result.returncode == 0, result.stderr
    assert len(lines) == len(files), lines
    for line, name in zip(lines, files, strict=True):
        cwd, _, args = line.partition(" ")
        assert Path(cwd).resolve() == ROOT, line
        assert args == f"run txt2tex examples/{SUBDIR}/{name}", line


def test_failed_file_stops_loop_and_fails_make(tmp_path: Path) -> None:
    """When the first file fails, make exits non-zero and skips the rest."""
    files = _subdir_files()
    assert len(files) >= 2
    result, lines = _make_in_examples(tmp_path, files[0])
    assert result.returncode != 0, "make reported success after a failed build"
    assert len(lines) == 1, f"loop continued after failure: {lines}"
    assert files[0] in lines[0]
    assert not any(files[1] in line for line in lines)
