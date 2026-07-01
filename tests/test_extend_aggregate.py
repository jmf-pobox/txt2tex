"""Tests for extend operator and two-argument aggregate form.

Features under test:
- Two-arg aggregator: Agg(rel, attr) as alias  (Date SUM(rel, exp) form)
- extend operator: R extend (Agg(...) as alias, ...)
- Fuzz routing: extend abbreviation goes to inline math, not zed
- Regression: single-arg aggregate and group output unchanged
"""

from __future__ import annotations

from txt2tex.ast_nodes import (
    Abbreviation,
    Aggregator,
    Document,
    Expr,
    ExtendAggregate,
    GroupAggregate,
    Identifier,
)
from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import RESERVED_WORDS, Lexer
from txt2tex.parser import Parser
from txt2tex.tokens import Token, TokenType

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _lex(src: str) -> list[Token]:
    """Tokenize src."""
    return Lexer(src).tokenize()


def _expr(src: str) -> Expr:
    """Parse a single expression and return the first document item."""
    result = Parser(_lex(src)).parse()
    item: Expr = result.items[0] if isinstance(result, Document) else result  # type: ignore[assignment]
    return item


def _expr_latex(src: str) -> str:
    """Generate LaTeX for an expression (math content without document wrapper)."""
    gen = LaTeXGenerator(use_fuzz=True)
    item = _expr(src)
    return gen.generate_expr(item)


def _doc_latex(src: str) -> str:
    """Generate LaTeX for a full document source string."""
    tokens = Lexer(src).tokenize()
    ast = Parser(tokens).parse()
    return LaTeXGenerator().generate_document(ast)


# ---------------------------------------------------------------------------
# Lexer: extend keyword
# ---------------------------------------------------------------------------


def test_lex_extend_token() -> None:
    """extend is lexed as EXTEND token, not IDENTIFIER."""
    tokens = _lex("extend")
    assert tokens[0].type == TokenType.EXTEND


def test_extend_in_reserved_words() -> None:
    """extend appears in RESERVED_WORDS."""
    assert "extend" in RESERVED_WORDS


# ---------------------------------------------------------------------------
# Test 1: Two-arg aggregate parse
# ---------------------------------------------------------------------------


def test_two_arg_agg_parse_sum() -> None:
    """R group (Sum(a, b) as t) -> AggregatorClause(SUM, source_rel='a', attr='b')."""
    node = _expr("R group (Sum(a, b) as t)")
    assert isinstance(node, GroupAggregate)
    assert len(node.clauses) == 1
    clause = node.clauses[0]
    assert clause.agg == Aggregator.SUM
    assert clause.source_rel == "a"
    assert clause.attr == "b"
    assert clause.alias == "t"


def test_two_arg_agg_parse_count() -> None:
    """R group (Count(rel, x) as total) -> source_rel='rel', attr='x'."""
    node = _expr("R group (Count(rel, x) as total)")
    assert isinstance(node, GroupAggregate)
    clause = node.clauses[0]
    assert clause.agg == Aggregator.COUNT
    assert clause.source_rel == "rel"
    assert clause.attr == "x"
    assert clause.alias == "total"


# ---------------------------------------------------------------------------
# Test 2: Two-arg aggregate render
# ---------------------------------------------------------------------------


def test_two_arg_agg_render_sum() -> None:
    r"""Two-arg Sum renders as \mathrm{Sum}(a, b)~\mathrm{as}~t."""
    result = _expr_latex("R group (Sum(a, b) as t)")
    assert r"\mathrm{Sum}(a, b)~\mathrm{as}~t" in result


def test_two_arg_agg_render_full_date_example() -> None:
    r"""Date example: Sum(payments, amountPaid) as totalInvoicePayment."""
    result = _expr_latex("R group (Sum(payments, amountPaid) as totalInvoicePayment)")
    assert (
        r"\mathrm{Sum}(payments, amountPaid)~\mathrm{as}~totalInvoicePayment" in result
    )


# ---------------------------------------------------------------------------
# Test 3: Single-arg aggregate unchanged (regression)
# ---------------------------------------------------------------------------


def test_single_arg_agg_source_rel_is_none() -> None:
    """R group (Sum(x) as t) -> source_rel is None."""
    node = _expr("R group (Sum(x) as t)")
    assert isinstance(node, GroupAggregate)
    clause = node.clauses[0]
    assert clause.source_rel is None
    assert clause.attr == "x"
    assert clause.alias == "t"


def test_single_arg_agg_render_unchanged() -> None:
    r"""Single-arg Sum still renders as \mathrm{Sum}(x)~\mathrm{as}~t."""
    result = _expr_latex("R group (Sum(x) as t)")
    assert r"\mathrm{Sum}(x)~\mathrm{as}~t" in result
    assert r"\mathrm{Sum}(x, " not in result


def test_single_arg_count_render_unchanged() -> None:
    r"""Regression: Count(x) as total renders as \mathrm{Count}(x)~\mathrm{as}~total."""
    result = _expr_latex("R group (Count(x) as total)")
    assert r"\mathrm{Count}(x)~\mathrm{as}~total" in result
    assert r"\mathop{\mathrm{Group}}" in result


# ---------------------------------------------------------------------------
# Test 4: extend parse
# ---------------------------------------------------------------------------


