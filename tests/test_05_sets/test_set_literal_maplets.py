"""Tests for set literals with maplets (Phase 11.7)."""

from __future__ import annotations

from txt2tex.ast_nodes import BinaryOp, Identifier, Number, SetLiteral, Tuple
from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser


class TestSetLiteralMapletParser:
    """Test parsing of set literals with maplets."""

    def test_simple_maplet_set(self) -> None:
        """Test parsing set literal with single maplet."""
        tokens = Lexer("{1 |-> a}").tokenize()
        ast = Parser(tokens).parse()
        assert isinstance(ast, SetLiteral)
        assert len(ast.elements) == 1
        elem = ast.elements[0]
        assert isinstance(elem, BinaryOp)
        assert elem.operator == "|->"
        assert isinstance(elem.left, Number)
        assert elem.left.value == "1"
        assert isinstance(elem.right, Identifier)
        assert elem.right.name == "a"

    def test_multiple_maplets(self) -> None:
        """Test parsing set literal with multiple maplets."""
        tokens = Lexer("{1 |-> a, 2 |-> b, 3 |-> c}").tokenize()
        ast = Parser(tokens).parse()
        assert isinstance(ast, SetLiteral)
        assert len(ast.elements) == 3
        for elem in ast.elements:
            assert isinstance(elem, BinaryOp)
            assert elem.operator == "|->"

    def test_maplet_with_expressions(self) -> None:
        """Test set literal with maplets containing expressions."""
        tokens = Lexer("{x + 1 |-> y * 2, a |-> b}").tokenize()
        ast = Parser(tokens).parse()
        assert isinstance(ast, SetLiteral)
        assert len(ast.elements) == 2
        first = ast.elements[0]
        assert isinstance(first, BinaryOp)
        assert first.operator == "|->"
        assert isinstance(first.left, BinaryOp)
        assert isinstance(first.right, BinaryOp)

    def test_solution_29a_example(self) -> None:
        """Test Solution 29(a) example."""
        tokens = Lexer("{2 |-> 4, 3 |-> 3, 3 |-> 4, 4 |-> 2}").tokenize()
        ast = Parser(tokens).parse()
        assert isinstance(ast, SetLiteral)
        assert len(ast.elements) == 4

    def test_solution_34a_example(self) -> None:
        """Test Solution 34(a) example."""
        tokens = Lexer("{1 |-> a, 2 |-> b, 3 |-> c, 4 |-> b}").tokenize()
        ast = Parser(tokens).parse()
        assert isinstance(ast, SetLiteral)
        assert len(ast.elements) == 4

    def test_mixed_maplets_and_values(self) -> None:
        """Test set literal mixing maplets land regular values."""
        tokens = Lexer("{1, 2 |-> 3, 4}").tokenize()
        ast = Parser(tokens).parse()
        assert isinstance(ast, SetLiteral)
        assert len(ast.elements) == 3
        assert isinstance(ast.elements[0], Number)
        assert isinstance(ast.elements[1], BinaryOp)
        assert ast.elements[1].operator == "|->"
        assert isinstance(ast.elements[2], Number)


class TestSetLiteralMapletLatex:
    """Test LaTeX generation for set literals with maplets."""

    def test_simple_maplet_latex(self) -> None:
        """Test LaTeX generation for single maplet."""
        tokens = Lexer("{1 |-> a}").tokenize()
        ast = Parser(tokens).parse()
        assert isinstance(ast, SetLiteral)
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)
        assert "\\{" in latex
        assert "\\}" in latex
        assert "\\mapsto" in latex
        assert "1" in latex
        assert "a" in latex

    def test_multiple_maplets_latex(self) -> None:
        """Test LaTeX generation for multiple maplets."""
        tokens = Lexer("{1 |-> a, 2 |-> b, 3 |-> c}").tokenize()
        ast = Parser(tokens).parse()
        assert isinstance(ast, SetLiteral)
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)
        assert latex.count(",") == 2
        assert latex.count("\\mapsto") == 3

    def test_solution_29a_latex(self) -> None:
        """Test LaTeX generation for Solution 29(a)."""
        tokens = Lexer("{2 |-> 4, 3 |-> 3, 3 |-> 4, 4 |-> 2}").tokenize()
        ast = Parser(tokens).parse()
        assert isinstance(ast, SetLiteral)
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)
        assert "\\{" in latex
        assert "\\}" in latex
        assert latex.count("\\mapsto") == 4

    def test_solution_34a_latex(self) -> None:
        """Test LaTeX generation for Solution 34(a)."""
        tokens = Lexer("{1 |-> a, 2 |-> b, 3 |-> c, 4 |-> b}").tokenize()
        ast = Parser(tokens).parse()
        assert isinstance(ast, SetLiteral)
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)
        assert "\\{" in latex
        assert "\\}" in latex
        assert latex.count("\\mapsto") == 4

    def test_empty_set_latex(self) -> None:
        """Test LaTeX generation for empty set."""
        tokens = Lexer("{}").tokenize()
        ast = Parser(tokens).parse()
        assert isinstance(ast, SetLiteral)
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)
        assert latex == "\\{\\}"


class TestSetLiteralEdgeCases:
    """Test edge cases for set literal with maplets."""

    def test_nested_set_with_maplets(self) -> None:
        """Test set containing sets with maplets."""
        tokens = Lexer("{{1 |-> 2}, {3 |-> 4}}").tokenize()
        ast = Parser(tokens).parse()
        assert isinstance(ast, SetLiteral)
        assert len(ast.elements) == 2
        assert isinstance(ast.elements[0], SetLiteral)
        assert isinstance(ast.elements[1], SetLiteral)

    def test_maplet_with_tuple_values(self) -> None:
        """Test maplet with tuple values."""
        tokens = Lexer("{(a, b) |-> (c, d)}").tokenize()
        ast = Parser(tokens).parse()
        assert isinstance(ast, SetLiteral)
        assert len(ast.elements) == 1
        elem = ast.elements[0]
        assert isinstance(elem, BinaryOp)
        assert elem.operator == "|->"
        assert isinstance(elem.left, Tuple)
        assert isinstance(elem.right, Tuple)
