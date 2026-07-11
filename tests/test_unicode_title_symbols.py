"""Tests for bare Unicode math/Greek symbols in non-math text context.

A whiteboard author may type a bare Unicode symbol (``μ``, ``∈``, ...) inside
a section title or ``PURETEXT:`` prose line — content that never enters the
``$...$`` math pipeline.  Left untranslated, the raw glyph either hard-errors
under pdflatex ("Unicode character μ (U+03BC) not set up for use with
LaTeX") or, historically, silently disappeared from the compiled PDF.

The fix routes such characters through the same Unicode-to-LaTeX-macro table
used by the ``$...$`` bare-symbol fast path, wrapped in ``\\ensuremath{}`` so
the macro is valid whether or not the enclosing context is already math mode.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from txt2tex.compile import compile_pdf
from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser


def _generate(source: str) -> str:
    """Parse whiteboard source and return the generated LaTeX document."""
    tokens = Lexer(source).tokenize()
    ast = Parser(tokens).parse()
    gen = LaTeXGenerator(use_fuzz=True)
    return gen.generate_document(ast)


def _pdflatex_available() -> bool:
    """Return True when either latexmk or pdflatex is on PATH."""
    return shutil.which("latexmk") is not None or shutil.which("pdflatex") is not None


class TestUnicodeInSectionTitle:
    """A bare Unicode symbol in a ``=== ... ===`` title compiles cleanly."""

    def test_mu_in_title_is_not_emitted_bare(self) -> None:
        """The raw μ byte must not reach \\section*{...} untranslated."""
        latex = _generate("=== Mu Operator (μ) ===\n")
        assert r"\section*{Mu Operator (\ensuremath{\mu})}" in latex
        # The bare glyph must not survive inside the section command.
        assert "\\section*{Mu Operator (μ)}" not in latex

    def test_mu_in_title_uses_ensuremath_mu(self) -> None:
        """μ is rewritten to \\ensuremath{\\mu}, a form pdflatex can compile."""
        latex = _generate("=== Mu Operator (μ) ===\n")
        assert r"\ensuremath{\mu}" in latex

    def test_epsilon_free_ascii_title_unaffected(self) -> None:
        """A title with no Unicode symbols is unchanged (no accidental rewrite)."""
        latex = _generate("=== Ordinary Title ===\n")
        assert r"\section*{Ordinary Title}" in latex

    @pytest.mark.skipif(
        not _pdflatex_available(),
        reason="no LaTeX toolchain (pdflatex/latexmk) on PATH",
    )
    def test_mu_title_document_compiles_with_pdflatex(self, tmp_path: Path) -> None:
        """A full document with a μ section title compiles to PDF without error."""
        latex = _generate("=== Mu Operator (μ) ===\n\nTEXT: A definite description.\n")
        tex_path = tmp_path / "doc.tex"
        tex_path.write_text(latex)
        assert compile_pdf(tex_path, keep_aux=True) is True
        assert (tmp_path / "doc.pdf").exists()


class TestUnicodeInPureText:
    """A bare Unicode symbol in ``PURETEXT:`` (non-math prose) compiles cleanly."""

    def test_mu_in_puretext_is_rewritten(self) -> None:
        """μ in PURETEXT: prose is rewritten to \\ensuremath{\\mu}."""
        latex = _generate("=== Test ===\n\nPURETEXT: The operator μ is defined here.\n")
        assert r"\ensuremath{\mu}" in latex
        assert "operator μ is" not in latex
