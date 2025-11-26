"""Tests for Phase 32: Distributed Intersection Operator (bigcap)."""

from __future__ import annotations

from txt2tex.ast_nodes import Identifier, UnaryOp
from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser
from txt2tex.tokens import TokenType


class TestBigcapLexer:
    """Tests for bigcap lexer features."""

    def test_bigcap_keyword(self) -> None:
        """Test lexing bigcap keyword."""
        lexer = Lexer("bigcap S")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.BIGCAP
        assert tokens[0].value == "bigcap"
        assert tokens[1].type == TokenType.IDENTIFIER
        assert tokens[1].value == "S"


class TestBigcapParser:
    """Tests for bigcap parser features."""

    def test_parse_bigcap_simple(self) -> None:
        """Test parsing bigcap S."""
        lexer = Lexer("bigcap S")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, UnaryOp)
        assert ast.operator == "bigcap"
        assert isinstance(ast.operand, Identifier)
        assert ast.operand.name == "S"

    def test_parse_bigcap_in_expression(self) -> None:
        """Test parsing bigcap elem compound expression."""
        lexer = Lexer("bigcap S elem T")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert ast.__class__.__name__ == "BinaryOp"


class TestBigcapLaTeX:
    """Tests for bigcap LaTeX generation."""

    def test_bigcap_latex_generation(self) -> None:
        """Test generating LaTeX for bigcap operator."""
        gen = LaTeXGenerator()
        ast = UnaryOp(
            operator="bigcap",
            operand=Identifier(name="S", line=1, column=8),
            line=1,
            column=1,
        )
        latex = gen.generate_expr(ast)
        assert "\\bigcap" in latex
        assert "S" in latex

    def test_bigcap_in_document(self) -> None:
        """Test bigcap elem complete document."""
        text = "bigcap S"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, UnaryOp)
        gen = LaTeXGenerator()
        doc = gen.generate_document(ast)
        assert "\\bigcap S" in doc
        assert "\\documentclass" in doc
        assert "\\end{document}" in doc


class TestBigcapIntegration:
    """End-to-end integration tests for bigcap."""

    def test_bigcap_pipeline(self) -> None:
        """Test complete pipeline for bigcap operator."""
        text = "bigcap S"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, UnaryOp)
        assert ast.operator == "bigcap"
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)
        assert "\\bigcap S" in latex

    def test_bigcap_with_complex_set(self) -> None:
        """Test bigcap with set comprehension."""
        text = "bigcap { S : P X | true }"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, UnaryOp)
        assert ast.operator == "bigcap"
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)
        assert "\\bigcap" in latex

    def test_bigcap_vs_bigcup(self) -> None:
        """Test that bigcap land bigcup are distinct operators."""
        text_cap = "bigcap S"
        text_cup = "bigcup S"
        lexer_cap = Lexer(text_cap)
        tokens_cap = lexer_cap.tokenize()
        assert tokens_cap[0].type == TokenType.BIGCAP
        lexer_cup = Lexer(text_cup)
        tokens_cup = lexer_cup.tokenize()
        assert tokens_cup[0].type == TokenType.BIGCUP
        parser_cap = Parser(tokens_cap)
        ast_cap = parser_cap.parse()
        assert isinstance(ast_cap, UnaryOp)
        assert ast_cap.operator == "bigcap"
        parser_cup = Parser(tokens_cup)
        ast_cup = parser_cup.parse()
        assert isinstance(ast_cup, UnaryOp)
        assert ast_cup.operator == "bigcup"
        gen = LaTeXGenerator()
        latex_cap = gen.generate_expr(ast_cap)
        latex_cup = gen.generate_expr(ast_cup)
        assert "\\bigcap" in latex_cap
        assert "\\bigcup" in latex_cup
        assert "\\bigcap" not in latex_cup
        assert "\\bigcup" not in latex_cap
