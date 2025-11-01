"""Tests for Phase 33: Partial Bijection Operator (>7->)."""

from __future__ import annotations

from txt2tex.ast_nodes import FunctionType, Identifier
from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser
from txt2tex.tokens import TokenType


class TestPartialBijectionLexer:
    """Tests for partial bijection lexer features."""

    def test_partial_bijection_operator(self) -> None:
        """Test lexing >7-> operator."""
        lexer = Lexer("X >7-> Y")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.IDENTIFIER
        assert tokens[0].value == "X"
        assert tokens[1].type == TokenType.PBIJECTION
        assert tokens[1].value == ">7->"
        assert tokens[2].type == TokenType.IDENTIFIER
        assert tokens[2].value == "Y"


class TestPartialBijectionParser:
    """Tests for partial bijection parser features."""

    def test_parse_simple_partial_bijection(self) -> None:
        """Test parsing X >7-> Y."""
        lexer = Lexer("X >7-> Y")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, FunctionType)
        assert ast.arrow == ">7->"
        assert isinstance(ast.domain, Identifier)
        assert ast.domain.name == "X"
        assert isinstance(ast.range, Identifier)
        assert ast.range.name == "Y"

    def test_parse_nested_partial_bijection(self) -> None:
        """Test parsing X >7-> (Y >7-> Z)."""
        lexer = Lexer("X >7-> Y >7-> Z")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, FunctionType)
        assert ast.arrow == ">7->"
        # Right-associative: X >7-> (Y >7-> Z)
        assert isinstance(ast.range, FunctionType)
        assert ast.range.arrow == ">7->"


class TestPartialBijectionLaTeX:
    """Tests for partial bijection LaTeX generation."""

    def test_partial_bijection_latex_generation(self) -> None:
        """Test generating LaTeX for >7-> operator."""
        gen = LaTeXGenerator()
        ast = FunctionType(
            arrow=">7->",
            domain=Identifier(name="X", line=1, column=1),
            range=Identifier(name="Y", line=1, column=8),
            line=1,
            column=3,
        )
        latex = gen.generate_expr(ast)
        assert r"\pbij" in latex
        assert "X" in latex
        assert "Y" in latex

    def test_partial_bijection_in_document(self) -> None:
        """Test partial bijection in complete document."""
        text = "X >7-> Y"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, FunctionType)
        gen = LaTeXGenerator()
        doc = gen.generate_document(ast)
        assert r"\pbij" in doc
        assert r"\documentclass" in doc
        assert r"\end{document}" in doc


class TestPartialBijectionIntegration:
    """End-to-end integration tests for partial bijections."""

    def test_partial_bijection_pipeline(self) -> None:
        """Test complete pipeline for >7-> operator."""
        text = "X >7-> Y"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, FunctionType)
        assert ast.arrow == ">7->"
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)
        assert r"X \pbij Y" in latex

    def test_partial_bijection_vs_bijection(self) -> None:
        """Test that >7-> and >->> are distinct operators."""
        text_pbij = "X >7-> Y"
        text_bij = "X >->> Y"

        lexer_pbij = Lexer(text_pbij)
        tokens_pbij = lexer_pbij.tokenize()
        assert tokens_pbij[1].type == TokenType.PBIJECTION

        lexer_bij = Lexer(text_bij)
        tokens_bij = lexer_bij.tokenize()
        assert tokens_bij[1].type == TokenType.BIJECTION

        parser_pbij = Parser(tokens_pbij)
        ast_pbij = parser_pbij.parse()
        assert isinstance(ast_pbij, FunctionType)
        assert ast_pbij.arrow == ">7->"

        parser_bij = Parser(tokens_bij)
        ast_bij = parser_bij.parse()
        assert isinstance(ast_bij, FunctionType)
        assert ast_bij.arrow == ">->>"

        gen = LaTeXGenerator()
        latex_pbij = gen.generate_expr(ast_pbij)
        latex_bij = gen.generate_expr(ast_bij)
        assert r"\pbij" in latex_pbij
        assert r"\bij" in latex_bij
        assert r"\pbij" not in latex_bij
        assert r"\bij" not in latex_pbij

    def test_partial_bijection_nested_right(self) -> None:
        """Test right-associativity of partial bijections."""
        text = "X >7-> Y >7-> Z"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        # Should parse as X >7-> (Y >7-> Z)
        assert isinstance(ast, FunctionType)
        assert ast.arrow == ">7->"
        assert isinstance(ast.domain, Identifier)
        assert ast.domain.name == "X"
        assert isinstance(ast.range, FunctionType)
        assert ast.range.arrow == ">7->"
        assert isinstance(ast.range.domain, Identifier)
        assert ast.range.domain.name == "Y"
        assert isinstance(ast.range.range, Identifier)
        assert ast.range.range.name == "Z"
