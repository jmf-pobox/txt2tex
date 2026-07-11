"""Tests for visible parens around a nested `Superscript` base.

`(z^2)^3` used to render as `{z \\bsup 2 \\esup} \\bsup 3 \\esup` -- the
inner `(z^2)` collapsed to invisible LaTeX grouping (`{...}`), so a reader
saw `z^2^3` with no visible parens, losing the exponent-of-exponent
grouping.  A `Superscript` whose base is itself a `Superscript` must
render with VISIBLE parens instead, in both fuzz and `--zed` mode:
`(z \\bsup 2 \\esup) \\bsup 3 \\esup`.

Numeric nested towers (`(z^2)^3` with `z : Z`) now raise
`NumericSuperscriptError` in fuzz mode (see
``test_numeric_superscript_reject.py``), so the fuzz-mode test vehicle
here is a RELATIONAL nested tower -- `(r^2)^3` with `r : S <-> S`, valid
iteration `iter 3 (iter 2 r)` -- which must both render with visible
parens and still type-check under fuzz.
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


def _gen(src: str, *, use_fuzz: bool) -> str:
    """Parse txt2tex source and return the full generated LaTeX document."""
    tokens = Lexer(src).tokenize()
    ast = Parser(tokens).parse()
    assert isinstance(ast, Document)
    return LaTeXGenerator(use_fuzz=use_fuzz).generate_document(ast)


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
        timeout=120,
    )


# ---------------------------------------------------------------------------
# --zed mode: (z^2)^3 renders with visible parens
# ---------------------------------------------------------------------------


class TestZedModeNestedSuperscriptVisibleParens:
    """`(z^2)^3` under `--zed` renders `(z \\bsup 2 \\esup) \\bsup 3 \\esup`."""

    SRC = "Z2 == (z^2)^3\n"

    def test_renders_visible_parens(self) -> None:
        tex = _gen(self.SRC, use_fuzz=False)
        assert r"(z \bsup 2 \esup) \bsup 3 \esup" in tex

    def test_does_not_render_invisible_braces(self) -> None:
        tex = _gen(self.SRC, use_fuzz=False)
        assert r"{z \bsup 2 \esup}" not in tex


# ---------------------------------------------------------------------------
# Fuzz mode, relational base: (r^2)^3 renders with visible parens and passes
# ---------------------------------------------------------------------------


class TestFuzzModeRelationalNestedSuperscriptVisibleParens:
    """`(r^2)^3` where `r : S <-> S` -- genuine iteration, visible parens."""

    SRC = "given S\naxdef\n  r : S <-> S\nend\n\nRR2 == (r^2)^3\n"

    def test_renders_visible_parens(self) -> None:
        tex = _gen(self.SRC, use_fuzz=True)
        assert r"(r \bsup 2 \esup) \bsup 3 \esup" in tex

    def test_does_not_render_invisible_braces(self) -> None:
        tex = _gen(self.SRC, use_fuzz=True)
        assert r"{r \bsup 2 \esup}" not in tex

    @pytest.mark.skipif(not _fuzz_available(), reason="fuzz binary not on PATH")
    def test_fuzz_accepts_the_nested_iteration(self, tmp_path: Path) -> None:
        r"""Fuzz accepts `(r \bsup 2 \esup) \bsup 3 \esup` as `iter 3 (iter 2 r)`."""
        full_tex = _gen(self.SRC, use_fuzz=True)
        result = _run_fuzz(full_tex, tmp_path)
        assert result.returncode == 0, (
            f"fuzz rejected the visibly-parenthesised nested iteration\n"
            f"tex:\n{full_tex}\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )
