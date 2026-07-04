"""Tests for the `setminus` keyword: word alias for the `\\` set-difference operator.

Docs (`docs/reference.tex:272`, precedence table line 1088) document
`A setminus B` -> `A \\setminus B`, but the *word* `setminus` was missing
from `KEYWORD_TO_TOKEN`, so it lexed as a bare identifier and `A setminus B`
parsed as function application (`A(setminus)(B)`) instead of set difference.
"""

from __future__ import annotations

import pytest

from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import RESERVED_WORDS, Lexer, LexerError
from txt2tex.parser import Parser
from txt2tex.tokens import TokenType


def _emit(src: str) -> str:
    """Compile a small txt2tex source and return the .tex output."""
    ast = Parser(Lexer(src).tokenize()).parse()
    return LaTeXGenerator().generate_document(ast)


def test_setminus_keyword_lexes_as_setminus_token() -> None:
    """`setminus` lexes to a SETMINUS token, not IDENTIFIER."""
    tokens = Lexer("A setminus B").tokenize()
    assert [t.type for t in tokens[:3]] == [
        TokenType.IDENTIFIER,
        TokenType.SETMINUS,
        TokenType.IDENTIFIER,
    ]
    assert tokens[1].value == "setminus"


def test_setminus_word_emits_backslash_setminus() -> None:
    r"""`A setminus B` emits `A \setminus B`, not `A(setminus)(B)`."""
    src = "TITLE: t\n\naxdef\n  A, B : P N\nwhere\n  A setminus B = A\nend\n"
    latex = _emit(src)
    assert "A \\setminus B" in latex
    assert "(setminus)" not in latex


def test_setminus_word_in_precedence_table() -> None:
    """`setminus` shares precedence with `\\` (same operator, alternate spelling)."""
    assert LaTeXGenerator.PRECEDENCE["setminus"] == LaTeXGenerator.PRECEDENCE["\\"]


def test_setminus_word_in_binary_ops_table() -> None:
    """`setminus` maps to the same LaTeX macro as the `\\` symbol form."""
    assert LaTeXGenerator.BINARY_OPS["setminus"] == LaTeXGenerator.BINARY_OPS["\\"]


def test_setminus_word_form_zed_paragraph() -> None:
    r"""`RelA setminus RelB` in a zed abbreviation emits `\setminus`."""
    src = "zed\n  C == RelA setminus RelB\nend\n"
    latex = _emit(src)
    assert "RelA \\setminus RelB" in latex
    assert "(setminus)" not in latex


def test_setminus_in_reserved_words() -> None:
    """`setminus` is in RESERVED_WORDS, like `union`/`intersect`."""
    assert "setminus" in RESERVED_WORDS


def test_setminus_decoration_is_rejected() -> None:
    r"""`setminus?` must raise, not lex as a decorated identifier.

    Reserved set operators cannot be decorated; `setminus` was missing from
    RESERVED_WORDS, so `setminus?` silently lexed as a decorated identifier
    instead of raising the reserved-keyword-decoration error.
    """
    with pytest.raises(LexerError, match=r"[Cc]annot decorate reserved keyword"):
        Lexer("zed\n  x == A setminus? B\nend\n").tokenize()
