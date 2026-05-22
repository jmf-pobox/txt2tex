"""Tests for the bag_diff keyword (bag difference, Z RM §4.6.2).

bag_diff emits \\uminus — the fuzz bag-difference operator.
Precedence and parser slot mirror bag_union / \\uplus exactly.
"""

from __future__ import annotations

import pytest

from txt2tex.ast_nodes import BagLiteral, BinaryOp, Identifier
from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer, LexerError
from txt2tex.parser import Parser
from txt2tex.tokens import TokenType


def _gen(source: str, *, use_fuzz: bool = True) -> str:
    """Parse source and return the generated LaTeX document body."""
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    doc = parser.parse()
    gen = LaTeXGenerator(use_fuzz=use_fuzz)
    return gen.generate_document(doc)


def _lex(source: str) -> list[TokenType]:
    """Return a list of token types for the given source."""
    lexer = Lexer(source)
    return [t.type for t in lexer.tokenize()]


# ---------------------------------------------------------------------------
# Lexer
# ---------------------------------------------------------------------------


class TestBagDiffLexer:
    """bag_diff lexes to BAG_DIFF; reserved word blocks decoration."""

    def test_keyword_produces_bag_diff_token(self) -> None:
        """'bag_diff' yields a BAG_DIFF token."""
        types = _lex("b1 bag_diff b2")
        assert TokenType.BAG_DIFF in types

    def test_bag_diff_not_decorated(self) -> None:
        """Decoration on 'bag_diff' is a lexer error."""
        with pytest.raises(LexerError, match="Cannot decorate reserved keyword"):
            _lex("bag_diff'")


# ---------------------------------------------------------------------------
# Parser / AST
# ---------------------------------------------------------------------------


class TestBagDiffParser:
    """bag_diff parses into a BinaryOp with operator value 'bag_diff'."""

    def test_simple_binary_op(self) -> None:
        """b1 bag_diff b2 → BinaryOp(operator='bag_diff', ...)."""
        tokens = Lexer("b1 bag_diff b2").tokenize()
        expr = Parser(tokens).parse()
        assert isinstance(expr, BinaryOp)
        assert expr.operator == "bag_diff"
        assert isinstance(expr.left, Identifier)
        assert expr.left.name == "b1"
        assert isinstance(expr.right, Identifier)
        assert expr.right.name == "b2"

    def test_left_associative_chaining(self) -> None:
        """b1 bag_diff b2 bag_diff b3 → left-associative grouping."""
        tokens = Lexer("b1 bag_diff b2 bag_diff b3").tokenize()
        expr = Parser(tokens).parse()
        assert isinstance(expr, BinaryOp)
        assert expr.operator == "bag_diff"
        assert isinstance(expr.left, BinaryOp)
        assert expr.left.operator == "bag_diff"

    def test_with_bag_literal_rhs(self) -> None:
        """b bag_diff [[x?]] parses correctly with a BagLiteral RHS."""
        tokens = Lexer("b bag_diff [[x?]]").tokenize()
        expr = Parser(tokens).parse()
        assert isinstance(expr, BinaryOp)
        assert expr.operator == "bag_diff"
        assert isinstance(expr.right, BagLiteral)


# ---------------------------------------------------------------------------
# Generator — emits \uminus
# ---------------------------------------------------------------------------


class TestBagDiffGenerator:
    """bag_diff generates \\uminus in all relevant contexts."""

    def test_simple_expression_emits_uminus(self) -> None:
        """b1 bag_diff b2 emits \\uminus."""
        source = """\
given X

axdef
  b1 : bag X
  b2 : bag X
  b3 : bag X
where
  b3 = b1 bag_diff b2
end
"""
        latex = _gen(source)
        assert r"\uminus" in latex

    def test_with_bag_literal_rhs_emits_uminus(self) -> None:
        """coins bag_diff [[c?]] emits \\uminus and bag-literal delimiters."""
        source = """\
given Coin

schema RemoveCoin
  coins : bag Coin
  coins' : bag Coin
  c? : Coin
where
  coins' = coins bag_diff [[c?]]
end
"""
        latex = _gen(source)
        assert r"\uminus" in latex
        # Bag literal delimiters (\lbag ... \rbag)
        assert r"\lbag" in latex

    def test_bag_union_still_emits_uplus(self) -> None:
        """Regression: bag_union still emits \\uplus after this change."""
        source = """\
given X

axdef
  b1 : bag X
  b2 : bag X
  b3 : bag X
where
  b3 = b1 bag_union b2
end
"""
        latex = _gen(source)
        assert r"\uplus" in latex
        assert r"\uminus" not in latex

    def test_mixed_bag_ops_in_one_expression(self) -> None:
        """bag_union and bag_diff together emit \\uplus and \\uminus."""
        source = """\
given X

axdef
  a : bag X
  b : bag X
  c : bag X
  d : bag X
where
  d = (a bag_union b) bag_diff c
end
"""
        latex = _gen(source)
        assert r"\uplus" in latex
        assert r"\uminus" in latex
