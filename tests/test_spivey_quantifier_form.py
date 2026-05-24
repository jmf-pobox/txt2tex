"""Tests for Spivey-canonical form across forall, exists, exists1, and mu.

The generator emits the single-quantifier form required by Z RM §3.12:

    \\forall x : \\nat; y : \\nat | predicate @ expression
    \\exists x : \\nat; y : \\nat | predicate @ expression
    \\exists_1 x : \\nat; y : \\nat | predicate @ expression
    (\\mu x : \\nat; y : \\nat | predicate @ expression)

Tests 1-6 verify the Spivey-canonical output form.
Tests 7-9 are fuzz round-trip tests confirming fuzz acceptance.
Test 10 is a control confirming the single-decl path is unaffected.
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
# Helpers (mirroring tests/test_08_functions/test_lambda_multidecl_fuzz.py)
# ---------------------------------------------------------------------------

_FUZZ_PREAMBLE = """\
\\documentclass[a4paper]{{article}}
\\usepackage{{fuzz}}
\\begin{{document}}
{body}
\\end{{document}}
"""


def _fuzz_available() -> bool:
    """Return True if the fuzz binary is on PATH."""
    return shutil.which("fuzz") is not None


def _gen_expr(src: str, *, use_fuzz: bool = True) -> str:
    """Parse a txt2tex expression and return the generated LaTeX."""
    tokens = Lexer(src).tokenize()
    ast = Parser(tokens).parse()
    gen = LaTeXGenerator(use_fuzz=use_fuzz)
    if isinstance(ast, Document):
        return gen.generate_document(ast)
    return gen.generate_expr(ast)


def _gen_doc(src: str) -> str:
    """Parse a txt2tex document source and return the full LaTeX document."""
    tokens = Lexer(src).tokenize()
    ast = Parser(tokens).parse()
    assert isinstance(ast, Document)
    return LaTeXGenerator(use_fuzz=True).generate_document(ast)


def _run_fuzz(tex_content: str, tmp_path: Path) -> subprocess.CompletedProcess[str]:
    """Write tex_content to a temp file and run fuzz on it."""
    fuzz_bin = shutil.which("fuzz")
    assert fuzz_bin is not None, "fuzz binary not found on PATH"
    tex_file = tmp_path / "test.tex"
    tex_file.write_text(tex_content, encoding="utf-8")
    return subprocess.run(  # noqa: S603
        [fuzz_bin, str(tex_file)],
        capture_output=True,
        text=True,
        check=False,
    )


# ---------------------------------------------------------------------------
# Tests 1-6: Spivey-canonical form assertions (all currently XFAIL)
# ---------------------------------------------------------------------------


def test_forall_two_decl_spivey_form() -> None:
    """Two-decl forall emits a single \\forall with semicolon-separated declarations.

    Input:  (forall x : N; y : N | x < y . (x + 0))
    Target: \\forall x : \\nat; y : \\nat | x < y @ (x + 0)
    Actual: \\forall x : \\nat @ \\forall y : \\nat | x < y @ (x + 0)
    """
    result = _gen_expr("(forall x : N; y : N | x < y . (x + 0))")
    # Must contain exactly one \forall
    assert result.count(r"\forall") == 1, f"Expected single \\forall, got: {result!r}"
    # Must use semicolon to separate declarations
    assert r"\nat; y : \nat" in result, (
        f"Expected semicolon-separated declarations, got: {result!r}"
    )


def test_forall_three_decl_spivey_form() -> None:
    """Three-decl forall emits a single \\forall with two semicolons.

    Input:  forall x : N; y : N; z : N | x < y
    Target: \\forall x : \\nat; y : \\nat; z : \\nat @ x < y
    Actual: \\forall x : \\nat @ \\forall y : \\nat @ \\forall z : \\nat @ x < y
    """
    result = _gen_expr("forall x : N; y : N; z : N | x < y")
    assert result.count(r"\forall") == 1, f"Expected single \\forall, got: {result!r}"
    assert r"\nat; y : \nat; z : \nat" in result, (
        f"Expected two semicolons in declarations, got: {result!r}"
    )


def test_forall_no_predicate_no_bullet() -> None:
    """Forall with no bullet separator emits one \\forall followed by @ body.

    Input:  forall x : N; y : N | x + y > 0
    Target: \\forall x : \\nat; y : \\nat @ x + y > 0
    Actual: \\forall x : \\nat @ \\forall y : \\nat @ x + y > 0
    """
    result = _gen_expr("forall x : N; y : N | x + y > 0")
    assert result.count(r"\forall") == 1, f"Expected single \\forall, got: {result!r}"
    assert r"\nat; y : \nat" in result, (
        f"Expected semicolon-separated declarations, got: {result!r}"
    )


def test_exists_two_decl_spivey_form() -> None:
    """Two-decl exists emits a single \\exists with semicolon-separated declarations.

    Input:  exists x : N; y : N | x < y
    Target: \\exists x : \\nat; y : \\nat @ x < y
    Actual: \\exists x : \\nat @ \\exists y : \\nat @ x < y
    """
    result = _gen_expr("exists x : N; y : N | x < y")
    assert result.count(r"\exists") == 1, f"Expected single \\exists, got: {result!r}"
    assert r"\nat; y : \nat" in result, (
        f"Expected semicolon-separated declarations, got: {result!r}"
    )


def test_exists1_two_decl_spivey_form() -> None:
    """Two-decl exists1 emits a single \\exists_1 with semicolon-separated declarations.

    Input:  exists1 x : N; y : N | x < y
    Target: \\exists_1 x : \\nat; y : \\nat @ x < y
    Actual: \\exists_1 x : \\nat @ \\exists_1 y : \\nat @ x < y
    """
    result = _gen_expr("exists1 x : N; y : N | x < y")
    assert result.count(r"\exists_1") == 1, (
        f"Expected single \\exists_1, got: {result!r}"
    )
    assert r"\nat; y : \nat" in result, (
        f"Expected semicolon-separated declarations, got: {result!r}"
    )


def test_mu_two_decl_spivey_form() -> None:
    """Two-decl mu emits a single \\mu with semicolon-separated declarations.

    Input:  (mu x : N; y : N | x = y . (x + 0))
    Target: (\\mu x : \\nat; y : \\nat | x = y @ (x + 0))
    Actual: (\\mu x : \\nat | (\\mu y : \\nat | x = y @ (x + 0)))
    """
    result = _gen_expr("(mu x : N; y : N | x = y . (x + 0))")
    # Single \mu — count only "\\mu " to avoid matching "\\mu x" inside nested form
    assert result.count(r"\mu") == 1, f"Expected single \\mu, got: {result!r}"
    assert r"\nat; y : \nat" in result, (
        f"Expected semicolon-separated declarations, got: {result!r}"
    )
    # Must be parenthesized
    assert result.startswith("("), (
        f"Expected leading '(' around \\mu expression, got: {result!r}"
    )
    assert result.endswith(")"), (
        f"Expected trailing ')' around \\mu expression, got: {result!r}"
    )


# ---------------------------------------------------------------------------
# Tests 7-9: Fuzz round-trip tests
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not _fuzz_available(), reason="fuzz binary not on PATH")
def test_fuzz_accepts_forall_multi_decl(tmp_path: Path) -> None:
    """Fuzz accepts the Spivey-canonical multi-decl forall output.

    The generator now emits ``\\forall x : \\nat; y : \\nat @ x < y``
    and fuzz accepts this canonical form.
    """
    src = """\
