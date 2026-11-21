"""Guard the public repo against machine-local or private tracked files.

This repository is public.  `.env` files, ethos session logs and ethos
mission records hold machine paths, personal data and private session
transcripts, so none of them may be committed.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path, PurePosixPath

import pytest

ROOT = Path(__file__).resolve().parents[1]
ALLOWED_ENV_FILES = frozenset({".env.example"})
ETHOS_PRIVATE_DIRS = (
    ".punt-labs/ethos/sessions/",
    ".punt-labs/ethos/missions/",
)
ETHOS_PRIVATE_FILES = frozenset({".punt-labs/ethos/missions.jsonl"})


@pytest.fixture(scope="module")
def tracked_files() -> tuple[str, ...]:
    """Return every path tracked by git, relative to the repo root."""
    git = shutil.which("git")
    if git is None:
        pytest.skip("git not available")
    if not (ROOT / ".git").exists():
        pytest.skip("not a git checkout")
    result = subprocess.run(  # noqa: S603
        [git, "ls-files", "-z"],
        cwd=ROOT,
        capture_output=True,
        check=True,
    )
    return tuple(p.decode() for p in result.stdout.split(b"\0") if p)


def test_no_env_files_tracked(tracked_files: tuple[str, ...]) -> None:
    """Forbid tracked `.env` and `.env.*` files, except `.env.example`."""
    offenders = [
        path
        for path in tracked_files
        if (name := PurePosixPath(path).name) not in ALLOWED_ENV_FILES
        and (name == ".env" or name.startswith(".env."))
    ]
    assert not offenders, f"tracked .env files: {offenders}"


def test_no_ethos_session_or_mission_records_tracked(
    tracked_files: tuple[str, ...],
) -> None:
    """Forbid tracked ethos session logs and mission records."""
    offenders = [
        path
        for path in tracked_files
        if path.startswith(ETHOS_PRIVATE_DIRS) or path in ETHOS_PRIVATE_FILES
    ]
    assert not offenders, f"tracked ethos session/mission records: {offenders}"
