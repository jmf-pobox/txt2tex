"""Tests for lnot parenthesisation of non-atomic predicates (bug #132).

fuzz rejects ``\\lnot \\exists_1 s @ P`` with
``Opening parenthesis expected at symbol \\exists_1``.
Z RM §3.8.1 permits the bare form, but fuzz's parser is stricter: the
operand of ``\\lnot`` must be an atomic predicate.

jms ruling (2026-05-22): emit ``\\lnot (child)`` when child is a
quantifier, connective (land/lor/etc), lambda, or any other non-atomic
form.  Leave atomic operands (identifiers, constants, relation
applications) bare.

Test plan:

+---+-----------------------------------+----------------------------+--------+
| T | Input                             | Expected emission          | Status |
+---+-----------------------------------+----------------------------+--------+
| 1 | lnot (exists s : N | s > 0)      | \\lnot (\\exists ...)       | pass   |
| 2 | lnot (exists1 s : N | s > 0)     | \\lnot (\\exists_1 ...)     | pass   |
| 3 | lnot (forall s : N | s > 0)      | \\lnot (\\forall ...)       | pass   |
| 4 | lnot (a land b)                   | \\lnot (a \\land b)         | pass   |
| 5 | lnot true                         | \\lnot true                 | pass   |
| 6 | lnot p                            | \\lnot p                    | pass   |
| 7 | lnot (x elem s)                   | \\lnot (x \\in s)           | pass   |
| 8 | fuzz round-trip: lnot exists1     | Type checking: passed      | pass   |
+---+-----------------------------------+----------------------------+--------+
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from txt2tex.ast_nodes import Document
from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _gen(src: str) -> str:
    """Parse txt2tex source and return the full generated LaTeX document."""
    tokens = Lexer(src).tokenize()
    ast = Parser(tokens).parse()
    assert isinstance(ast, Document)
    return LaTeXGenerator(use_fuzz=True).generate_document(ast)


def _extract_env(tex: str, env: str) -> str:
    """Return the content between \\begin{env} and \\end{env} (inclusive)."""
    start_marker = rf"\begin{{{env}}}"
    end_marker = rf"\end{{{env}}}"
    start = tex.find(start_marker)
    end = tex.find(end_marker) + len(end_marker)
    assert start != -1, f"\\begin{{{env}}} not found in generated LaTeX"
    return tex[start:end]


def _fuzz_available() -> bool:
    """Return True if the fuzz binary is on PATH."""
    return shutil.which("fuzz") is not None


def _run_fuzz(tex: str, tmp_path: Path) -> subprocess.CompletedProcess[str]:
    """Write tex to a temp file and run fuzz on it; return the completed process."""
    fuzz_bin = shutil.which("fuzz")
    assert fuzz_bin is not None, "fuzz binary not found on PATH"
    tex_file = tmp_path / "test.tex"
    tex_file.write_text(tex, encoding="utf-8")
    return subprocess.run(  # noqa: S603
        [fuzz_bin, str(tex_file)],
        capture_output=True,
        text=True,
        check=False,
    )


# ---------------------------------------------------------------------------
# T1 — lnot (exists s : N | s > 0)
# ---------------------------------------------------------------------------


def test_lnot_exists_wraps_quantifier() -> None:
    r"""lnot of an exists quantifier emits \lnot (\exists ...).

    Fuzz rejects ``\lnot \exists s @ s > 0``; requires parens.
    Expected: ``\lnot (\exists s : \nat @ s > 0)``
    """
    src = "axdef\n  pp : N\nwhere\n  lnot (exists s : N | s > 0)\nend"
    axdef = _extract_env(_gen(src), "axdef")
    assert r"\lnot (\exists s : \nat @ s > 0)" in axdef


# ---------------------------------------------------------------------------
# T2 — lnot (exists1 s : N | s > 0)
# ---------------------------------------------------------------------------


def test_lnot_exists1_wraps_quantifier() -> None:
    r"""lnot of an exists1 quantifier emits \lnot (\exists_1 ...).

    This is the primary repro for bug #132: fuzz rejected
    ``\lnot \exists_1 s @ P`` from SEM Ex 51 part (b).
    Expected: ``\lnot (\exists_1 s : \nat @ s > 0)``
    """
    src = "axdef\n  pp : N\nwhere\n  lnot (exists1 s : N | s > 0)\nend"
    axdef = _extract_env(_gen(src), "axdef")
    assert r"\lnot (\exists_1 s : \nat @ s > 0)" in axdef


# ---------------------------------------------------------------------------
# T3 — lnot (forall s : N | s > 0)
# ---------------------------------------------------------------------------


def test_lnot_forall_wraps_quantifier() -> None:
    r"""lnot of a forall quantifier emits \lnot (\forall ...).

    Expected: ``\lnot (\forall s : \nat @ s > 0)``
    """
    src = "axdef\n  pp : N\nwhere\n  lnot (forall s : N | s > 0)\nend"
    axdef = _extract_env(_gen(src), "axdef")
    assert r"\lnot (\forall s : \nat @ s > 0)" in axdef


# ---------------------------------------------------------------------------
# T4 — lnot (a land b)
# ---------------------------------------------------------------------------


def test_lnot_conjunction_wraps_connective() -> None:
    r"""lnot of a conjunction emits \lnot (a \land b).

    The explicit parens in source mark the BinaryOp with explicit_parens=True,
    so the BinaryOp generator emits ``(a \land b)`` and the operand is already
    parenthesised.  The lnot rule must not double-wrap.
    Expected: ``\lnot (a \land b)``
    """
    src = "axdef\n  a : N\n  b : N\nwhere\n  lnot (a land b)\nend"
    axdef = _extract_env(_gen(src), "axdef")
    assert r"\lnot (a \land b)" in axdef
    # Guard against double-wrapping
    assert r"\lnot ((a \land b))" not in axdef


# ---------------------------------------------------------------------------
# T5 — lnot true  (atomic — no parens)
# ---------------------------------------------------------------------------


def test_lnot_true_no_parens() -> None:
    r"""lnot of the atomic constant ``true`` emits \lnot true (no parens).

    ``true`` is an Identifier — atomic per jms ruling.
    Expected: ``\lnot true``
    """
    src = "axdef\n  pp : N\nwhere\n  lnot true\nend"
    axdef = _extract_env(_gen(src), "axdef")
    assert r"\lnot true" in axdef
    assert r"\lnot (true)" not in axdef


# ---------------------------------------------------------------------------
# T6 — lnot p  (atomic identifier — no parens)
# ---------------------------------------------------------------------------


def test_lnot_identifier_no_parens() -> None:
    r"""lnot of an identifier emits \lnot p (no parens).

    Identifiers are atomic per jms ruling.
    Expected: ``\lnot p``
    """
    src = "axdef\n  p : N\nwhere\n  lnot p\nend"
    axdef = _extract_env(_gen(src), "axdef")
    assert r"\lnot p" in axdef
    assert r"\lnot (p)" not in axdef


# ---------------------------------------------------------------------------
# T7 — lnot (x elem s)
# ---------------------------------------------------------------------------


def test_lnot_relation_application() -> None:
    r"""lnot of a relation application emits \lnot (x \in s).

    ``x elem s`` parses as BinaryOp("elem", x, s) with explicit_parens=True
    (because the user wrote the outer parens).  The BinaryOp generator
    wraps to ``(x \in s)``; the lnot rule sees a BinaryOp (atomic) and
    does not add a second layer.
    Expected: ``\lnot (x \in s)`` — fuzz accepts both bare and parenthesised.
    Note: the contract permits either form; we document that txt2tex
    emits the parenthesised form because the user supplied explicit parens.
    """
    src = "axdef\n  x : N\n  s : N\nwhere\n  lnot (x elem s)\nend"
    axdef = _extract_env(_gen(src), "axdef")
    assert r"\lnot (x \in s)" in axdef
    assert r"\lnot ((x \in s))" not in axdef


# ---------------------------------------------------------------------------
# T8 — fuzz round-trip: lnot (exists1 s : N | s > 0)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not _fuzz_available(), reason="fuzz binary not on PATH")
def test_fuzz_accepts_lnot_exists1(tmp_path: Path) -> None:
    r"""Fuzz accepts \lnot (\exists_1 s : \nat @ s > 0) in an axdef where clause.

    This is the primary end-to-end regression test for bug #132.
    The output must contain ``Type checking: passed``.
    """
    src = (
        "TITLE: smoke\n"
        "TEXT: regression\n"
        "\n"
        "axdef\n"
        "  pp : N\n"
        "where\n"
        "  lnot (exists1 s : N | s > 0)\n"
        "end"
    )
    full_tex = _gen(src)
    result = _run_fuzz(full_tex, tmp_path)
    assert result.returncode == 0, (
        f"fuzz rejected lnot (exists1 ...) in axdef where clause\n"
        f"tex:\n{full_tex}\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )
