"""Tests for Phase 35: Bag Union Operator (⊎ / bag_union)."""

from __future__ import annotations

from txt2tex.ast_nodes import BinaryOp, Identifier
from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser
from txt2tex.tokens import TokenType


class TestBagUnionLexer:
    """Tests for bag union lexer features."""

    def test_bag_union_operator_unicode(self) -> None:
        """Test lexing ⊎ operator (Unicode)."""
        lexer = Lexer("b1 ⊎ b2")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.IDENTIFIER
        assert tokens[0].value == "b1"
        assert tokens[1].type == TokenType.BAG_UNION
        assert tokens[1].value == "⊎"
        assert tokens[2].type == TokenType.IDENTIFIER
        assert tokens[2].value == "b2"

    def test_bag_union_operator_ascii(self) -> None:
        """Test lexing bag_union operator (ASCII keyword)."""
        lexer = Lexer("b1 bag_union b2")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.IDENTIFIER
        assert tokens[0].value == "b1"
        assert tokens[1].type == TokenType.BAG_UNION
        assert tokens[1].value == "bag_union"
        assert tokens[2].type == TokenType.IDENTIFIER
        assert tokens[2].value == "b2"


class TestBagUnionParser:
    """Tests for bag union parser features."""

    def test_parse_simple_bag_union_unicode(self) -> None:
        """Test parsing b1 ⊎ b2 (Unicode)."""
        lexer = Lexer("b1 ⊎ b2")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "⊎"
        assert isinstance(ast.left, Identifier)
        assert ast.left.name == "b1"
        assert isinstance(ast.right, Identifier)
        assert ast.right.name == "b2"

    def test_parse_simple_bag_union_ascii(self) -> None:
        """Test parsing b1 bag_union b2 (ASCII keyword)."""
        lexer = Lexer("b1 bag_union b2")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "bag_union"
        assert isinstance(ast.left, Identifier)
        assert ast.left.name == "b1"
        assert isinstance(ast.right, Identifier)
        assert ast.right.name == "b2"


class TestBagUnionLaTeX:
    """Tests for bag union LaTeX generation."""

    def test_bag_union_latex_generation_unicode(self) -> None:
        """Test generating LaTeX for ⊎ operator (Unicode)."""
        gen = LaTeXGenerator()
        ast = BinaryOp(
            operator="⊎",
            left=Identifier(name="b1", line=1, column=1),
            right=Identifier(name="b2", line=1, column=6),
            line=1,
            column=4,
        )
        latex = gen.generate_expr(ast)
        assert r"\uplus" in latex
        assert "b1" in latex
        assert "b2" in latex

    def test_bag_union_latex_generation_ascii(self) -> None:
        """Test generating LaTeX for bag_union operator (ASCII keyword)."""
        gen = LaTeXGenerator()
        ast = BinaryOp(
            operator="bag_union",
            left=Identifier(name="b1", line=1, column=1),
            right=Identifier(name="b2", line=1, column=12),
            line=1,
            column=4,
        )
        latex = gen.generate_expr(ast)
        assert r"\uplus" in latex
        assert "b1" in latex
        assert "b2" in latex

    def test_bag_union_in_document_unicode(self) -> None:
        """Test bag union in complete document (Unicode)."""
        text = "b1 ⊎ b2"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, BinaryOp)
        gen = LaTeXGenerator()
        doc = gen.generate_document(ast)
        assert r"\uplus" in doc
        assert r"\documentclass" in doc
        assert r"\end{document}" in doc

    def test_bag_union_in_document_ascii(self) -> None:
        """Test bag union in complete document (ASCII keyword)."""
        text = "b1 bag_union b2"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, BinaryOp)
        gen = LaTeXGenerator()
        doc = gen.generate_document(ast)
        assert r"\uplus" in doc
        assert r"\documentclass" in doc
        assert r"\end{document}" in doc


class TestBagUnionIntegration:
    """End-to-end integration tests for bag union."""

    def test_bag_union_pipeline_unicode(self) -> None:
        """Test complete pipeline for ⊎ operator (Unicode)."""
        text = "b1 ⊎ b2"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "⊎"
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)
        assert r"b1 \uplus b2" in latex

    def test_bag_union_pipeline_ascii(self) -> None:
        """Test complete pipeline for bag_union operator (ASCII keyword)."""
        text = "b1 bag_union b2"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "bag_union"
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)
        assert r"b1 \uplus b2" in latex

    def test_bag_union_left_associative(self) -> None:
        """Test left-associativity of bag union operator."""
        text = "b1 bag_union b2 bag_union b3"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        # Should parse as (b1 bag_union b2) bag_union b3 (left-associative)
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "bag_union"
        assert isinstance(ast.left, BinaryOp)
        assert ast.left.operator == "bag_union"
        assert isinstance(ast.left.left, Identifier)
        assert ast.left.left.name == "b1"
        assert isinstance(ast.left.right, Identifier)
        assert ast.left.right.name == "b2"
        assert isinstance(ast.right, Identifier)
        assert ast.right.name == "b3"
