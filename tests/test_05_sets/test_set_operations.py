"""Tests for set operations (equality, mu operator, membership)."""

from __future__ import annotations

from txt2tex.ast_nodes import BinaryOp, Identifier, Number, Quantifier
from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser


class TestLexer:
    """Tests for set operation lexer features."""

    def test_mu_keyword(self) -> None:
        """Test lexing mu keyword."""
        lexer = Lexer("mu x : N | x > 0")
        tokens = lexer.tokenize()
        assert tokens[0].type.name == "MU"
        assert tokens[0].value == "mu"

    def test_not_equal(self) -> None:
        """Test lexing != operator."""
        lexer = Lexer("x != y")
        tokens = lexer.tokenize()
        assert tokens[0].type.name == "IDENTIFIER"
        assert tokens[1].type.name == "NOT_EQUAL"
        assert tokens[1].value == "!="

    def test_notin_keyword(self) -> None:
        """Test lexing notin keyword."""
        lexer = Lexer("x notin S")
        tokens = lexer.tokenize()
        assert tokens[0].type.name == "IDENTIFIER"
        assert tokens[1].type.name == "NOTIN"
        assert tokens[1].value == "notin"

    def test_in_keyword(self) -> None:
        """Test that 'elem' is recognized as set membership."""
        lexer = Lexer("x elem S")
        tokens = lexer.tokenize()
        assert tokens[0].type.name == "IDENTIFIER"
        assert tokens[1].type.name == "IN"
        assert tokens[1].value == "elem"


class TestParser:
    """Tests for set operation parser features."""

    def test_mu_operator(self) -> None:
        """Test parsing mu operator (definite description)."""
        lexer = Lexer("mu x : N | x > 0")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Quantifier)
        assert ast.quantifier == "mu"
        assert ast.variables == ["x"]
        assert isinstance(ast.domain, Identifier)
        assert ast.domain.name == "N"
        assert isinstance(ast.body, BinaryOp)
        assert ast.body.operator == ">"

    def test_mu_without_domain(self) -> None:
        """Test parsing mu without explicit domain."""
        lexer = Lexer("mu x | x > 0")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Quantifier)
        assert ast.quantifier == "mu"
        assert ast.variables == ["x"]
        assert ast.domain is None

    def test_not_equal_comparison(self) -> None:
        """Test parsing != (not equal) comparison."""
        lexer = Lexer("x != 0")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "!="
        assert isinstance(ast.left, Identifier)
        assert ast.left.name == "x"
        assert isinstance(ast.right, Number)
        assert ast.right.value == "0"

    def test_notin_membership(self) -> None:
        """Test parsing notin (not in) membership."""
        lexer = Lexer("x notin S")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "notin"
        assert isinstance(ast.left, Identifier)
        assert ast.left.name == "x"
        assert isinstance(ast.right, Identifier)
        assert ast.right.name == "S"

    def test_in_membership(self) -> None:
        """Test that 'elem' works correctly for set membership."""
        lexer = Lexer("x elem S")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "elem"

    def test_complex_mu_expression(self) -> None:
        """Test parsing mu with complex body."""
        lexer = Lexer("mu x : N | x^2 = 4 land x > 0")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Quantifier)
        assert ast.quantifier == "mu"
        assert isinstance(ast.body, BinaryOp)
        assert ast.body.operator == "land"

    def test_inequality_chain(self) -> None:
        """Test parsing expression with != elem compound statement."""
        lexer = Lexer("x != y land y != z")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "land"
        assert isinstance(ast.left, BinaryOp)
        assert ast.left.operator == "!="
        assert isinstance(ast.right, BinaryOp)
        assert ast.right.operator == "!="


