"""Tests for error handling and edge cases in latex_gen.py."""

from __future__ import annotations

import pytest

from txt2tex.ast_nodes import (
    BagLiteral,
    BinaryOp,
    FunctionType,
    Identifier,
    UnaryOp,
)
from txt2tex.latex_gen import LaTeXGenerator


def test_unknown_expression_type() -> None:
    """Test error for unknown expression type (line 309)."""
    gen = LaTeXGenerator()

    # Create a mock expression with an unknown type
    class UnknownExpr:
        pass

    with pytest.raises(TypeError, match="Unknown expression type"):
        gen.generate_expr(UnknownExpr())  # type: ignore[arg-type]


def test_identifier_with_fuzz_flag() -> None:
    """Test identifier with use_fuzz=True (line 328)."""
    node = Identifier(name="x_max", line=1, column=1)
    gen = LaTeXGenerator(use_fuzz=True)
    latex = gen._generate_identifier(node)

    # With fuzz, underscores are kept as-is (no escaping)
    assert latex == "x_max"


def test_identifier_fallback_case() -> None:
    """Test identifier fallback to mathit (lines 349-351)."""
    # Empty parts after split (edge case)
    node = Identifier(name="a__b", line=1, column=1)
    gen = LaTeXGenerator()
    latex = gen._generate_identifier(node)

    # Should use fallback: mathit with escaped underscores
    assert r"\mathit{" in latex
    assert r"\_" in latex


def test_identifier_multi_char_subscript() -> None:
    """Test identifier with multi-char subscript (line 347)."""
    node = Identifier(name="x_max", line=1, column=1)
    gen = LaTeXGenerator()
    latex = gen._generate_identifier(node)

    # Should add braces around multi-char subscript
    assert "x_{max}" in latex or r"\mathit{x\_max}" in latex


def test_unknown_unary_operator() -> None:
    """Test error for unknown unary operator (line 368)."""
    node = UnaryOp(
        operator="???",
        operand=Identifier(name="x", line=1, column=1),
        line=1,
        column=1,
    )
    gen = LaTeXGenerator()

    with pytest.raises(ValueError, match="Unknown unary operator"):
        gen.generate_expr(node)


def test_right_associative_parens() -> None:
    """Test parentheses for right-associative operators (line 425)."""
    # Create (a => b) => c where left child needs parens
    left = BinaryOp(
        operator="=>",
        left=Identifier(name="a", line=1, column=1),
        right=Identifier(name="b", line=1, column=1),
        line=1,
        column=1,
    )
    node = BinaryOp(
        operator="=>",
        left=left,
        right=Identifier(name="c", line=1, column=1),
        line=1,
        column=1,
    )

    gen = LaTeXGenerator()
    latex = gen.generate_expr(node)

    # Left child should be parenthesized (right-associative)
    assert "(" in latex
    assert ")" in latex


def test_unknown_binary_operator() -> None:
    """Test error for unknown binary operator (line 435)."""
    node = BinaryOp(
        operator="???",
        left=Identifier(name="x", line=1, column=1),
        right=Identifier(name="y", line=1, column=1),
        line=1,
        column=1,
    )
    gen = LaTeXGenerator()

    with pytest.raises(ValueError, match="Unknown binary operator"):
        gen.generate_expr(node)


def test_unknown_function_arrow() -> None:
    """Test error for unknown function arrow (line 655)."""
    node = FunctionType(
        arrow="???",
        domain=Identifier(name="A", line=1, column=1),
        range=Identifier(name="B", line=1, column=1),
        line=1,
        column=1,
    )
    gen = LaTeXGenerator()

    with pytest.raises(ValueError, match="Unknown function arrow"):
        gen.generate_expr(node)


def test_bag_literal_empty() -> None:
    """Test empty bag literal (line 770)."""
    node = BagLiteral(elements=[], line=1, column=1)
    gen = LaTeXGenerator()
    latex = gen.generate_expr(node)

    # Empty bag: \lbag \rbag
    assert r"\lbag" in latex
    assert r"\rbag" in latex
