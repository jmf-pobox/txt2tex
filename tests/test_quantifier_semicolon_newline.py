"""Regression tests for a newline after ';' in a quantifier prefix.

The parser previously raised ``Expected variable name after ';' in quantifier``
when a natural newline (or explicit ``\\`` continuation) appeared immediately
after ``;`` in a semicolon-chained quantifier prefix.

Fix: ``_parse_quantifier_continuation`` now skips newlines at its top, mirroring
the existing post-``|`` line-break handling.
"""

from __future__ import annotations

from txt2tex.ast_nodes import Document
from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser


def _gen_expr(src: str, *, use_fuzz: bool = True) -> str:
    """Parse a txt2tex expression and return the generated LaTeX."""
    tokens = Lexer(src).tokenize()
    ast = Parser(tokens).parse()
    gen = LaTeXGenerator(use_fuzz=use_fuzz)
    if isinstance(ast, Document):
        return gen.generate_document(ast)
    return gen.generate_expr(ast)


# ---------------------------------------------------------------------------
# Test 1 — sanity: newline AFTER pipe (existing, should still work)
# ---------------------------------------------------------------------------


def test_newline_after_pipe_sanity() -> None:
    """Newline after '|' in a two-decl forall parses without error.

    This is the existing behaviour.
    Included as a sanity regression to ensure the new fix does not
    disturb the post-'|' line-break path.
    """
    src = "forall x : N; y : N |\n  x < y"
    result = _gen_expr(src)
    assert r"\forall" in result
    assert "x" in result
    assert "y" in result


# ---------------------------------------------------------------------------
# Test 2 — the bug: newline AFTER first ';'
# ---------------------------------------------------------------------------


def test_newline_after_first_semicolon() -> None:
    """Newline immediately after the first ';' in a two-decl forall is accepted.

    Before the fix this raised:
        Expected variable name after ';' in quantifier
    """
    src = "forall x : N;\n y : N | x < y"
    result = _gen_expr(src)
    assert r"\forall" in result
    assert "x" in result
    assert "y" in result


# ---------------------------------------------------------------------------
# Test 3 — newline after trailing ';' in a three-decl chain
# ---------------------------------------------------------------------------


def test_newline_after_trailing_semicolon() -> None:
    """Newline after the second ';' in a three-decl forall is accepted."""
    src = "forall x : N; y : N;\n z : N | x < y"
    result = _gen_expr(src)
    assert r"\forall" in result
    assert "z" in result


# ---------------------------------------------------------------------------
# Test 4 — explicit backslash continuation after ';'
# ---------------------------------------------------------------------------


def test_backslash_continuation_after_semicolon() -> None:
    """An explicit '\\' continuation after ';' is accepted."""
    src = "forall x : N; \\\n y : N | x < y"
    result = _gen_expr(src)
    assert r"\forall" in result
    assert "x" in result
    assert "y" in result


# ---------------------------------------------------------------------------
# Test 5 — three-way chain with a newline after the second ';'
# ---------------------------------------------------------------------------


def test_three_way_chain_newline_after_second_semicolon() -> None:
    """Three-decl exists with newline after the second ';' parses cleanly.

    Shape under test:
        exists d : Date; c : Venue;
               att : N | body
    """
    src = "exists d : Date; c : Venue;\n  att : N | att > 0"
    result = _gen_expr(src)
    assert r"\exists" in result
    assert "d" in result
    assert "c" in result
    assert "att" in result


# ---------------------------------------------------------------------------
# Test 6 — newline after EVERY ';' in a three-decl chain
# ---------------------------------------------------------------------------


def test_newline_after_every_semicolon() -> None:
    """Newlines after each ';' in a three-decl forall are all accepted."""
    src = "forall x : N;\n  y : N;\n  z : N | x < y"
    result = _gen_expr(src)
    assert r"\forall" in result
    assert "x" in result
    assert "y" in result
    assert "z" in result
