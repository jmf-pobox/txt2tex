"""Tests for GROUP aggregate form: Count/Sum/Avg/Min/Max/Median inside GROUP RHS."""

from __future__ import annotations

import pytest

from txt2tex.ast_nodes import (
    Aggregator,
    AggregatorClause,
    Document,
    Expr,
    Group,
    GroupAggregate,
    Identifier,
)
from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import RESERVED_WORDS, Lexer
from txt2tex.parser import Parser, ParserError
from txt2tex.tokens import Token, TokenType

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _lex(src: str) -> list[Token]:
    """Tokenize src."""
    return Lexer(src).tokenize()


def _expr(src: str) -> Expr:
    """Parse a single expression and return the first document item as Expr."""
    result = Parser(_lex(src)).parse()
    item: Expr = result.items[0] if isinstance(result, Document) else result  # type: ignore[assignment]
    return item


def _expr_latex(src: str) -> str:
    """Generate LaTeX for an expression (math content without wrapper)."""
    gen = LaTeXGenerator(use_fuzz=True)
    item = _expr(src)
    return gen.generate_expr(item)


# ---------------------------------------------------------------------------
# Lexer tests — token types
# ---------------------------------------------------------------------------


def test_lex_count_token() -> None:
    """Count is lexed as COUNT token."""
    tokens = _lex("Count")
    assert tokens[0].type == TokenType.COUNT


def test_lex_sum_token() -> None:
    """Sum is lexed as SUM token."""
    tokens = _lex("Sum")
    assert tokens[0].type == TokenType.SUM


def test_lex_avg_token() -> None:
    """Avg is lexed as AVG token."""
    tokens = _lex("Avg")
    assert tokens[0].type == TokenType.AVG


def test_lex_min_token() -> None:
    """Min is lexed as MIN token."""
    tokens = _lex("Min")
    assert tokens[0].type == TokenType.MIN


def test_lex_max_token() -> None:
    """Max is lexed as MAX token."""
    tokens = _lex("Max")
    assert tokens[0].type == TokenType.MAX


def test_lex_median_token() -> None:
    """Median is lexed as MEDIAN token."""
    tokens = _lex("Median")
    assert tokens[0].type == TokenType.MEDIAN


def test_lex_as_token() -> None:
    """as is lexed as AS token."""
    tokens = _lex("as")
    assert tokens[0].type == TokenType.AS


@pytest.mark.parametrize(
    ("keyword", "expected"),
    [
        ("Count", TokenType.COUNT),
        ("Sum", TokenType.SUM),
        ("Avg", TokenType.AVG),
        ("Min", TokenType.MIN),
        ("Max", TokenType.MAX),
        ("Median", TokenType.MEDIAN),
        ("as", TokenType.AS),
    ],
)
def test_aggregator_keywords_not_identifiers(keyword: str, expected: TokenType) -> None:
    """Aggregator keywords tokenise as their dedicated types, not IDENTIFIER."""
    tokens = _lex(keyword)
    assert tokens[0].type == expected


def test_aggregator_keywords_in_reserved_words() -> None:
    """All aggregator keywords appear in RESERVED_WORDS."""
    for word in ("Count", "Sum", "Avg", "Min", "Max", "Median", "as"):
        assert word in RESERVED_WORDS, f"{word!r} not in RESERVED_WORDS"


# ---------------------------------------------------------------------------
# AST tests — parse produces correct GroupAggregate structure
# ---------------------------------------------------------------------------


def test_parse_count_aggregate() -> None:
    """R group (Count(x) as total) parses to GroupAggregate with COUNT clause."""
    node = _expr("R group (Count(x) as total)")
    assert isinstance(node, GroupAggregate)
    assert isinstance(node.relation, Identifier)
    assert node.relation.name == "R"
    assert len(node.clauses) == 1
    clause = node.clauses[0]
    assert isinstance(clause, AggregatorClause)
    assert clause.agg == Aggregator.COUNT
    assert clause.attr == "x"
    assert clause.alias == "total"


def test_parse_sum_aggregate() -> None:
    """R group (Sum(y) as grand) parses to GroupAggregate with SUM clause."""
    node = _expr("R group (Sum(y) as grand)")
    assert isinstance(node, GroupAggregate)
    assert node.clauses[0].agg == Aggregator.SUM
    assert node.clauses[0].attr == "y"
    assert node.clauses[0].alias == "grand"


def test_parse_avg_aggregate() -> None:
    """R group (Avg(score) as mean) parses to GroupAggregate with AVG clause."""
    node = _expr("R group (Avg(score) as mean)")
    assert isinstance(node, GroupAggregate)
    assert node.clauses[0].agg == Aggregator.AVG


