"""Tests for parser edge cases and error handling to improve coverage.

This file focuses on error paths and edge cases to improve parser coverage.
Only tests that run quickly and don't hang are included.
"""

from __future__ import annotations

import pytest

from txt2tex.ast_nodes import Quantifier, SetComprehension
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser, ParserError


def test_incomplete_solution_marker() -> None:
    """Test error when solution marker is not closed."""
    text = "** Solution 1"  # Missing closing **
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    with pytest.raises(ParserError, match="Expected closing '\\*\\*'"):
        parser.parse()


def test_missing_quantifier_pipe() -> None:
    """Test error when quantifier is missing pipe separator."""
    text = "forall x : N  x > 0"  # Missing |
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    with pytest.raises(ParserError, match="Expected '\\|' after quantifier binding"):
        parser.parse()


def test_missing_set_comprehension_pipe() -> None:
    """Test error when set comprehension is missing pipe or period."""
    text = "{x : N  x > 0}"  # Missing | or .
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    with pytest.raises(
        ParserError, match="Expected '\\|' or '\\.' after set comprehension binding"
    ):
        parser.parse()


def test_missing_set_comprehension_closing_brace() -> None:
    """Test error when set comprehension is not closed."""
    text = "{x : N | x > 0"  # Missing }
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    with pytest.raises(ParserError, match="Expected '\\}' to close set comprehension"):
        parser.parse()


def test_set_comprehension_no_domain() -> None:
    """Test set comprehension without domain (just variable)."""
    text = "{x | x > 0}"
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    result = parser.parse()

    # Result is SetComprehension directly (single expression)
    assert isinstance(result, SetComprehension)
    assert result.domain is None


def test_set_comprehension_with_expression_part() -> None:
    """Test set comprehension with expression part (x : N | P . E)."""
    text = "{x : N | x > 0 . x * 2}"
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    result = parser.parse()

    assert isinstance(result, SetComprehension)
    assert result.expression is not None


def test_set_comprehension_multiple_variables() -> None:
    """Test set comprehension with multiple comma-separated variables."""
    text = "{x, y : N | x + y = 10}"
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    result = parser.parse()

    assert isinstance(result, SetComprehension)
    assert len(result.variables) == 2
    assert result.variables == ["x", "y"]


def test_quantifier_no_domain() -> None:
    """Test quantifier without domain."""
    text = "forall x | x > 0"
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    result = parser.parse()

    assert isinstance(result, Quantifier)
    assert result.domain is None


def test_mu_with_expression() -> None:
    """Test mu operator with expression part."""
    text = "(mu x : N | x > 0 . x + 1)"
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    result = parser.parse()

    assert isinstance(result, Quantifier)
    assert result.quantifier == "mu"
    assert result.expression is not None


def test_truth_table_invalid_first_token() -> None:
    """Test truth table with invalid starting token."""
    text = "TRUTH TABLE:\n123 | 456"  # Numbers not identifiers
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    with pytest.raises(ParserError, match="Expected truth table header row"):
        parser.parse()


def test_truth_table_no_headers() -> None:
    """Test truth table with no headers."""
    text = "TRUTH TABLE:\n"  # Empty table
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    with pytest.raises(ParserError, match="Expected truth table header"):
        parser.parse()
