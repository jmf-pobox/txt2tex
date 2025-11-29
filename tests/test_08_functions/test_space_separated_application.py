"""Tests for space-separated function application.

Allows function application without parentheses: f x instead of f(x).
Syntax: f x y → (f x) y (left-associative)
"""

from __future__ import annotations

from txt2tex.ast_nodes import BinaryOp, Document, FunctionApp, Identifier, Number
from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser


class TestSpaceSeparatedApplicationParser:
    """Test parser handling of space-separated function application."""

    def test_simple_application(self) -> None:
        """f x should parse as FunctionApp(f, [x])."""
        text = "f x"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, FunctionApp)
        assert isinstance(ast.function, Identifier)
        assert ast.function.name == "f"
        assert len(ast.args) == 1
        assert isinstance(ast.args[0], Identifier)
        assert ast.args[0].name == "x"

    def test_multiple_arguments(self) -> None:
        """f x y should parse as (f x) y → FunctionApp(FunctionApp(f, [x]), [y])."""
        text = "f x y"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, FunctionApp)
        assert isinstance(ast.function, FunctionApp)
        inner = ast.function
        assert isinstance(inner.function, Identifier)
        assert inner.function.name == "f"
        assert len(inner.args) == 1
        assert isinstance(inner.args[0], Identifier)
        assert inner.args[0].name == "x"
        assert len(ast.args) == 1
        assert isinstance(ast.args[0], Identifier)
        assert ast.args[0].name == "y"

    def test_three_arguments(self) -> None:
        """f x y z should parse as ((f x) y) z."""
        text = "f x y z"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, FunctionApp)
        assert len(ast.args) == 1
        assert isinstance(ast.args[0], Identifier)
        assert ast.args[0].name == "z"
        middle = ast.function
        assert isinstance(middle, FunctionApp)
        assert len(middle.args) == 1
        assert isinstance(middle.args[0], Identifier)
        assert middle.args[0].name == "y"
        inner = middle.function
        assert isinstance(inner, FunctionApp)
        assert isinstance(inner.function, Identifier)
        assert inner.function.name == "f"
        assert len(inner.args) == 1
        assert isinstance(inner.args[0], Identifier)
        assert inner.args[0].name == "x"

    def test_application_with_addition(self) -> None:
        """f x + g y should parse as (f x) + (g y)."""
        text = "f x + g y"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "+"
        assert isinstance(ast.left, FunctionApp)
        assert isinstance(ast.left.function, Identifier)
        assert ast.left.function.name == "f"
        assert len(ast.left.args) == 1
        assert isinstance(ast.left.args[0], Identifier)
        assert ast.left.args[0].name == "x"
        assert isinstance(ast.right, FunctionApp)
        assert isinstance(ast.right.function, Identifier)
        assert ast.right.function.name == "g"
        assert len(ast.right.args) == 1
        assert isinstance(ast.right.args[0], Identifier)
        assert ast.right.args[0].name == "y"

    def test_application_vs_parenthesized_application(self) -> None:
        """f(x) should be parenthesized application, f x should be space-separated."""
        text1 = "f(x)"
        lexer1 = Lexer(text1)
        tokens1 = lexer1.tokenize()
        parser1 = Parser(tokens1)
        ast1 = parser1.parse()
        text2 = "f x"
        lexer2 = Lexer(text2)
        tokens2 = lexer2.tokenize()
        parser2 = Parser(tokens2)
        ast2 = parser2.parse()
        assert isinstance(ast1, FunctionApp)
        assert isinstance(ast2, FunctionApp)
        assert isinstance(ast1.function, Identifier)
        assert isinstance(ast2.function, Identifier)
        assert ast1.function.name == ast2.function.name == "f"
        assert isinstance(ast1.args[0], Identifier)
        assert isinstance(ast2.args[0], Identifier)
        assert ast1.args[0].name == ast2.args[0].name == "x"

    def test_mixed_application_styles(self) -> None:
        """f(x) y should parse as (f(x)) y."""
        text = "f(x) y"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, FunctionApp)
        assert isinstance(ast.function, FunctionApp)
        inner = ast.function
        assert isinstance(inner.function, Identifier)
        assert inner.function.name == "f"
        assert len(inner.args) == 1
        assert isinstance(inner.args[0], Identifier)
        assert inner.args[0].name == "x"
        assert len(ast.args) == 1
        assert isinstance(ast.args[0], Identifier)
        assert ast.args[0].name == "y"

    def test_application_stops_at_equals(self) -> None:
        """f x = y should parse as (f x) = y, lnot f (x = y)."""
        text = "f x = y"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "="
        assert isinstance(ast.left, FunctionApp)
        assert isinstance(ast.left.function, Identifier)
        assert ast.left.function.name == "f"
        assert isinstance(ast.right, Identifier)
        assert ast.right.name == "y"

    def test_application_with_numbers(self) -> None:
        """f 42 should work with number arguments."""
        text = "f 42"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, FunctionApp)
        assert isinstance(ast.function, Identifier)
        assert ast.function.name == "f"
        assert len(ast.args) == 1
        assert isinstance(ast.args[0], Number)
        assert ast.args[0].value == "42"


class TestSpaceSeparatedApplicationLatex:
    """Test LaTeX generation for space-separated application."""

    def test_simple_application_latex(self) -> None:
        """Test LaTeX rendering of f x."""
        text = "f x"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert not isinstance(ast, Document)
        generator = LaTeXGenerator(use_fuzz=False)
        latex = generator.generate_expr(ast)
        assert "f" in latex
        assert "x" in latex

    def test_multiple_arguments_latex(self) -> None:
        """Test LaTeX rendering of f x y."""
        text = "f x y"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert not isinstance(ast, Document)
        generator = LaTeXGenerator(use_fuzz=False)
        latex = generator.generate_expr(ast)
        assert "f" in latex
        assert "x" in latex
        assert "y" in latex
