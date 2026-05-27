"""Tests for GROUP aggregate abbreviations followed by more abbreviations.

Three bugs exposed by this input:

1. GROUP newline continuation: after ``E == D group (Count(x) as y)``,
   the continuation logic consumes the trailing NEWLINE, causing the
   next abbreviation to be parsed as part of E's expression.

2. ``F`` as FINSET: single-letter ``F`` lexes as TokenType.FINSET
   (finite-set operator), not IDENTIFIER, so ``F == expr`` is not
   recognised as an abbreviation.

3. ``>`` inside ``[...]`` lexes as RANGLE: in ``sigma[x>1](R)``, the
   ``>`` becomes RANGLE instead of GREATER_THAN, breaking the sigma
   predicate parse.
"""

from __future__ import annotations

import pytest

from txt2tex.ast_nodes import (
    Abbreviation,
    Document,
    Expr,
    GroupAggregate,
    Project,
    Restrict,
)
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser
from txt2tex.tokens import Token, TokenType


def _lex(src: str) -> list[Token]:
    return Lexer(src).tokenize()


def _parse(src: str) -> Document:
    result = Parser(_lex(src)).parse()
    assert isinstance(result, Document)
    return result


def _expr(src: str) -> Expr:
    result = Parser(_lex(src)).parse()
    item: Expr = result.items[0] if isinstance(result, Document) else result  # type: ignore[assignment]
    return item


# ===================================================================
# Bug 1: GROUP newline continuation swallows the next line
# ===================================================================


class TestGroupNewlineContinuation:
    """After GROUP aggregate, a bare newline must NOT be treated as
    a line continuation.  The next line is a new statement."""

    def test_abbreviation_after_group_aggregate(self) -> None:
        """Abbreviation on the line after a GROUP aggregate must parse
        as a separate Abbreviation node."""
        src = "E == D group (Count(a) as ca)\nG == E"
        doc = _parse(src)
        assert len(doc.items) == 2
        assert isinstance(doc.items[0], Abbreviation)
        assert doc.items[0].name == "E"
        assert isinstance(doc.items[0].expression, GroupAggregate)
        assert isinstance(doc.items[1], Abbreviation)
        assert doc.items[1].name == "G"

    def test_two_group_aggregates_in_sequence(self) -> None:
        """Two GROUP aggregate abbreviations on consecutive lines."""
        src = "X == R group (Count(a) as ca)\nY == S group (Sum(b) as sb)"
        doc = _parse(src)
        assert len(doc.items) == 2
        assert isinstance(doc.items[0], Abbreviation)
        assert doc.items[0].name == "X"
        assert isinstance(doc.items[0].expression, GroupAggregate)
        assert isinstance(doc.items[1], Abbreviation)
        assert doc.items[1].name == "Y"
        assert isinstance(doc.items[1].expression, GroupAggregate)

    def test_expression_after_group_aggregate(self) -> None:
        """A non-abbreviation expression after GROUP aggregate."""
        src = "X == R group (Count(a) as ca)\npi[a,b](X)"
        doc = _parse(src)
        assert len(doc.items) == 2
        assert isinstance(doc.items[0], Abbreviation)
        assert isinstance(doc.items[1], Project)


# ===================================================================
# Bug 2: F (and P) are reserved words, not usable as abbreviation names
# ===================================================================


class TestReservedWordAbbreviations:
    """Single-letter names that collide with Z type operators
    (F → FINSET, P → POWER) must still be usable as abbreviation
    names when followed by ``==``."""

    def test_f_as_abbreviation_name(self) -> None:
        """F == expr should parse as an abbreviation, not as FINSET prefix."""
        src = "F == pi[a,b](R)"
        doc = _parse(src)
        assert len(doc.items) == 1
        assert isinstance(doc.items[0], Abbreviation)
        assert doc.items[0].name == "F"

    def test_p_as_abbreviation_name(self) -> None:
        """P == expr should parse as an abbreviation, not as POWER prefix."""
        src = "P == sigma[x > 0](R)"
        doc = _parse(src)
        assert len(doc.items) == 1
        assert isinstance(doc.items[0], Abbreviation)
        assert doc.items[0].name == "P"


# ===================================================================
# Bug 3: > inside [...] lexes as RANGLE instead of GREATER_THAN
# ===================================================================


class TestGreaterThanInBrackets:
    """``>`` inside sigma[...] must lex as GREATER_THAN, not RANGLE."""

    @pytest.mark.xfail(reason="Gotcha #7: unspaced > lexes as RANGLE")
    def test_sigma_greater_than_predicate(self) -> None:
        """sigma[x>1](R) must parse with > as a comparison operator."""
        expr = _expr("sigma[x>1](R)")
        assert isinstance(expr, Restrict)

    def test_sigma_greater_equal_predicate(self) -> None:
        """sigma[x>=1](R) must parse with >= as comparison."""
        expr = _expr("sigma[x>=1](R)")
        assert isinstance(expr, Restrict)

    def test_sigma_greater_than_with_spaces(self) -> None:
        """sigma[x > 1](R) — spaced form should also work."""
        expr = _expr("sigma[x > 1](R)")
        assert isinstance(expr, Restrict)

    @pytest.mark.xfail(reason="Gotcha #7: unspaced > lexes as RANGLE")
    def test_lex_greater_than_inside_sigma_brackets(self) -> None:
        """The > token inside sigma[...] should be GREATER_THAN."""
        tokens = _lex("sigma[x>1](R)")
        gt_tokens = [t for t in tokens if t.value == ">"]
        assert len(gt_tokens) == 1
        assert gt_tokens[0].type == TokenType.GREATER_THAN


# ===================================================================
# Integration: the full user scenario
# ===================================================================


class TestFullRelationalAlgebraChain:
    """Six consecutive abbreviation definitions — the user's actual input.
    Exercises all three bugs simultaneously."""

    def test_six_line_chain(self) -> None:
        src = (
            "A == pi[username,job](Members)\n"
            "B == pi[groupname,leader](Groups)\n"
            "C == B[username/leader]\n"
            "D == A join C\n"
            "E == D group (Count(groupname) as groupcount)\n"
            "G == pi[username,job](sigma[groupcount > 1](E))"
        )
        doc = _parse(src)
        assert len(doc.items) == 6
        for i, name in enumerate(["A", "B", "C", "D", "E", "G"]):
            item = doc.items[i]
            assert isinstance(item, Abbreviation), (
                f"Item {i} should be Abbreviation({name}), got {type(item).__name__}"
            )
            assert item.name == name
