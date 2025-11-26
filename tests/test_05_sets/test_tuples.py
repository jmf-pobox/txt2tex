"""Tests for tuple expressions (Phase 11.6)."""

from __future__ import annotations

import pytest

from txt2tex.ast_nodes import (
    BinaryOp,
    Identifier,
    Number,
    SetComprehension,
    Tuple,
)
from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser, ParserError


class TestTupleParser:
    """Test parsing of tuple expressions."""

    def test_simple_tuple_two_elements(self) -> None:
        """Test parsing simple 2-element tuple."""
        tokens = Lexer("(a, b)").tokenize()
        ast = Parser(tokens).parse()
        assert isinstance(ast, Tuple)
        assert len(ast.elements) == 2
        assert isinstance(ast.elements[0], Identifier)
        assert ast.elements[0].name == "a"
        assert isinstance(ast.elements[1], Identifier)
        assert ast.elements[1].name == "b"

    def test_simple_tuple_three_elements(self) -> None:
        """Test parsing 3-element tuple."""
        tokens = Lexer("(x, y, z)").tokenize()
        ast = Parser(tokens).parse()
        assert isinstance(ast, Tuple)
        assert len(ast.elements) == 3
        elem0 = ast.elements[0]
        elem1 = ast.elements[1]
        elem2 = ast.elements[2]
        assert isinstance(elem0, Identifier)
        assert isinstance(elem1, Identifier)
        assert isinstance(elem2, Identifier)
        assert elem0.name == "x"
        assert elem1.name == "y"
        assert elem2.name == "z"

    def test_tuple_with_numbers(self) -> None:
        """Test parsing tuple with numeric elements."""
        tokens = Lexer("(1, 2)").tokenize()
        ast = Parser(tokens).parse()
        assert isinstance(ast, Tuple)
        assert len(ast.elements) == 2
        assert isinstance(ast.elements[0], Number)
        assert ast.elements[0].value == "1"
        assert isinstance(ast.elements[1], Number)
        assert ast.elements[1].value == "2"

    def test_tuple_with_expressions(self) -> None:
        """Test parsing tuple with complex expressions."""
        tokens = Lexer("(a, b + 1)").tokenize()
        ast = Parser(tokens).parse()
        assert isinstance(ast, Tuple)
        assert len(ast.elements) == 2
        assert isinstance(ast.elements[0], Identifier)
        assert ast.elements[0].name == "a"
        assert isinstance(ast.elements[1], BinaryOp)
        assert ast.elements[1].operator == "+"

    def test_tuple_trailing_comma(self) -> None:
        """Test parsing tuple with trailing comma."""
        tokens = Lexer("(a, b,)").tokenize()
        ast = Parser(tokens).parse()
        assert isinstance(ast, Tuple)
        assert len(ast.elements) == 2
        elem0 = ast.elements[0]
        elem1 = ast.elements[1]
        assert isinstance(elem0, Identifier)
        assert isinstance(elem1, Identifier)
        assert elem0.name == "a"
        assert elem1.name == "b"

    def test_tuple_whitespace_handling(self) -> None:
        """Test parsing tuple with various whitespace."""
        tokens = Lexer("( a , b , c )").tokenize()
        ast = Parser(tokens).parse()
        assert isinstance(ast, Tuple)
        assert len(ast.elements) == 3

    def test_parenthesized_expression_not_tuple(self) -> None:
        """Test that (x) is parsed as expression, not tuple."""
        tokens = Lexer("(x)").tokenize()
        ast = Parser(tokens).parse()
        # Should be Identifier, not Tuple
        assert not isinstance(ast, Tuple)
        assert isinstance(ast, Identifier)
        assert ast.name == "x"

    def test_nested_tuples(self) -> None:
        """Test parsing nested tuples."""
        tokens = Lexer("((a, b), c)").tokenize()
        ast = Parser(tokens).parse()
        assert isinstance(ast, Tuple)
        assert len(ast.elements) == 2
        assert isinstance(ast.elements[0], Tuple)
        assert isinstance(ast.elements[1], Identifier)

    def test_tuple_with_four_elements(self) -> None:
        """Test parsing tuple with more than 3 elements."""
        tokens = Lexer("(a, b, c, d)").tokenize()
        ast = Parser(tokens).parse()
        assert isinstance(ast, Tuple)
        assert len(ast.elements) == 4

    def test_tuple_mixed_types(self) -> None:
        """Test parsing tuple with mixed element types."""
        tokens = Lexer("(1, x, 2 + 3)").tokenize()
        ast = Parser(tokens).parse()
        assert isinstance(ast, Tuple)
        assert len(ast.elements) == 3
        assert isinstance(ast.elements[0], Number)
        assert isinstance(ast.elements[1], Identifier)
        assert isinstance(ast.elements[2], BinaryOp)