zed
  forall x : N; y : N | x < y
end
"""
    tex = _gen_doc(src)
    result = _run_fuzz(tex, tmp_path)
    assert result.returncode == 0, (
        f"fuzz rejected forall multi-decl output\n"
        f"tex: {tex}\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )


@pytest.mark.skipif(not _fuzz_available(), reason="fuzz binary not on PATH")
def test_fuzz_accepts_exists_multi_decl(tmp_path: Path) -> None:
    """Fuzz accepts the Spivey-canonical multi-decl exists output.

    The generator now emits ``\\exists x : \\nat; y : \\nat @ x < y``
    and fuzz accepts this canonical form.
    """
    src = """\
zed
  exists x : N; y : N | x < y
end
"""
    tex = _gen_doc(src)
    result = _run_fuzz(tex, tmp_path)
    assert result.returncode == 0, (
        f"fuzz rejected exists multi-decl output\n"
        f"tex: {tex}\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )


@pytest.mark.skipif(not _fuzz_available(), reason="fuzz binary not on PATH")
def test_fuzz_accepts_mu_multi_decl(tmp_path: Path) -> None:
    """Fuzz accepts the Spivey-canonical multi-decl mu output.

    The generator now emits ``(\\mu x : \\nat; y : \\nat | x = y @ (x + 0))``
    and fuzz accepts this form.  The previously-generated nested form
    ``(\\mu x : \\nat | (\\mu y : \\nat | x = y @ (x + 0)))`` caused a
    fuzz syntax error at the closing ``)``.
    """
    src = """\
axdef
  k : N
where
  k = (mu x : N; y : N | x = y . (x + 0))
end
"""
    tex = _gen_doc(src)
    result = _run_fuzz(tex, tmp_path)
    assert result.returncode == 0, (
        f"fuzz rejected mu multi-decl output\n"
        f"tex: {tex}\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )


# ---------------------------------------------------------------------------
# Test 10: Control — single-decl quantifier must be unchanged
# ---------------------------------------------------------------------------


def test_forall_single_decl_unchanged() -> None:
    """Single-decl forall output is unaffected by the Spivey multi-decl change.

    Input:  forall x : N | x > 0
    Target: \\forall x : \\nat @ x > 0
    """
    result = _gen_expr("forall x : N | x > 0")
    assert result == r"\forall x : \nat @ x > 0", (
        f"Single-decl forall changed unexpectedly: {result!r}"
    )
