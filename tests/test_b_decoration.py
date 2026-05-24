"""Regression tests for bare-`B` identifier decoration.

The `B:` block keyword (#138) reserved the identifier `B` overzealously, which
broke uses like `B! : P BookingId` (SBM ex14).  The lexer now only treats the
`B:` *sequence* as the block opener; bare `B` remains a usable identifier with
the full `' ? !` decoration set.
"""

from __future__ import annotations

from txt2tex.lexer import Lexer
from txt2tex.parser import Parser
from txt2tex.tokens import TokenType


def test_b_bang_as_output_decorated_identifier() -> None:
    """`B!` in a schema declaration must lex+parse as a decorated identifier."""
    src = "TITLE: T\n\ngiven X\n\nschema S\n  B! : P X\nend\n"
    tokens = Lexer(src).tokenize()
    Parser(tokens).parse()


def test_b_prime_as_after_state_identifier() -> None:
    """`B'` (after-state) must also lex+parse cleanly."""
    src = "TITLE: T\n\ngiven X\n\nschema S\n  B : X\n  B' : X\nend\n"
    tokens = Lexer(src).tokenize()
    Parser(tokens).parse()


def test_b_question_as_input_decorated_identifier() -> None:
    """`B?` (input) must also lex+parse cleanly."""
    src = "TITLE: T\n\ngiven X\n\nschema S\n  B? : X\nend\n"
    tokens = Lexer(src).tokenize()
    Parser(tokens).parse()


def test_b_colon_still_opens_block() -> None:
    """`B:` at line start (followed by content + END) still triggers B_BLOCK."""
    src = "B:\nMACHINE Foo\nEND\n"
    tokens = Lexer(src).tokenize()
    types = [t.type for t in tokens]
    assert TokenType.B_BLOCK in types
