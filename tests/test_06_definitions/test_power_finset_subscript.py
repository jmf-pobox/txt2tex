"""Regression tests for issue #93: P1/F1 must emit unbraced subscripts.

fuzz rejects a braced subscript (``\\power_{1}``) on these macros with
``Syntax error at symbol "_"`` — the accepted form is unbraced
(``\\power_1``).
"""

from __future__ import annotations

from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser


def _generate(source: str) -> str:
    tokens = Lexer(source).tokenize()
    ast = Parser(tokens).parse()
    return LaTeXGenerator().generate_document(ast)


class TestPowerSetOneLaTeX:
    """Test LaTeX generation for the non-empty power set operator P1."""

    def test_p1_emits_unbraced_subscript(self) -> None:
        """P1 renders as \\power_1, not \\power_{1}."""
        latex = _generate("axdef\n  admins : P1 User\nend")
        assert r"\power_1" in latex
        assert r"\power_{1}" not in latex


class TestFiniteSetOneLaTeX:
    """Test LaTeX generation for the non-empty finite set operator F1."""

    def test_f1_emits_unbraced_subscript(self) -> None:
        """F1 renders as \\finset_1, not \\finset_{1}."""
        latex = _generate("axdef\n  activeUsers : F1 User\nend")
        assert r"\finset_1" in latex
        assert r"\finset_{1}" not in latex