class TestTupleLatexGeneration:
    """Test LaTeX generation for tuple expressions."""

    def test_simple_tuple_latex(self) -> None:
        """Test LaTeX generation for simple tuple."""
        tokens = Lexer("(a, b)").tokenize()
        ast = Parser(tokens).parse()
        assert isinstance(ast, Tuple)
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)
        assert latex == "(a, b)"

    def test_three_element_tuple_latex(self) -> None:
        """Test LaTeX generation for 3-element tuple."""
        tokens = Lexer("(x, y, z)").tokenize()
        ast = Parser(tokens).parse()
        assert isinstance(ast, Tuple)
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)
        assert latex == "(x, y, z)"

    def test_tuple_with_numbers_latex(self) -> None:
        """Test LaTeX generation for tuple with numbers."""
        tokens = Lexer("(1, 2)").tokenize()
        ast = Parser(tokens).parse()
        assert isinstance(ast, Tuple)
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)
        assert latex == "(1, 2)"

    def test_tuple_with_expressions_latex(self) -> None:
        """Test LaTeX generation for tuple with expressions."""
        tokens = Lexer("(a, b + 1)").tokenize()
        ast = Parser(tokens).parse()
        assert isinstance(ast, Tuple)
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)
        assert latex == "(a, b + 1)"

    def test_nested_tuple_latex(self) -> None:
        """Test LaTeX generation for nested tuples."""
        tokens = Lexer("((a, b), c)").tokenize()
        ast = Parser(tokens).parse()
        assert isinstance(ast, Tuple)
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)
        assert latex == "((a, b), c)"

    def test_four_element_tuple_latex(self) -> None:
        """Test LaTeX generation for 4-element tuple."""
        tokens = Lexer("(a, b, c, d)").tokenize()
        ast = Parser(tokens).parse()
        assert isinstance(ast, Tuple)
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)
        assert latex == "(a, b, c, d)"


class TestTupleInSetComprehension:
    """Test tuples in set comprehension bodies."""

    def test_set_comprehension_with_tuple_body(self) -> None:
        """Test parsing set comprehension with tuple in body."""
        tokens = Lexer("{ n : N | n <= 4 . (n, n^2) }").tokenize()
        ast = Parser(tokens).parse()
        # Should parse as SetComprehension
        assert isinstance(ast, SetComprehension)
        assert ast.expression is not None
        assert isinstance(ast.expression, Tuple)
        assert len(ast.expression.elements) == 2

    def test_set_comprehension_tuple_latex(self) -> None:
        """Test LaTeX generation for set comprehension with tuple."""
        tokens = Lexer("{ n : N | n <= 4 . (n, n^2) }").tokenize()
        ast = Parser(tokens).parse()
        assert isinstance(ast, SetComprehension)
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)
        # Should render as set comprehension with tuple in expression part
        assert r"\{" in latex
        assert r"\mid" in latex
        assert r"\bullet" in latex
        # Single-character exponents don't get braces
        assert r"(n, n \bsup 2 \esup)" in latex

    def test_set_comprehension_multi_var_tuple(self) -> None:
        """Test set comprehension with multiple vars and tuple expression."""
        tokens = Lexer("{ x, y : N | x > 0 and y > 0 . (x, y) }").tokenize()
        ast = Parser(tokens).parse()
        assert isinstance(ast, SetComprehension)
        assert ast.expression is not None
        assert isinstance(ast.expression, Tuple)


class TestCartesianProductTuples:
    """Test tuples in Cartesian product contexts."""

    def test_tuple_in_set_membership(self) -> None:
        """Test parsing tuple in set membership expression."""
        tokens = Lexer("(a, b) elem A cross B").tokenize()
        ast = Parser(tokens).parse()
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "elem"
        assert isinstance(ast.left, Tuple)

    def test_tuple_membership_latex(self) -> None:
        """Test LaTeX generation for tuple membership."""
        tokens = Lexer("(a, b) elem A cross B").tokenize()
        ast = Parser(tokens).parse()
        assert isinstance(ast, BinaryOp)
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)
        assert "(a, b)" in latex
        assert r"\in" in latex
        assert r"\cross" in latex


class TestTupleEdgeCases:
    """Test edge cases for tuple parsing."""

    def test_empty_parens_error(self) -> None:
        """Test that empty parentheses raise parser error."""
        tokens = Lexer("()").tokenize()
        with pytest.raises(ParserError):
            Parser(tokens).parse()

    def test_single_element_no_comma(self) -> None:
        """Test that (x) without comma is not a tuple."""
        tokens = Lexer("(x)").tokenize()
        ast = Parser(tokens).parse()
        # Should be Identifier, not Tuple
        assert not isinstance(ast, Tuple)
        assert isinstance(ast, Identifier)

    def test_complex_nested_expression(self) -> None:
        """Test tuple with complex nested expressions."""
        tokens = Lexer("(a + b, c * d, (e, f))").tokenize()
        ast = Parser(tokens).parse()
        assert isinstance(ast, Tuple)
        assert len(ast.elements) == 3
        assert isinstance(ast.elements[0], BinaryOp)
        assert isinstance(ast.elements[1], BinaryOp)
        assert isinstance(ast.elements[2], Tuple)
