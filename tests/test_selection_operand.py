"""Tests for field-selection (`p.field`) as an operand of infix operators.

Phase 1 fix: extended `safe_followers` in `_parse_postfix` with all infix
operator tokens so that `p.amount |-> q.amount`, `p.a union q.b`, etc.,
parse correctly.

Phase 2 fix (Copilot review of PR #77): a tight dot — no whitespace between
`.` and the field name — now bypasses `safe_followers` entirely via the
short-circuit `not self._dot_is_spaced(next_token)`.  Z RM §3.16: selection
binds tighter than every infix operator, and syntactically a tight dot is
unambiguous.  The whitelist is now belt-and-suspenders for the spaced-dot path.

Root cause: `src/txt2tex/parser_pkg/expressions.py` `_parse_postfix`,
condition around the `safe_followers` check.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from txt2tex.ast_nodes import (
    BinaryOp,
    Divide,
    Document,
    Identifier,
    NaturalJoin,
    Number,
    SetComprehension,
    SetLiteral,
    Superscript,
    TupleProjection,
    UnaryOp,
)
from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_FUZZ_PREAMBLE = """\
\\documentclass[a4paper]{{article}}
\\usepackage{{fuzz}}
\\begin{{document}}
{body}
\\end{{document}}
"""


def _gen(src: str) -> str:
    """Parse src and return generated LaTeX."""
    tokens = Lexer(src).tokenize()
    ast = Parser(tokens).parse()
    gen = LaTeXGenerator(use_fuzz=True)
    if isinstance(ast, Document):
        return gen.generate_document(ast)
    return gen.generate_expr(ast)


def _fuzz_available() -> bool:
    """Return True if the fuzz binary is on PATH."""
    return shutil.which("fuzz") is not None


def _run_fuzz(tex_body: str, tmp_path: Path) -> subprocess.CompletedProcess[str]:
    """Run fuzz on tex_body wrapped in a minimal document."""
    fuzz_bin = shutil.which("fuzz")
    assert fuzz_bin is not None
    content = _FUZZ_PREAMBLE.format(body=tex_body)
    tex_file = tmp_path / "test.tex"
    tex_file.write_text(content, encoding="utf-8")
    return subprocess.run(  # noqa: S603
        [fuzz_bin, str(tex_file)],
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
        cwd=tmp_path,
    )


# ---------------------------------------------------------------------------
# Matrix: maplet (|->) operator
# ---------------------------------------------------------------------------


def test_maplet_both_sides_selection() -> None:
    """p.a |-> q.b must parse with TupleProjection on both sides.

    Z RM §3.16: selection binds tighter than any infix operator.
    `p.a |-> q.b` == `(p.a) |-> (q.b)`.
    """
    tokens = Lexer("p.a |-> q.b").tokenize()
    ast = Parser(tokens).parse()
    assert isinstance(ast, BinaryOp), f"Expected BinaryOp, got {type(ast).__name__!r}"
    assert ast.operator == "|->"
    assert isinstance(ast.left, TupleProjection), (
        f"Expected TupleProjection on left, got {type(ast.left).__name__!r}"
    )
    assert ast.left.index == "a"
    assert isinstance(ast.right, TupleProjection), (
        f"Expected TupleProjection on right, got {type(ast.right).__name__!r}"
    )
    assert ast.right.index == "b"


def test_maplet_selection_left_literal_right() -> None:
    """p.a |-> 0 must parse with TupleProjection on the left."""
    tokens = Lexer("p.a |-> 0").tokenize()
    ast = Parser(tokens).parse()
    assert isinstance(ast, BinaryOp), f"Expected BinaryOp, got {type(ast).__name__!r}"
    assert ast.operator == "|->"
    assert isinstance(ast.left, TupleProjection)
    assert ast.left.index == "a"
    assert isinstance(ast.right, Number)


def test_maplet_literal_left_selection_right() -> None:
    """0 |-> p.a must parse with TupleProjection on the right.

    A literal left operand is already unambiguous; this confirms the right
    operand is also parsed correctly.
    """
    tokens = Lexer("0 |-> p.a").tokenize()
    ast = Parser(tokens).parse()
    assert isinstance(ast, BinaryOp), f"Expected BinaryOp, got {type(ast).__name__!r}"
    assert ast.operator == "|->"
    assert isinstance(ast.left, Number)
    assert isinstance(ast.right, TupleProjection)
    assert ast.right.index == "a"


# ---------------------------------------------------------------------------
# Matrix: set operators
# ---------------------------------------------------------------------------


def test_union_selection_operand() -> None:
    """p.a union q.b must parse with TupleProjection on both sides."""
    tokens = Lexer("p.a union q.b").tokenize()
    ast = Parser(tokens).parse()
    assert isinstance(ast, BinaryOp), f"Expected BinaryOp, got {type(ast).__name__!r}"
    assert ast.operator == "union"
    assert isinstance(ast.left, TupleProjection)
    assert isinstance(ast.right, TupleProjection)


def test_override_selection_operand() -> None:
    """p.a ++ q.b must parse with TupleProjection on both sides."""
    tokens = Lexer("p.a ++ q.b").tokenize()
    ast = Parser(tokens).parse()
    assert isinstance(ast, BinaryOp), f"Expected BinaryOp, got {type(ast).__name__!r}"
    assert ast.operator == "++"
    assert isinstance(ast.left, TupleProjection)
    assert isinstance(ast.right, TupleProjection)


def test_intersect_selection_operand() -> None:
    """p.a intersect q.b must parse with TupleProjection on both sides."""
    tokens = Lexer("p.a intersect q.b").tokenize()
    ast = Parser(tokens).parse()
    assert isinstance(ast, BinaryOp), f"Expected BinaryOp, got {type(ast).__name__!r}"
    assert ast.operator == "intersect"
    assert isinstance(ast.left, TupleProjection)
    assert isinstance(ast.right, TupleProjection)


def test_setminus_selection_operand() -> None:
    r"""p.a \ q.b must parse with TupleProjection on both sides.

    In txt2tex notation, set difference is the backslash character `\`
    (which lexes as SETMINUS when not followed by a newline).  There is
    no `setminus` keyword.
    """
    tokens = Lexer("p.a \\ q.b").tokenize()
    ast = Parser(tokens).parse()
    assert isinstance(ast, BinaryOp), f"Expected BinaryOp, got {type(ast).__name__!r}"
    assert ast.operator == "\\"
    assert isinstance(ast.left, TupleProjection)
    assert isinstance(ast.right, TupleProjection)


def test_cross_selection_operand() -> None:
    """p.a cross q.b must parse with TupleProjection on both sides."""
    tokens = Lexer("p.a cross q.b").tokenize()
    ast = Parser(tokens).parse()
    assert isinstance(ast, BinaryOp), f"Expected BinaryOp, got {type(ast).__name__!r}"
    assert ast.operator == "cross"
    assert isinstance(ast.left, TupleProjection)
    assert isinstance(ast.right, TupleProjection)


# ---------------------------------------------------------------------------
# Matrix: relation type and restriction operators
# ---------------------------------------------------------------------------


def test_relation_type_selection_operand() -> None:
    """p.a <-> q.b must parse with TupleProjection on both sides."""
    tokens = Lexer("p.a <-> q.b").tokenize()
    ast = Parser(tokens).parse()
    assert isinstance(ast, BinaryOp), f"Expected BinaryOp, got {type(ast).__name__!r}"
    assert ast.operator == "<->"
    assert isinstance(ast.left, TupleProjection)
    assert isinstance(ast.right, TupleProjection)


def test_dres_selection_on_right() -> None:
    """s <| p.a must parse with TupleProjection on the right."""
    tokens = Lexer("s <| p.a").tokenize()
    ast = Parser(tokens).parse()
    assert isinstance(ast, BinaryOp), f"Expected BinaryOp, got {type(ast).__name__!r}"
    assert ast.operator == "<|"
    assert isinstance(ast.left, Identifier)
    assert isinstance(ast.right, TupleProjection)
    assert ast.right.index == "a"


def test_rres_selection_on_left() -> None:
    """p.a |> s must parse with TupleProjection on the left."""
    tokens = Lexer("p.a |> s").tokenize()
    ast = Parser(tokens).parse()
    assert isinstance(ast, BinaryOp), f"Expected BinaryOp, got {type(ast).__name__!r}"
    assert ast.operator == "|>"
    assert isinstance(ast.left, TupleProjection)
    assert ast.left.index == "a"
    assert isinstance(ast.right, Identifier)


def test_ndres_selection_on_right() -> None:
    """s <<| p.a must parse with TupleProjection on the right."""
    tokens = Lexer("s <<| p.a").tokenize()
    ast = Parser(tokens).parse()
    assert isinstance(ast, BinaryOp), f"Expected BinaryOp, got {type(ast).__name__!r}"
    assert ast.operator == "<<|"
    assert isinstance(ast.right, TupleProjection)
    assert ast.right.index == "a"


def test_nrres_selection_on_left() -> None:
    """p.a |>> s must parse with TupleProjection on the left."""
    tokens = Lexer("p.a |>> s").tokenize()
    ast = Parser(tokens).parse()
    assert isinstance(ast, BinaryOp), f"Expected BinaryOp, got {type(ast).__name__!r}"
    assert ast.operator == "|>>"
    assert isinstance(ast.left, TupleProjection)
    assert ast.left.index == "a"


# ---------------------------------------------------------------------------
# Matrix: composition operators
# ---------------------------------------------------------------------------


def test_circ_selection_operand() -> None:
    """p.a o9 q.b must parse with TupleProjection on both sides."""
    tokens = Lexer("p.a o9 q.b").tokenize()
    ast = Parser(tokens).parse()
    assert isinstance(ast, BinaryOp), f"Expected BinaryOp, got {type(ast).__name__!r}"
    assert ast.operator == "o9"
    assert isinstance(ast.left, TupleProjection)
    assert isinstance(ast.right, TupleProjection)


def test_comp_selection_operand() -> None:
    """p.a comp q.b must parse with TupleProjection on both sides."""
    tokens = Lexer("p.a comp q.b").tokenize()
    ast = Parser(tokens).parse()
    assert isinstance(ast, BinaryOp), f"Expected BinaryOp, got {type(ast).__name__!r}"
    assert ast.operator == "comp"
    assert isinstance(ast.left, TupleProjection)
    assert isinstance(ast.right, TupleProjection)


# ---------------------------------------------------------------------------
# Matrix: arithmetic and relational-algebra operators
# ---------------------------------------------------------------------------


def test_star_selection_operand() -> None:
    """p.a * 0 must parse with TupleProjection on the left.

    Outside a comprehension body, `*` is arithmetic multiplication.
    Selection binds tighter, so this is `(p.a) * 0`.
    """
    tokens = Lexer("p.a * 0").tokenize()
    ast = Parser(tokens).parse()
    assert isinstance(ast, BinaryOp), f"Expected BinaryOp, got {type(ast).__name__!r}"
    assert ast.operator == "*"
    assert isinstance(ast.left, TupleProjection)
    assert ast.left.index == "a"
    assert isinstance(ast.right, Number)


def test_join_selection_operand() -> None:
    """p.a join q.b must parse as a NaturalJoin with TupleProjection on both sides.

    The relational-algebra `join` operator produces a NaturalJoin AST node,
    not a generic BinaryOp.
    """
    tokens = Lexer("p.a join q.b").tokenize()
    ast = Parser(tokens).parse()
    assert isinstance(ast, NaturalJoin), (
        f"Expected NaturalJoin, got {type(ast).__name__!r}"
    )
    assert isinstance(ast.left, TupleProjection), (
        f"Expected TupleProjection on left, got {type(ast.left).__name__!r}"
    )
    assert isinstance(ast.right, TupleProjection), (
        f"Expected TupleProjection on right, got {type(ast.right).__name__!r}"
    )


def test_div_selection_operand() -> None:
    """p.a div q.b must parse as a Divide with TupleProjection on both sides.

    The relational-algebra `div` operator produces a Divide AST node,
    not a generic BinaryOp.
    """
    tokens = Lexer("p.a div q.b").tokenize()
    ast = Parser(tokens).parse()
    assert isinstance(ast, Divide), f"Expected Divide, got {type(ast).__name__!r}"
    assert isinstance(ast.left, TupleProjection), (
        f"Expected TupleProjection on left, got {type(ast.left).__name__!r}"
    )
    assert isinstance(ast.right, TupleProjection), (
        f"Expected TupleProjection on right, got {type(ast.right).__name__!r}"
    )


# ---------------------------------------------------------------------------
# Matrix: sequence and judgment operators (Phase 2 additions)
# ---------------------------------------------------------------------------


def test_filter_selection_operand() -> None:
    """p.a filter s must parse with TupleProjection on the left.

    `filter` (↾) is a sequence restriction operator.  It was missing from
    `safe_followers` before the Phase 2 fix; the tight-dot bypass now ensures
    it is always handled even for future operator gaps in the whitelist.
    """
    tokens = Lexer("p.a filter s").tokenize()
    ast = Parser(tokens).parse()
    assert isinstance(ast, BinaryOp), f"Expected BinaryOp, got {type(ast).__name__!r}"
    assert ast.operator == "filter"
    assert isinstance(ast.left, TupleProjection), (
        f"Expected TupleProjection on left, got {type(ast.left).__name__!r}"
    )
    assert ast.left.index == "a"
    assert isinstance(ast.right, Identifier)
    assert ast.right.name == "s"


def test_shows_selection_operand() -> None:
    """p.a shows q.b must parse with TupleProjection on both sides.

    `shows` (⊢) is a sequent/judgment operator.  Both operands are field
    selections; the tight-dot bypass ensures both are parsed as projections.
    """
    tokens = Lexer("p.a shows q.b").tokenize()
    ast = Parser(tokens).parse()
    assert isinstance(ast, BinaryOp), f"Expected BinaryOp, got {type(ast).__name__!r}"
    assert ast.operator == "shows"
    assert isinstance(ast.left, TupleProjection), (
        f"Expected TupleProjection on left, got {type(ast.left).__name__!r}"
    )
    assert ast.left.index == "a"
    assert isinstance(ast.right, TupleProjection), (
        f"Expected TupleProjection on right, got {type(ast.right).__name__!r}"
    )
    assert ast.right.index == "b"


# ---------------------------------------------------------------------------
# Matrix: postfix operators applied to a selection result (Phase 2 additions)
# ---------------------------------------------------------------------------


def test_postfix_superscript_after_selection() -> None:
    """p.a^2 must parse as Superscript(TupleProjection(p, 'a'), Number('2')).

    The tight dot in `p.a` binds before the postfix `^`, so the base of the
    Superscript is the projection, not the bare identifier `a`.
    """
    tokens = Lexer("p.a^2").tokenize()
    ast = Parser(tokens).parse()
    assert isinstance(ast, Superscript), (
        f"Expected Superscript, got {type(ast).__name__!r}"
    )
    assert isinstance(ast.base, TupleProjection), (
        f"Expected TupleProjection as Superscript.base, got {type(ast.base).__name__!r}"
    )
    assert ast.base.index == "a"
    assert isinstance(ast.exponent, Number)
    assert ast.exponent.value == "2"


def test_postfix_inverse_after_selection() -> None:
    """p.a~ must parse as UnaryOp('~', TupleProjection(p, 'a')).

    The `~` postfix operator (relational inverse) applies to the projected
    field, not to the base identifier.  The tight dot ensures the projection
    is built first.
    """
    tokens = Lexer("p.a~").tokenize()
    ast = Parser(tokens).parse()
    assert isinstance(ast, UnaryOp), f"Expected UnaryOp, got {type(ast).__name__!r}"
    assert ast.operator == "~"
    assert isinstance(ast.operand, TupleProjection), (
        f"Expected TupleProjection as operand, got {type(ast.operand).__name__!r}"
    )
    assert ast.operand.index == "a"


def test_selection_field_name_with_underscore() -> None:
    """p.a_1 must parse as TupleProjection with field name 'a_1'.

    In the lexer, `a_1` is a single IDENTIFIER token — the underscore is
    part of the name, not a subscript operator.  The safe_followers whitelist
    includes UNDERSCORE for the spaced-dot path, but tight `p.a_1` goes via
    the tight-dot bypass and the selected field is 'a_1'.
    """
    tokens = Lexer("p.a_1").tokenize()
    ast = Parser(tokens).parse()
    assert isinstance(ast, TupleProjection), (
        f"Expected TupleProjection, got {type(ast).__name__!r}"
    )
    assert ast.index == "a_1", f"Expected field name 'a_1', got {ast.index!r}"
    assert isinstance(ast.base, Identifier)
    assert ast.base.name == "p"


def test_selection_field_with_underscore_then_operator() -> None:
    """p.a_1 union s must parse with TupleProjection(field='a_1') as left operand."""
    tokens = Lexer("p.a_1 union s").tokenize()
    ast = Parser(tokens).parse()
    assert isinstance(ast, BinaryOp), f"Expected BinaryOp, got {type(ast).__name__!r}"
    assert ast.operator == "union"
    assert isinstance(ast.left, TupleProjection)
    assert ast.left.index == "a_1"
    assert isinstance(ast.right, Identifier)


# ---------------------------------------------------------------------------
# Matrix: set display and comprehension characteristic expression
# ---------------------------------------------------------------------------


def test_set_display_with_maplet_selections() -> None:
    """{ p.a |-> p.b } must parse as a SetLiteral containing a maplet BinaryOp.

    The single element is `p.a |-> p.b` — a BinaryOp where both operands
    are TupleProjection nodes.
    """
    tokens = Lexer("{ p.a |-> p.b }").tokenize()
    ast = Parser(tokens).parse()
    assert isinstance(ast, SetLiteral), (
        f"Expected SetLiteral, got {type(ast).__name__!r}"
    )
    assert len(ast.elements) == 1
    elem = ast.elements[0]
    assert isinstance(elem, BinaryOp), (
        f"Expected BinaryOp element, got {type(elem).__name__!r}"
    )
    assert elem.operator == "|->"
    assert isinstance(elem.left, TupleProjection)
    assert elem.left.index == "a"
    assert isinstance(elem.right, TupleProjection)
    assert elem.right.index == "b"


def test_comprehension_char_expr_with_maplet_selections() -> None:
    """{ p : T | p.x = 0 . p.a |-> p.b } must parse with maplet as char-expr.

    The bullet `p.x = 0 . body` separates the predicate from the
    characteristic expression.  The char-expr `p.a |-> p.b` must parse
    as a BinaryOp with TupleProjection on both sides.
    """
    tokens = Lexer("{ p : T | p.x = 0 . p.a |-> p.b }").tokenize()
    ast = Parser(tokens).parse()
    assert isinstance(ast, SetComprehension), (
        f"Expected SetComprehension, got {type(ast).__name__!r}"
    )
    expr = ast.expression
    assert expr is not None, (
        "SetComprehension.expression must not be None — "
        "the bullet body `p.a |-> p.b` was not parsed"
    )
    assert isinstance(expr, BinaryOp), (
        f"Expected BinaryOp as char-expr, got {type(expr).__name__!r}"
    )
    assert expr.operator == "|->"
    assert isinstance(expr.left, TupleProjection)
    assert expr.left.index == "a"
    assert isinstance(expr.right, TupleProjection)
    assert expr.right.index == "b"


def test_realistic_invoice_comprehension() -> None:
    """{ p : Payment | i.invoiceId = p.invoiceId . p.paymentId |-> p.amount } parses.

    This is the user's real use case.  The predicate ends with the
    doubly-projected `p.invoiceId`; the double-projection carve-out
    (lines 2359-2362 in expressions.py) fires there and correctly marks
    `.` as the bullet separator.  The char-expr `p.paymentId |-> p.amount`
    must then parse with TupleProjection on both sides.
    """
    src = "{ p : Payment | i.invoiceId = p.invoiceId . p.paymentId |-> p.amount }"
    tokens = Lexer(src).tokenize()
    ast = Parser(tokens).parse()
    assert isinstance(ast, SetComprehension), (
        f"Expected SetComprehension, got {type(ast).__name__!r}"
    )
    expr = ast.expression
    assert expr is not None, (
        "char-expr `p.paymentId |-> p.amount` not parsed — "
        "bullet was not recognised after `p.invoiceId`"
    )
    assert isinstance(expr, BinaryOp)
    assert expr.operator == "|->"
    assert isinstance(expr.left, TupleProjection)
    assert expr.left.index == "paymentId"
    assert isinstance(expr.right, TupleProjection)
    assert expr.right.index == "amount"


def test_axdef_predicate_with_maplet_selections() -> None:
    """(p.a |-> p.b) elem r must parse correctly in an axdef-like context.

    Parsed as a bare expression; the `_in_comprehension_body` flag is False
    so the safe_followers check governs.  After the fix, MAPLET is in
    safe_followers and `p.a` is parsed as TupleProjection.
    """
    tokens = Lexer("(p.a |-> p.b) elem r").tokenize()
    ast = Parser(tokens).parse()
    assert isinstance(ast, BinaryOp), f"Expected BinaryOp, got {type(ast).__name__!r}"
    # The `elem` keyword maps to TokenType.IN; the BinaryOp carries the
    # token's string value ("elem"), not the type name.
    assert ast.operator == "elem"
    inner = ast.left
    assert isinstance(inner, BinaryOp)
    assert inner.operator == "|->"
    assert isinstance(inner.left, TupleProjection)
    assert inner.left.index == "a"
    assert isinstance(inner.right, TupleProjection)
    assert inner.right.index == "b"


# ---------------------------------------------------------------------------
# Matrix: chained selection outside comprehension
# ---------------------------------------------------------------------------


def test_chained_selection_outside_comprehension() -> None:
    """a.b.c |-> d must parse as a doubly-chained projection on the left.

    Outside a comprehension body, `a.b.c` is always two applications of
    named-field selection.  The double-projection carve-out (lines 2359-2362)
    only fires when `_in_comprehension_body` is True, so `a.b.c` outside a
    comprehension is unambiguously `TupleProjection(TupleProjection(a, b), c)`.
    """
    tokens = Lexer("a.b.c |-> d").tokenize()
    ast = Parser(tokens).parse()
    assert isinstance(ast, BinaryOp), f"Expected BinaryOp, got {type(ast).__name__!r}"
    assert ast.operator == "|->"
    left = ast.left
    assert isinstance(left, TupleProjection), (
        f"Expected TupleProjection on left, got {type(left).__name__!r}"
    )
    assert left.index == "c"
    assert isinstance(left.base, TupleProjection), (
        f"Expected nested TupleProjection, got {type(left.base).__name__!r}"
    )
    assert left.base.index == "b"
    assert isinstance(ast.right, Identifier)
    assert ast.right.name == "d"


# ---------------------------------------------------------------------------
# LaTeX generation smoke tests
# ---------------------------------------------------------------------------


def test_latex_maplet_both_selections() -> None:
    """p.a |-> q.b generates LaTeX containing the maplet operator."""
    latex = _gen("p.a |-> q.b")
    assert r"\mapsto" in latex or "|->" in latex, (
        f"maplet operator missing from LaTeX: {latex!r}"
    )
    # Both projections must appear
    assert "p" in latex
    assert "a" in latex
    assert "q" in latex
    assert "b" in latex


def test_latex_union_both_selections() -> None:
    """p.a union q.b generates LaTeX containing the union operator."""
    latex = _gen("p.a union q.b")
    assert r"\cup" in latex or "union" in latex, (
        f"union operator missing from LaTeX: {latex!r}"
    )


def test_latex_cross_both_selections() -> None:
    """p.a cross q.b generates LaTeX containing the cross operator."""
    latex = _gen("p.a cross q.b")
    assert r"\cross" in latex or r"\times" in latex, (
        f"cross operator missing from LaTeX: {latex!r}"
    )


# ---------------------------------------------------------------------------
# Carve-out regressions — MUST NOT change
# ---------------------------------------------------------------------------


def test_carveout_spaced_dot_is_bullet_not_selection() -> None:
    """{ s : S | s = s . s } — spaced dot with quantifier var is bullet.

    Z RM §3.16: a spaced `. ident` where `ident` is a quantifier variable
    is the bullet separator, never field selection.  This carve-out fires
    at lines 2372-2377 in expressions.py, BEFORE `safe_followers` is
    checked, so adding tokens to the whitelist cannot break it.
    """
    src = "{ s : S | s = s . s }"
    tokens = Lexer(src).tokenize()
    ast = Parser(tokens).parse()
    assert isinstance(ast, SetComprehension), (
        f"Expected SetComprehension, got {type(ast).__name__!r}"
    )
    # The bullet body must be the identifier `s`, not a TupleProjection.
    assert ast.expression is not None, (
        "expression must not be None — the spaced dot was not parsed as bullet"
    )
    assert isinstance(ast.expression, Identifier), (
        f"Expected Identifier as body, got {type(ast.expression).__name__!r} — "
        "spaced dot may have been parsed as selection instead of bullet"
    )
    assert ast.expression.name == "s"


def test_carveout_predicate_ending_with_projection_sees_bullet() -> None:
    """Predicate ending with TupleProjection: next `.` is bullet, not projection.

    The carve-out at lines 2359-2362 fires when `base` is already a
    TupleProjection inside a comprehension body.  After the predicate's final
    `p.x`, the subsequent `. p.b` is the bullet separator plus the char-expr,
    NOT a third-level chained projection.

    This carve-out fires BEFORE `safe_followers` is checked, so extending
    `safe_followers` cannot affect it.  This test verifies the carve-out
    is still in place after the fix.

    Input: `{ p : T | 0 = p.x . p.b }`
    Predicate: `0 = p.x`; bullet: `.`; char-expr: `p.b`.
    """
    src = "{ p : T | 0 = p.x . p.b }"
    tokens = Lexer(src).tokenize()
    ast = Parser(tokens).parse()
    assert isinstance(ast, SetComprehension), (
        f"Expected SetComprehension, got {type(ast).__name__!r}"
    )
    # The char-expr must be p.b, not a chained p.x.p or p.x.p.b.
    assert ast.expression is not None, (
        "expression must not be None — bullet after p.x was not recognised"
    )
    expr = ast.expression
    assert isinstance(expr, TupleProjection), (
        f"Expected TupleProjection for p.b, got {type(expr).__name__!r}"
    )
    assert expr.index == "b", (
        f"Expected char-expr to be p.b (index='b'), got index={expr.index!r}"
    )


# ---------------------------------------------------------------------------
# End-to-end fuzz round-trip (guarded)
# ---------------------------------------------------------------------------

# Parse-only source — mirrors the user's motivating example.  The
# comprehension char-expr uses the maplet |-> (paymentId |-> amount) — the
# reported bug: a field selection as an operand of |-> now parses after the
# fix.  (The `+->` in the gendef signature is the partial-function *type*
# arrow and is unrelated.)
_INV_SRC = (
    "given InvoiceId, PaymentId\n"
    "\n"
    "Currency == N\n"
    "\n"
    "gendef [X]\n"
    "  sum : (X +-> Currency) -> Currency\n"
    "where\n"
    "  sum(emptyset[X cross Currency]) = 0\n"
    "  forall amtByKey : X +-> Currency; key : X; amount : Currency"
    " | key notin dom amtByKey =>\n"
    "      sum(amtByKey union {key |-> amount}) = amount + sum amtByKey\n"
    "end\n"
    "\n"
    "schema Invoice\n"
    "  invoiceId : InvoiceId\n"
    "  amountPaid : Currency\n"
    "end\n"
    "\n"
    "schema Payment\n"
    "  paymentId : PaymentId\n"
    "  invoiceId : InvoiceId\n"
    "  amount : Currency\n"
    "end\n"
    "\n"
    "zed\n"
    "  forall i : Invoice |\n"
    "    i.amountPaid = sum({ p : Payment | i.invoiceId = p.invoiceId"
    " . p.paymentId |-> p.amount })\n"
    "end\n"
)

# Fuzz round-trip source — uses a schema with set-valued fields so that
# `a.items union b.items` is well-typed in fuzz.  This tests that a
# field selection is accepted as the left operand of `union` (newly added
# to safe_followers), and that the generated LaTeX type-checks.
_FUZZ_SRC = (
    "schema Container\n"
    "  items : P N\n"
    "end\n"
    "\n"
    "axdef\n"
    "  a, b : Container\n"
    "  s : P N\n"
    "where\n"
    "  s = a.items union b.items\n"
    "end\n"
)


def test_invoice_comprehension_parses_without_error() -> None:
    """The invoice comprehension parses without ParserError.

    Confirms that `i.invoiceId`, `p.invoiceId`, `p.paymentId`, and
    `p.amount` (each a TupleProjection) are accepted as operands next to
    `=` and the maplet `|->`, and inside a comprehension char-expr.
    """
    tokens = Lexer(_INV_SRC).tokenize()
    doc = Parser(tokens).parse()
    assert isinstance(doc, Document), f"Expected Document, got {type(doc).__name__!r}"
    # Successful parse is sufficient — fuzz type-checks separately.
    assert len(doc.items) > 0


@pytest.mark.skipif(not _fuzz_available(), reason="fuzz binary not on PATH")
def test_fuzz_accepts_selection_as_union_operand(tmp_path: Path) -> None:
    """Fuzz accepts LaTeX where a field selection is the left operand of union.

    Regression pin: if the selection-operand bug reappears, `a.items` would
    not parse as a TupleProjection when followed by `union`, causing a
    ParserError or wrong LaTeX that fuzz rejects.

    Uses a minimal Container schema so the semantics are well-typed:
    `a.items : P N`, `b.items : P N`, `a.items union b.items : P N`.
    """
    tokens = Lexer(_FUZZ_SRC).tokenize()
    doc = Parser(tokens).parse()
    assert isinstance(doc, Document)
    tex = LaTeXGenerator(use_fuzz=True).generate_document(doc)

    # Confirm both projections appear in the output.
    assert "items" in tex, f"items missing from generated LaTeX:\n{tex}"
    assert r"\cup" in tex or "union" in tex, (
        f"union operator missing from generated LaTeX:\n{tex}"
    )

    result = _run_fuzz(tex, tmp_path)
    assert result.returncode == 0, (
        f"fuzz rejected selection-as-union-operand LaTeX\n"
        f"tex:\n{tex}\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )
