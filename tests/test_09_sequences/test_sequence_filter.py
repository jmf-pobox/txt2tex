"""Tests for sequence filter operator (↾)."""

from __future__ import annotations

from txt2tex.ast_nodes import BinaryOp, Identifier, SetLiteral
from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser
from txt2tex.tokens import TokenType


class TestSequenceFilterLexer:
    """Tests for sequence filter lexer features."""

    def test_filter_operator_unicode(self) -> None:
        """Test lexing ↾ operator (Unicode)."""
        lexer = Lexer("s ↾ A")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.IDENTIFIER
        assert tokens[0].value == "s"
        assert tokens[1].type == TokenType.FILTER
        assert tokens[1].value == "↾"
        assert tokens[2].type == TokenType.IDENTIFIER
        assert tokens[2].value == "A"

    def test_filter_operator_ascii(self) -> None:
        """Test lexing filter operator (ASCII keyword)."""
        lexer = Lexer("s filter A")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.IDENTIFIER
        assert tokens[0].value == "s"
        assert tokens[1].type == TokenType.FILTER
        assert tokens[1].value == "filter"
        assert tokens[2].type == TokenType.IDENTIFIER
        assert tokens[2].value == "A"


class TestSequenceFilterParser:
    """Tests for sequence filter parser features."""

    def test_parse_simple_filter(self) -> None:
        """Test parsing s ↾ A."""
        lexer = Lexer("s ↾ A")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "↾"
        assert isinstance(ast.left, Identifier)
        assert ast.left.name == "s"
        assert isinstance(ast.right, Identifier)
        assert ast.right.name == "A"

    def test_parse_filter_with_set_literal(self) -> None:
        """Test parsing s ↾ {1, 2, 3}."""
        lexer = Lexer("s ↾ {1, 2, 3}")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "↾"
        assert isinstance(ast.left, Identifier)
        assert isinstance(ast.right, SetLiteral)

    def test_parse_nested_filter(self) -> None:
        """Test parsing (s ↾ A) ↾ B - left-associative."""
        lexer = Lexer("s ↾ A ↾ B")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "↾"
        assert isinstance(ast.left, BinaryOp)
        assert ast.left.operator == "↾"

    def test_parse_simple_filter_ascii(self) -> None:
        """Test parsing s filter A (ASCII keyword)."""
        lexer = Lexer("s filter A")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "filter"
        assert isinstance(ast.left, Identifier)
        assert ast.left.name == "s"
        assert isinstance(ast.right, Identifier)
        assert ast.right.name == "A"

    def test_parse_filter_with_set_literal_ascii(self) -> None:
        """Test parsing s filter {1, 2, 3} (ASCII keyword)."""
        lexer = Lexer("s filter {1, 2, 3}")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "filter"
        assert isinstance(ast.left, Identifier)
        assert isinstance(ast.right, SetLiteral)


class TestSequenceFilterLaTeX:
    """Tests for sequence filter LaTeX generation."""

    def test_filter_latex_generation(self) -> None:
        """Test generating LaTeX for ↾ operator."""
        gen = LaTeXGenerator()
        ast = BinaryOp(
            operator="↾",
            left=Identifier(name="s", line=1, column=1),
            right=Identifier(name="A", line=1, column=5),
            line=1,
            column=3,
        )
        latex = gen.generate_expr(ast)
        assert "\\filter" in latex
        assert "s" in latex
        assert "A" in latex

    def test_filter_in_document(self) -> None:
        """Test filter elem complete document."""
        text = "s ↾ A"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, BinaryOp)
        gen = LaTeXGenerator()
        doc = gen.generate_document(ast)
        assert "\\filter" in doc
        assert "\\documentclass" in doc
        assert "\\end{document}" in doc

    def test_filter_latex_generation_ascii(self) -> None:
        """Test generating LaTeX for filter operator (ASCII keyword)."""
        gen = LaTeXGenerator()
        ast = BinaryOp(
            operator="filter",
            left=Identifier(name="s", line=1, column=1),
            right=Identifier(name="A", line=1, column=9),
            line=1,
            column=3,
        )
        latex = gen.generate_expr(ast)
        assert "\\filter" in latex
        assert "s" in latex
        assert "A" in latex

    def test_filter_in_document_ascii(self) -> None:
        """Test filter elem complete document (ASCII keyword)."""
        text = "s filter A"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, BinaryOp)
        gen = LaTeXGenerator()
        doc = gen.generate_document(ast)
        assert "\\filter" in doc
        assert "\\documentclass" in doc
        assert "\\end{document}" in doc


class TestSequenceFilterIntegration:
    """End-to-end integration tests for sequence filter."""

    def test_filter_pipeline(self) -> None:
        """Test complete pipeline for ↾ operator."""
        text = "s ↾ A"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "↾"
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)
        assert "s \\filter A" in latex

    def test_filter_vs_range_restriction(self) -> None:
        """Test that ↾ (filter) land |> (range restriction) are distinct."""
        text_filter = "s ↾ A"
        text_rres = "R |> S"
        lexer_filter = Lexer(text_filter)
        tokens_filter = lexer_filter.tokenize()
        assert tokens_filter[1].type == TokenType.FILTER
        lexer_rres = Lexer(text_rres)
        tokens_rres = lexer_rres.tokenize()
        assert tokens_rres[1].type == TokenType.RRES
        parser_filter = Parser(tokens_filter)
        ast_filter = parser_filter.parse()
        assert isinstance(ast_filter, BinaryOp)
        assert ast_filter.operator == "↾"
        parser_rres = Parser(tokens_rres)
        ast_rres = parser_rres.parse()
        assert isinstance(ast_rres, BinaryOp)
        assert ast_rres.operator == "|>"
        gen = LaTeXGenerator()
        latex_filter = gen.generate_expr(ast_filter)
        latex_rres = gen.generate_expr(ast_rres)
        assert "\\filter" in latex_filter
        assert "\\rres" in latex_rres
        assert "\\filter" not in latex_rres
        assert "\\rres" not in latex_filter

    def test_filter_real_usage(self) -> None:
        """Test realistic usage from Solutions 40, 41."""
        text = "s ↾ {t : Title | true}"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "↾"
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)
        assert "\\filter" in latex

    def test_filter_left_associative(self) -> None:
        """Test left-associativity of filter operator."""
        text = "s ↾ A ↾ B"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "↾"
        assert isinstance(ast.left, BinaryOp)
        assert ast.left.operator == "↾"
        assert isinstance(ast.left.left, Identifier)
        assert ast.left.left.name == "s"
        assert isinstance(ast.left.right, Identifier)
        assert ast.left.right.name == "A"
        assert isinstance(ast.right, Identifier)
        assert ast.right.name == "B"

    def test_filter_pipeline_ascii(self) -> None:
        """Test complete pipeline for filter operator (ASCII keyword)."""
        text = "s filter A"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "filter"
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)
        assert "s \\filter A" in latex

    def test_filter_real_usage_ascii(self) -> None:
        """Test realistic usage with ASCII keyword."""
        text = "s filter {t : Title | true}"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "filter"
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)
        assert "\\filter" in latex
