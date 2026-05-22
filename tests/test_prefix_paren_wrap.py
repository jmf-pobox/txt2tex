"""Tests for prefix-operator parenthesis wrapping (bug #133).

Fuzz grammar rule (Z RM §3.7): prefix-generic operators require an atomic
Expression0 as their immediate right operand.  A nested prefix application is
not atomic, so the generator must wrap it in parentheses.
"""

from __future__ import annotations

from txt2tex.ast_nodes import Document, Expr
from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser
from txt2tex.tokens import Token

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _lex(src: str) -> list[Token]:
    """Tokenize src."""
    return Lexer(src).tokenize()


def _expr(src: str) -> Expr:
    """Parse a single expression from a bare expression source."""
    result = Parser(_lex(src)).parse()
    item: Expr = result.items[0] if isinstance(result, Document) else result  # type: ignore[assignment]
    return item


def _expr_latex(src: str) -> str:
    """Generate fuzz-mode LaTeX for a bare expression."""
    gen = LaTeXGenerator(use_fuzz=True)
    return gen.generate_expr(_expr(src))


# ---------------------------------------------------------------------------
# Bug-fix cases: UnaryOp operand of a special-function FunctionApp
# ---------------------------------------------------------------------------


def test_seq_power_wraps_operand() -> None:
    r"""`seq (P X)` emits `\seq~(\power X)`, not `\seq~\power X`."""
    result = _expr_latex("seq (P X)")
    assert result == r"\seq~(\power X)"


def test_finset_seq_wraps_operand() -> None:
    r"""`F (seq X)` emits `\finset (\seq~X)`, not `\finset \seq~X`."""
    result = _expr_latex("F (seq X)")
    assert result == r"\finset (\seq~X)"


# ---------------------------------------------------------------------------
# Bug-fix cases: UnaryOp operand of a _FUZZ_FUNCTION_LIKE_UNARY UnaryOp
# ---------------------------------------------------------------------------


def test_ran_bigcup_wraps_operand() -> None:
    r"""`ran (bigcup (ran s))` emits `\ran (\bigcup (\ran s))`."""
    result = _expr_latex("ran (bigcup (ran s))")
    assert result == r"\ran (\bigcup (\ran s))"


def test_ran_dom_wraps_operand() -> None:
    r"""`ran (dom R)` emits `\ran (\dom R)`."""
    result = _expr_latex("ran (dom R)")
    assert result == r"\ran (\dom R)"


# ---------------------------------------------------------------------------
# Sanity cases: behaviours that must be preserved
# ---------------------------------------------------------------------------


def test_power_power_wraps_operand() -> None:
    r"""`P (P X)` emits `\power (\power X)` (existing FunctionApp→FunctionApp path)."""
    result = _expr_latex("P (P X)")
    assert result == r"\power (\power X)"


def test_bigcup_ran_wraps_operand() -> None:
    r"""`bigcup (ran s)` emits `\bigcup (\ran s)` (existing rule, now generalised)."""
    result = _expr_latex("bigcup (ran s)")
    assert result == r"\bigcup (\ran s)"


def test_dom_binary_wraps_operand() -> None:
    r"""`dom (R cross S)` emits `\dom (R \cross S)` — BinaryOp arg still wrapped."""
    result = _expr_latex("dom (R cross S)")
    assert result == r"\dom (R \cross S)"


def test_ran_atomic_no_wrap() -> None:
    r"""`ran R` emits `\ran R` — atomic identifier operand is not wrapped."""
    result = _expr_latex("ran R")
    assert result == r"\ran R"
