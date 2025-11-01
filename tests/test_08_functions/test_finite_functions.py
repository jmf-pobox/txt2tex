"""Tests for Phase 34: Finite Partial Function Operator (77->)."""

from __future__ import annotations

from txt2tex.ast_nodes import FunctionType, Identifier
from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser
from txt2tex.tokens import TokenType


class TestFiniteFunctionLexer:
    """Tests for finite function lexer features."""

    def test_finite_function_operator(self) -> None:
        """Test lexing 77-> operator."""
        lexer = Lexer("X 77-> Y")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.IDENTIFIER
        assert tokens[0].value == "X"
        assert tokens[1].type == TokenType.FINFUN
        assert tokens[1].value == "77->"
        assert tokens[2].type == TokenType.IDENTIFIER
        assert tokens[2].value == "Y"

    def test_finite_function_vs_number(self) -> None:
        """Test that 7 by itself is still a number."""
        lexer = Lexer("7")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.NUMBER
        assert tokens[0].value == "7"

    def test_finite_function_vs_number_space(self) -> None:
        """Test that '7 ' followed by something else is not finite function."""
        lexer = Lexer("7 X")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.NUMBER
        assert tokens[0].value == "7"
        assert tokens[1].type == TokenType.IDENTIFIER


class TestFiniteFunctionParser:
    """Tests for finite function parser features."""

    def test_parse_simple_finite_function(self) -> None:
        """Test parsing X 77-> Y."""
        lexer = Lexer("X 77-> Y")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, FunctionType)
        assert ast.arrow == "77->"
        assert isinstance(ast.domain, Identifier)
        assert ast.domain.name == "X"
        assert isinstance(ast.range, Identifier)
        assert ast.range.name == "Y"

    def test_parse_nested_finite_function(self) -> None:
        """Test parsing X 77-> Y 77-> Z."""
        lexer = Lexer("X 77-> Y 77-> Z")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, FunctionType)
        assert ast.arrow == "77->"
        # Right-associative: X 77-> (Y 77-> Z)
        assert isinstance(ast.range, FunctionType)
        assert ast.range.arrow == "77->"


class TestFiniteFunctionLaTeX:
    """Tests for finite function LaTeX generation."""

    def test_finite_function_latex_generation(self) -> None:
        """Test generating LaTeX for 77-> operator."""
        gen = LaTeXGenerator()
        ast = FunctionType(
            arrow="77->",
            domain=Identifier(name="X", line=1, column=1),
            range=Identifier(name="Y", line=1, column=9),
            line=1,
            column=3,
        )
        latex = gen.generate_expr(ast)
        assert r"\ffun" in latex
        assert "X" in latex
        assert "Y" in latex

    def test_finite_function_in_document(self) -> None:
        """Test finite function in complete document."""
        text = "X 77-> Y"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, FunctionType)
        gen = LaTeXGenerator()
        doc = gen.generate_document(ast)
        assert r"\ffun" in doc
        assert r"\documentclass" in doc
        assert r"\end{document}" in doc


class TestFiniteFunctionIntegration:
    """End-to-end integration tests for finite functions."""

    def test_finite_function_pipeline(self) -> None:
        """Test complete pipeline for 77-> operator."""
        text = "X 77-> Y"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, FunctionType)
        assert ast.arrow == "77->"
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)
        assert r"X \ffun Y" in latex

    def test_finite_function_vs_partial_function(self) -> None:
        """Test that 77-> and +-> are distinct operators."""
        text_ffun = "X 77-> Y"
        text_pfun = "X +-> Y"

        lexer_ffun = Lexer(text_ffun)
        tokens_ffun = lexer_ffun.tokenize()
        assert tokens_ffun[1].type == TokenType.FINFUN

        lexer_pfun = Lexer(text_pfun)
        tokens_pfun = lexer_pfun.tokenize()
        assert tokens_pfun[1].type == TokenType.PFUN

        parser_ffun = Parser(tokens_ffun)
        ast_ffun = parser_ffun.parse()
        assert isinstance(ast_ffun, FunctionType)
        assert ast_ffun.arrow == "77->"

        parser_pfun = Parser(tokens_pfun)
        ast_pfun = parser_pfun.parse()
        assert isinstance(ast_pfun, FunctionType)
        assert ast_pfun.arrow == "+->"

        gen = LaTeXGenerator()
        latex_ffun = gen.generate_expr(ast_ffun)
        latex_pfun = gen.generate_expr(ast_pfun)
        assert r"\ffun" in latex_ffun
        assert r"\pfun" in latex_pfun
        assert r"\ffun" not in latex_pfun
        assert r"\pfun" not in latex_ffun

    def test_finite_function_nested_right(self) -> None:
        """Test right-associativity of finite functions."""
        text = "X 77-> Y 77-> Z"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        # Should parse as X 77-> (Y 77-> Z)
        assert isinstance(ast, FunctionType)
        assert ast.arrow == "77->"
        assert isinstance(ast.domain, Identifier)
        assert ast.domain.name == "X"
        assert isinstance(ast.range, FunctionType)
        assert ast.range.arrow == "77->"
        assert isinstance(ast.range.domain, Identifier)
        assert ast.range.domain.name == "Y"
        assert isinstance(ast.range.range, Identifier)
        assert ast.range.range.name == "Z"

    def test_finite_function_real_usage(self) -> None:
        """Test realistic usage from Solutions 36, 40, 41."""
        text = "records : Year 77-> Table"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        # Should tokenize: records, :, Year, 77->, Table
        assert any(t.type == TokenType.FINFUN for t in tokens)
