"""Test cases for tuple patterns in quantifiers (Phase 28).

Tests the ability to destructure tuples in quantifier variable bindings.
Examples: forall (x, y) : T | P
"""

from __future__ import annotations

import pytest

from txt2tex.ast_nodes import Identifier, Quantifier, Tuple
from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser, ParserError


def test_simple_tuple_pattern_forall():
    """Test forall with simple 2-element tuple pattern."""
    text = "forall (x, y) : T | x > y"
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)

    quant = parser.parse()
    assert isinstance(quant, Quantifier)
    assert quant.quantifier == "forall"
    assert quant.variables == ["x", "y"]
    assert isinstance(quant.tuple_pattern, Tuple)
    assert len(quant.tuple_pattern.elements) == 2
    assert isinstance(quant.tuple_pattern.elements[0], Identifier)
    assert quant.tuple_pattern.elements[0].name == "x"
    assert isinstance(quant.tuple_pattern.elements[1], Identifier)
    assert quant.tuple_pattern.elements[1].name == "y"


def test_tuple_pattern_with_three_variables():
    """Test tuple pattern with three variables."""
    text = "exists (a, b, c) : T | a > 0"
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)

    quant = parser.parse()
    assert isinstance(quant, Quantifier)
    assert quant.quantifier == "exists"
    assert quant.variables == ["a", "b", "c"]
    assert isinstance(quant.tuple_pattern, Tuple)
    assert len(quant.tuple_pattern.elements) == 3


def test_tuple_pattern_latex_generation():
    """Test that tuple patterns generate correct LaTeX."""
    text = "forall (s, e) : ran my_episodes | s > 0"
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    doc = parser.parse()

    generator = LaTeXGenerator(use_fuzz=False)
    latex = generator.generate_document(doc)

    # Should contain tuple pattern in output
    assert r"\forall (s, e)" in latex or r"\forall (s, e)" in latex
    # Should contain domain
    assert r"\ran" in latex
    assert "my_episodes" in latex or "my\\_episodes" in latex


def test_tuple_pattern_with_complex_domain():
    """Test tuple pattern with complex domain expression."""
    text = "forall (x, y) : A cross B | x elem A"
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)

    quant = parser.parse()
    assert isinstance(quant, Quantifier)
    assert quant.variables == ["x", "y"]
    assert quant.tuple_pattern is not None


def test_tuple_pattern_exists1():
    """Test tuple pattern with unique existence quantifier."""
    text = "exists1 (x, y) : T | x = y"
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)

    quant = parser.parse()
    assert isinstance(quant, Quantifier)
    assert quant.quantifier == "exists1"
    assert quant.variables == ["x", "y"]
    assert quant.tuple_pattern is not None


def test_empty_tuple_pattern_error():
    """Test that empty tuple pattern produces error."""
    text = "forall () : T | P"
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)

    # Empty parens trigger parse error (can't parse expression after LPAREN)
    with pytest.raises(ParserError):
        parser.parse()


def test_nested_tuple_pattern_error():
    """Test that nested tuple patterns are not supported (for now)."""
    text = "forall ((a, b), c) : T | P"
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)

    with pytest.raises(
        ParserError,
        match="Tuple pattern in quantifier must contain only identifiers",
    ):
        parser.parse()


def test_tuple_pattern_with_non_identifier_error():
    """Test that tuple pattern must contain only identifiers."""
    text = "forall (x, 2) : T | P"
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)

    with pytest.raises(
        ParserError,
        match="Tuple pattern in quantifier must contain only identifiers",
    ):
        parser.parse()


def test_regular_quantifier_still_works():
    """Test that regular quantifiers still work (backward compatibility)."""
    text = "forall x : N | x > 0"
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)

    quant = parser.parse()
    assert isinstance(quant, Quantifier)
    assert quant.variables == ["x"]
    assert quant.tuple_pattern is None  # No tuple pattern


def test_multi_variable_quantifier_still_works():
    """Test that multi-variable quantifiers still work."""
    text = "forall x, y : N | x > y"
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)

    quant = parser.parse()
    assert isinstance(quant, Quantifier)
    assert quant.variables == ["x", "y"]
    assert quant.tuple_pattern is None  # No tuple pattern


def test_tuple_pattern_in_nested_quantifier():
    """Test tuple pattern in nested quantifier body."""
    text = "forall (x, y) : A | exists z : B | x > z"
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)

    outer_quant = parser.parse()
    assert isinstance(outer_quant, Quantifier)
    assert outer_quant.quantifier == "forall"
    assert outer_quant.variables == ["x", "y"]
    assert outer_quant.tuple_pattern is not None

    # Check nested quantifier
    inner_quant = outer_quant.body
    assert isinstance(inner_quant, Quantifier)
    assert inner_quant.quantifier == "exists"
    assert inner_quant.variables == ["z"]


def test_tuple_pattern_with_constrained_quantifier():
    """Test tuple pattern with constrained quantifier (double pipe)."""
    text = "forall (x, y) : T | x > 0 | x > y"
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)

    quant = parser.parse()
    assert isinstance(quant, Quantifier)
    assert quant.variables == ["x", "y"]
    assert quant.tuple_pattern is not None


def test_tuple_pattern_latex_with_colon():
    """Test LaTeX uses \\colon for non-fuzz mode."""
    text = "forall (a, b) : T | a > b"
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    doc = parser.parse()

    generator = LaTeXGenerator(use_fuzz=False)
    latex = generator.generate_document(doc)

    assert r"\colon" in latex
    assert r"(a, b)" in latex


def test_tuple_pattern_latex_fuzz_mode():
    """Test LaTeX uses : for fuzz mode."""
    text = "forall (a, b) : T | a > b"
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    doc = parser.parse()

    generator = LaTeXGenerator(use_fuzz=True)
    latex = generator.generate_document(doc)

    # Fuzz uses : not \colon
    assert ": T" in latex or ":\\," in latex
    assert r"(a, b)" in latex


def test_realistic_example_from_homework():
    """Test the actual example from user's homework."""
    text = "forall (s, e) : ran my_episodes | s > 0"
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)

    quant = parser.parse()
    assert isinstance(quant, Quantifier)
    assert quant.quantifier == "forall"
    assert quant.variables == ["s", "e"]
    assert quant.tuple_pattern is not None

    # Generate LaTeX and verify it's valid
    generator = LaTeXGenerator(use_fuzz=False)
    latex = generator.generate_expr(quant)

    # Should contain the tuple pattern and domain
    assert "(s, e)" in latex
    assert "ran" in latex or r"\ran" in latex