def test_extend_parse_single_clause() -> None:
    """R extend (Sum(payments, amountPaid) as total) -> ExtendAggregate, one clause."""
    node = _expr("R extend (Sum(payments, amountPaid) as total)")
    assert isinstance(node, ExtendAggregate)
    assert isinstance(node.relation, Identifier)
    assert node.relation.name == "R"
    assert len(node.clauses) == 1
    clause = node.clauses[0]
    assert clause.agg == Aggregator.SUM
    assert clause.source_rel == "payments"
    assert clause.attr == "amountPaid"
    assert clause.alias == "total"


def test_extend_parse_single_arg_clause() -> None:
    """extend also accepts single-arg clauses (no source_rel)."""
    node = _expr("R extend (Count(x) as n)")
    assert isinstance(node, ExtendAggregate)
    clause = node.clauses[0]
    assert clause.source_rel is None
    assert clause.attr == "x"
    assert clause.alias == "n"


def test_extend_no_line_break_after_by_default() -> None:
    """ExtendAggregate has line_break_after=False by default."""
    node = _expr("R extend (Count(x) as n)")
    assert isinstance(node, ExtendAggregate)
    assert node.line_break_after is False


# ---------------------------------------------------------------------------
# Test 5: extend render
# ---------------------------------------------------------------------------


def test_extend_render_single_clause() -> None:
    r"""R extend (...) renders with \mathop{\mathrm{Extend}} and correct clause."""
    result = _expr_latex("R extend (Sum(payments, amountPaid) as total)")
    expected = (
        r"R \mathop{\mathrm{Extend}}"
        r"(\mathrm{Sum}(payments, amountPaid)~\mathrm{as}~total)"
    )
    assert expected in result


def test_extend_render_mathop_extend() -> None:
    r"""extend operator emits \mathop{\mathrm{Extend}}."""
    result = _expr_latex("R extend (Count(x) as n)")
    assert r"\mathop{\mathrm{Extend}}" in result


# ---------------------------------------------------------------------------
# Test 6: extend multi-clause
# ---------------------------------------------------------------------------


def test_extend_parse_multi_clause() -> None:
    """R extend (Sum(p, a) as x, Count(p) as y) -> two clauses."""
    node = _expr("R extend (Sum(p, a) as x, Count(p) as y)")
    assert isinstance(node, ExtendAggregate)
    assert len(node.clauses) == 2
    c0 = node.clauses[0]
    assert c0.agg == Aggregator.SUM
    assert c0.source_rel == "p"
    assert c0.attr == "a"
    assert c0.alias == "x"
    c1 = node.clauses[1]
    assert c1.agg == Aggregator.COUNT
    assert c1.source_rel is None
    assert c1.attr == "p"
    assert c1.alias == "y"


def test_extend_render_multi_clause_comma_joined() -> None:
    r"""Multi-clause extend emits comma-separated clause LaTeX."""
    result = _expr_latex("R extend (Sum(p, a) as x, Count(p) as y)")
    assert r"\mathrm{Sum}(p, a)~\mathrm{as}~x" in result
    assert r"\mathrm{Count}(p)~\mathrm{as}~y" in result
    joined = r"\mathrm{Sum}(p, a)~\mathrm{as}~x, \mathrm{Count}(p)~\mathrm{as}~y"
    assert joined in result


# ---------------------------------------------------------------------------
# Test 7: Fuzz routing -- extend abbreviation -> inline math, not zed
# ---------------------------------------------------------------------------


def test_extend_abbreviation_routes_to_inline_math() -> None:
    r"""X == R extend (...) emits as \noindent $...$, not inside zed."""
    src = (
        "TITLE: probe\n\n"
        "given Foo\n"
        "schema R\n  x : Foo\nend\n\n"
        "X == R extend (Sum(p, a) as t)\n"
    )
    latex = _doc_latex(src)
    assert r"\begin{zed}" + "\nX ==" not in latex
    assert r"\noindent" in latex
    assert r"$X == R \mathop{\mathrm{Extend}}" in latex


# ---------------------------------------------------------------------------
# Test 8: Regression -- group output unchanged; extend emits no spurious backslash
# ---------------------------------------------------------------------------


def test_group_aggregate_render_regression() -> None:
    r"""Existing group/Count output unchanged after extend feature is added."""
    result = _expr_latex("R group (Count(x) as t, Sum(y) as g)")
    assert r"\mathop{\mathrm{Group}}" in result
    assert r"\mathrm{Count}(x)~\mathrm{as}~t" in result
    assert r"\mathrm{Sum}(y)~\mathrm{as}~g" in result


def test_extend_single_line_no_spurious_linebreak() -> None:
    r"""Single-line extend must not inject a line-break into the output."""
    result = _expr_latex("R extend (Count(x) as n)")
    assert r"\\" not in result


def test_extend_abbreviation_after_extend_no_swallow() -> None:
    """Abbreviation on the line after extend parses as a separate statement."""
    src = "E == D extend (Count(a) as ca)\nG == E"
    doc_result = Parser(_lex(src)).parse()
    assert isinstance(doc_result, Document)
    assert len(doc_result.items) == 2
    assert isinstance(doc_result.items[0], Abbreviation)
    assert doc_result.items[0].name == "E"
    assert isinstance(doc_result.items[0].expression, ExtendAggregate)
    assert isinstance(doc_result.items[1], Abbreviation)
    assert doc_result.items[1].name == "G"