def test_parse_min_aggregate() -> None:
    """R group (Min(val) as lo) parses to GroupAggregate with MIN clause."""
    node = _expr("R group (Min(val) as lo)")
    assert isinstance(node, GroupAggregate)
    assert node.clauses[0].agg == Aggregator.MIN


def test_parse_max_aggregate() -> None:
    """R group (Max(val) as hi) parses to GroupAggregate with MAX clause."""
    node = _expr("R group (Max(val) as hi)")
    assert isinstance(node, GroupAggregate)
    assert node.clauses[0].agg == Aggregator.MAX


def test_parse_median_aggregate() -> None:
    """R group (Median(score) as med) parses to GroupAggregate with MEDIAN clause."""
    node = _expr("R group (Median(score) as med)")
    assert isinstance(node, GroupAggregate)
    assert node.clauses[0].agg == Aggregator.MEDIAN


def test_parse_two_aggregators() -> None:
    """R group (Count(x) as t, Sum(y) as g) produces two AggregatorClauses."""
    node = _expr("R group (Count(x) as t, Sum(y) as g)")
    assert isinstance(node, GroupAggregate)
    assert len(node.clauses) == 2
    assert node.clauses[0].agg == Aggregator.COUNT
    assert node.clauses[0].attr == "x"
    assert node.clauses[0].alias == "t"
    assert node.clauses[1].agg == Aggregator.SUM
    assert node.clauses[1].attr == "y"
    assert node.clauses[1].alias == "g"


def test_parse_regroup_form_unchanged() -> None:
    """R group ({a, b} as alias) still parses to the regroup Group node."""
    node = _expr("R group ({a, b} as alias)")
    assert isinstance(node, Group)
    assert node.attrs == ["a", "b"]
    assert node.alias == "alias"


# ---------------------------------------------------------------------------
# LaTeX generation tests
# ---------------------------------------------------------------------------


def test_emit_count() -> None:
    r"""R group (Count(x) as total) emits \mathrm{Count}(x)~\mathrm{as}~total."""
    result = _expr_latex("R group (Count(x) as total)")
    assert r"\mathrm{Count}(x)~\mathrm{as}~total" in result
    assert r"\mathrm{Group}" in result


def test_emit_sum() -> None:
    r"""Sum aggregator emits \mathrm{Sum}(attr)~\mathrm{as}~alias."""
    result = _expr_latex("R group (Sum(y) as grand)")
    assert r"\mathrm{Sum}(y)~\mathrm{as}~grand" in result


def test_emit_avg() -> None:
    r"""Avg aggregator emits \mathrm{Avg}(attr)~\mathrm{as}~alias."""
    result = _expr_latex("R group (Avg(score) as mean)")
    assert r"\mathrm{Avg}(score)~\mathrm{as}~mean" in result


def test_emit_min() -> None:
    r"""Min aggregator emits \mathrm{Min}(attr)~\mathrm{as}~alias."""
    result = _expr_latex("R group (Min(val) as lo)")
    assert r"\mathrm{Min}(val)~\mathrm{as}~lo" in result


def test_emit_max() -> None:
    r"""Max aggregator emits \mathrm{Max}(attr)~\mathrm{as}~alias."""
    result = _expr_latex("R group (Max(val) as hi)")
    assert r"\mathrm{Max}(val)~\mathrm{as}~hi" in result


def test_emit_median() -> None:
    r"""Median aggregator emits \mathrm{Median}(attr)~\mathrm{as}~alias."""
    result = _expr_latex("R group (Median(score) as med)")
    assert r"\mathrm{Median}(score)~\mathrm{as}~med" in result


def test_emit_two_clauses_comma_separated() -> None:
    """Two aggregators in one GROUP emit with comma separation."""
    result = _expr_latex("R group (Count(x) as t, Sum(y) as g)")
    assert r"\mathrm{Count}(x)~\mathrm{as}~t" in result
    assert r"\mathrm{Sum}(y)~\mathrm{as}~g" in result
    # Comma must connect the two clauses
    assert r"\mathrm{Count}(x)~\mathrm{as}~t, \mathrm{Sum}(y)~\mathrm{as}~g" in result


def test_emit_regroup_form_unchanged() -> None:
    r"""Regroup form R group ({a, b} as alias) still emits GROUP/AS macros."""
    result = _expr_latex("R group ({a, b} as alias)")
    assert r"\mathop{\mathrm{GROUP}}" in result


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------


def test_error_mix_regroup_and_aggregator() -> None:
    """Mixing regroup and aggregator forms in one GROUP RHS is rejected."""
    with pytest.raises(ParserError, match="cannot mix regroup and aggregator forms"):
        _expr("R group (Count(x) as t, {a} as alias)")


def test_error_unknown_token_after_lparen() -> None:
    """An unexpected token after '(' in GROUP raises ParserError."""
    with pytest.raises(ParserError):
        _expr("R group (x as t)")
