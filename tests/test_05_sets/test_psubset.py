"""Tests for strict subset operator (psubset)."""

from __future__ import annotations

from txt2tex.ast_nodes import BinaryOp, Identifier
from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser
from txt2tex.tokens import TokenType


class TestPSubsetLexer:
    """Tests for psubset lexer features."""

    def test_psubset_operator(self) -> None:
        """Test lexing psubset operator (ASCII keyword)."""
        lexer = Lexer("A psubset B")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.IDENTIFIER
        assert tokens[0].value == "A"
        assert tokens[1].type == TokenType.PSUBSET
        assert tokens[1].value == "psubset"
        assert tokens[2].type == TokenType.IDENTIFIER
        assert tokens[2].value == "B"


class TestPSubsetParser:
    """Tests for psubset parser features."""

    def test_parse_simple_psubset(self) -> None:
        """Test parsing A psubset B."""
        lexer = Lexer("A psubset B")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "psubset"
        assert isinstance(ast.left, Identifier)
        assert ast.left.name == "A"
        assert isinstance(ast.right, Identifier)
        assert ast.right.name == "B"

    def test_psubset_vs_subset(self) -> None:
        """Test that psubset land subset are distinct operators."""
        lexer_psubset = Lexer("A psubset B")
        tokens_psubset = lexer_psubset.tokenize()
        parser_psubset = Parser(tokens_psubset)
        ast_psubset = parser_psubset.parse()
        lexer_subset = Lexer("A subset B")
        tokens_subset = lexer_subset.tokenize()
        parser_subset = Parser(tokens_subset)
        ast_subset = parser_subset.parse()
        assert isinstance(ast_psubset, BinaryOp)
        assert isinstance(ast_subset, BinaryOp)
        assert ast_psubset.operator == "psubset"
        assert ast_subset.operator == "subset"


class TestPSubsetLaTeX:
    """Tests for psubset LaTeX generation."""

    def test_psubset_latex_generation(self) -> None:
        """Test generating LaTeX for psubset operator."""
        gen = LaTeXGenerator()
        ast = BinaryOp(
            operator="psubset",
            left=Identifier(name="A", line=1, column=1),
            right=Identifier(name="B", line=1, column=10),
            line=1,
            column=3,
        )
        latex = gen.generate_expr(ast)
        assert "\\subset" in latex
        assert "A" in latex
        assert "B" in latex

    def test_psubset_vs_subset_latex(self) -> None:
        """Test that psubset land subset generate different LaTeX."""
        gen = LaTeXGenerator()
        ast_psubset = BinaryOp(
            operator="psubset",
            left=Identifier(name="A", line=1, column=1),
            right=Identifier(name="B", line=1, column=10),
            line=1,
            column=3,
        )
        latex_psubset = gen.generate_expr(ast_psubset)
        ast_subset = BinaryOp(
            operator="subset",
            left=Identifier(name="A", line=1, column=1),
            right=Identifier(name="B", line=1, column=9),
            line=1,
            column=3,
        )
        latex_subset = gen.generate_expr(ast_subset)
        assert "\\subset" in latex_psubset
        assert "\\subseteq" not in latex_psubset
        assert "\\subseteq" in latex_subset
        assert latex_subset == "A \\subseteq B"

    def test_psubset_in_document(self) -> None:
        """Test psubset elem complete document."""
        text = "A psubset B"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, BinaryOp)
        gen = LaTeXGenerator()
        doc = gen.generate_document(ast)
        assert "\\subset" in doc
        assert "\\documentclass" in doc
        assert "\\end{document}" in doc


class TestPSubsetIntegration:
    """End-to-end integration tests for psubset."""

    def test_psubset_pipeline(self) -> None:
        """Test complete pipeline for psubset operator."""
        text = "A psubset B"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "psubset"
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)
        assert "A \\subset B" in latex

    def test_psubset_precedence(self) -> None:
        """Test psubset has correct precedence with other set operators."""
        text = "A psubset B union C"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "psubset"
        assert isinstance(ast.right, BinaryOp)
        assert ast.right.operator == "union"
