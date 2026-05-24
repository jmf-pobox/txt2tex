"""Regression tests for bug #144: newline after '|' and ';' in set-comprehension.

The parser previously raised ``Expected identifier, number, '(', '{', '{|',
'⟨', or lambda, got NEWLINE`` when a natural newline (or explicit ``\\``
continuation) appeared immediately after ``|`` or ``;`` in a set-comprehension
binding-prefix.

Fix: the two sites in ``_parse_set_comprehension_from_brace`` now carry the
same CONTINUATION/NEWLINE skip block used by ``_parse_quantifier_continuation``
since #131.
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
# Test 1 — newline after '|', single binding
# ---------------------------------------------------------------------------


def test_newline_after_pipe_single_binding() -> None:
    """Newline immediately after '|' in a single-binding comprehension is accepted.

    Before the fix this raised:
        Expected identifier, number, '(', '{', '{|', '⟨', or lambda, got NEWLINE
    """
    src = "{ x : T |\n  x > 0 . x }"
    result = _gen_expr(src)
    assert "x" in result


# ---------------------------------------------------------------------------
# Test 2 — newline after '|', two bindings
# ---------------------------------------------------------------------------


def test_newline_after_pipe_two_bindings() -> None:
    """Newline after '|' in a two-binding comprehension is accepted."""
    src = "{ x : T; y : U |\n  x > 0 . x }"
    result = _gen_expr(src)
    assert "x" in result
    assert "y" in result


# ---------------------------------------------------------------------------
# Test 3 — newline after ';'
# ---------------------------------------------------------------------------


def test_newline_after_semicolon() -> None:
    """Newline immediately after ';' in a two-binding comprehension is accepted.

    Before the fix this was silently accepted only when the bare-newline path
    happened to match; explicit CONTINUATION was not handled.
    """
    src = "{ x : T;\n  y : U | x > 0 . x }"
    result = _gen_expr(src)
    assert "x" in result
    assert "y" in result


# ---------------------------------------------------------------------------
# Test 4 — explicit backslash continuation after ';'
# ---------------------------------------------------------------------------


def test_backslash_continuation_after_semicolon() -> None:
    r"""An explicit '\\' continuation after ';' in a set comprehension is accepted."""
    src = "{ x : T; \\\n  y : U | x > 0 . x }"
    result = _gen_expr(src)
    assert "x" in result
    assert "y" in result


# ---------------------------------------------------------------------------
# Test 5 — newline after '|' and before expr (sanity: already worked)
# ---------------------------------------------------------------------------


def test_newline_before_expr_sanity() -> None:
    """Newlines surrounding both predicate and expr are accepted.

    This exercises the post-'|' newline path and the closing-brace
    _skip_newlines() that already existed before the fix.
    """
    src = "{ x : T |\n  x > 0 .\n  x }"
    result = _gen_expr(src)
    assert "x" in result


# ---------------------------------------------------------------------------
# Test 6 — three-way prefix with mixed breaks (mirrors s1q2 (d) DAT pattern)
# ---------------------------------------------------------------------------


def test_three_way_prefix_mixed_breaks() -> None:
    """Three-binding prefix with newline after '|' and after ';' is accepted.

    Mirrors the s1q2 (d) DAT pattern:
        { o : Outcome; c : Class; s : Ship |
              o.battle = Guadalcanal land o.ship = s.name .
              {| name == s.name |} }
    """
    src = "{ o : Outcome; c : Class;\n  s : Ship |\n  o = c land c = s . o }"
    result = _gen_expr(src)
    assert "o" in result
    assert "c" in result
    assert "s" in result