class TestLaTeXGenerator:
    """Tests for set operation LaTeX generation."""

    def test_mu_operator_generation(self) -> None:
        """Test generating LaTeX for mu operator."""
        gen = LaTeXGenerator()
        ast = Quantifier(
            quantifier="mu",
            variables=["x"],
            domain=Identifier(name="N", line=1, column=6),
            body=BinaryOp(
                operator=">",
                left=Identifier(name="x", line=1, column=12),
                right=Number(value="0", line=1, column=16),
                line=1,
                column=14,
            ),
            line=1,
            column=1,
        )
        latex = gen.generate_expr(ast)
        assert "\\mu" in latex
        assert "\\colon" in latex
        assert "\\bullet" in latex
        assert "N" in latex
        assert "x > 0" in latex

    def test_not_equal_generation(self) -> None:
        """Test generating LaTeX for != operator."""
        gen = LaTeXGenerator()
        ast = BinaryOp(
            operator="!=",
            left=Identifier(name="x", line=1, column=1),
            right=Number(value="0", line=1, column=6),
            line=1,
            column=3,
        )
        latex = gen.generate_expr(ast)
        assert "\\neq" in latex
        assert "x" in latex
        assert "0" in latex

    def test_notin_generation(self) -> None:
        """Test generating LaTeX for notin operator."""
        gen = LaTeXGenerator()
        ast = BinaryOp(
            operator="notin",
            left=Identifier(name="x", line=1, column=1),
            right=Identifier(name="S", line=1, column=8),
            line=1,
            column=3,
        )
        latex = gen.generate_expr(ast)
        assert "\\notin" in latex
        assert "x" in latex
        assert "S" in latex

    def test_mu_without_domain_generation(self) -> None:
        """Test generating LaTeX for mu without explicit domain."""
        gen = LaTeXGenerator()
        ast = Quantifier(
            quantifier="mu",
            variables=["x"],
            domain=None,
            body=BinaryOp(
                operator=">",
                left=Identifier(name="x", line=1, column=8),
                right=Number(value="0", line=1, column=12),
                line=1,
                column=10,
            ),
            line=1,
            column=1,
        )
        latex = gen.generate_expr(ast)
        assert "\\mu" in latex
        assert "\\bullet" in latex
        assert "\\colon" not in latex


class TestIntegration:
    """End-to-end integration tests for set operations."""

    def test_mu_operator_pipeline(self) -> None:
        """Test complete pipeline for mu operator."""
        text = "mu x : N | x^2 = 4 land x > 0"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Quantifier)
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)
        assert "\\mu x \\colon \\mathbb{N} \\bullet" in latex
        assert "x \\bsup 2 \\esup = 4" in latex
        assert "\\land" in latex
        assert "x > 0" in latex

    def test_not_equal_pipeline(self) -> None:
        """Test complete pipeline for != operator."""
        text = "x != 0"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, BinaryOp)
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)
        assert "x \\neq 0" in latex

    def test_notin_pipeline(self) -> None:
        """Test complete pipeline for notin operator."""
        text = "x notin S"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, BinaryOp)
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)
        assert "x \\notin S" in latex

    def test_complex_equality_reasoning(self) -> None:
        """Test one-point rule style reasoning with equality."""
        text = "exists y : N | y = 0 land x != y"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Quantifier)
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)
        assert "\\exists y \\colon \\mathbb{N} \\bullet" in latex
        assert "y = 0" in latex
        assert "\\land" in latex
        assert "x \\neq y" in latex

    def test_document_with_set_features(self) -> None:
        """Test document generation with set operation features."""
        text = "mu x : N | x > 0"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Quantifier)
        gen = LaTeXGenerator()
        doc = gen.generate_document(ast)
        assert "\\documentclass[a4paper,10pt,fleqn]{article}" in doc
        assert "\\usepackage{zed-cm}" in doc
        assert "\\mu x \\colon \\mathbb{N} \\bullet x > 0" in doc
        assert "\\end{document}" in doc

    def test_membership_in_document(self) -> None:
        """Test membership operators elem complete document."""
        text = "x elem S land y notin T"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, BinaryOp)
        gen = LaTeXGenerator()
        doc = gen.generate_document(ast)
        assert "x \\in S" in doc
        assert "y \\notin T" in doc
