"""Tests for Z slash-negation operators: `/=` (≠) and `/in` (∉).

Both are aliases for the corresponding negated standard operators
(`!=` → `\\neq`, `notin` → `\\notin`).  They appear in `BINARY_OPS` and
must also appear in `PRECEDENCE` so `_needs_parens` returns the right
answer when one is a child of a lower-precedence parent.
"""

from __future__ import annotations

from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser


def _emit(src: str) -> str:
    """Compile a small txt2tex source and return the .tex output."""
    ast = Parser(Lexer(src).tokenize()).parse()
    return LaTeXGenerator().generate_document(ast)


def test_slash_eq_emits_neq() -> None:
    r"""`x /= y` emits `\neq`."""
    src = "TITLE: t\n\naxdef\n  x, y : N\nwhere\n  x /= y\nend\n"
    assert "x \\neq y" in _emit(src)


def test_slash_in_emits_notin() -> None:
    r"""`x /in S` emits `\notin`."""
    src = "TITLE: t\n\naxdef\n  S : P N\n  x : N\nwhere\n  x /in S\nend\n"
    assert "x \\notin S" in _emit(src)


def test_slash_eq_in_precedence_table() -> None:
    """`/=` is in PRECEDENCE so paren logic treats it like `!=` (level 5)."""
    assert LaTeXGenerator.PRECEDENCE["/="] == LaTeXGenerator.PRECEDENCE["!="]


def test_slash_in_in_precedence_table() -> None:
    """`/in` is in PRECEDENCE so paren logic treats it like `notin` (level 7)."""
    assert LaTeXGenerator.PRECEDENCE["/in"] == LaTeXGenerator.PRECEDENCE["notin"]


def test_override_in_precedence_table() -> None:
    """`++` (override) is in PRECEDENCE.

    Round-4 gap: without this entry, `R o9 (S ++ T)` would lose its
    inner parens and the LaTeX reader would parse the result as
    `(R \\semi S) \\oplus T`.
    """
    assert "++" in LaTeXGenerator.PRECEDENCE


def test_cross_strictly_tighter_than_union() -> None:
    """cross binds tighter than union (parser: _parse_union calls _parse_cross)."""
    assert LaTeXGenerator.PRECEDENCE["cross"] > LaTeXGenerator.PRECEDENCE["union"]


def test_intersect_strictly_tighter_than_cross() -> None:
    """intersect binds tighter than cross.

    Parser cascade: ``_parse_cross`` calls ``_parse_intersect`` for each operand.
    """
    assert LaTeXGenerator.PRECEDENCE["intersect"] > LaTeXGenerator.PRECEDENCE["cross"]


def test_setminus_same_level_as_intersect() -> None:
    """setminus shares precedence with intersect (_parse_intersect handles both)."""
    assert LaTeXGenerator.PRECEDENCE["\\"] == LaTeXGenerator.PRECEDENCE["intersect"]
