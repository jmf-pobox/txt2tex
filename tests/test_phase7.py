"""Tests for Phase 7: Equality and Special Operators."""

from __future__ import annotations

from txt2tex.ast_nodes import (
    BinaryOp,
    Identifier,
    Number,
    Quantifier,
)
from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser


class TestLexer:
    """Tests for Phase 7 lexer features."""

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
        """Test that 'in' is still recognized (not broken by notin)."""
        lexer = Lexer("x in S")
        tokens = lexer.tokenize()
        assert tokens[0].type.name == "IDENTIFIER"
        assert tokens[1].type.name == "IN"
        assert tokens[1].value == "in"


class TestParser:
    """Tests for Phase 7 parser features."""

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
        """Test that 'in' still works correctly."""
        lexer = Lexer("x in S")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "in"

    def test_complex_mu_expression(self) -> None:
        """Test parsing mu with complex body."""
        lexer = Lexer("mu x : N | x^2 = 4 and x > 0")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Quantifier)
        assert ast.quantifier == "mu"
        assert isinstance(ast.body, BinaryOp)
        assert ast.body.operator == "and"

    def test_inequality_chain(self) -> None:
        """Test parsing expression with != in compound statement."""
        lexer = Lexer("x != y and y != z")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "and"
        assert isinstance(ast.left, BinaryOp)
        assert ast.left.operator == "!="
        assert isinstance(ast.right, BinaryOp)
        assert ast.right.operator == "!="


class TestLaTeXGenerator:
    """Tests for Phase 7 LaTeX generator."""

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
        assert r"\mu" in latex
        assert r"\colon" in latex
        assert r"\bullet" in latex
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
        assert r"\neq" in latex
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
        assert r"\notin" in latex
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
        assert r"\mu" in latex
        assert r"\bullet" in latex
        assert r"\colon" not in latex  # No domain specified


class TestIntegration:
    """End-to-end integration tests for Phase 7."""

    def test_mu_operator_pipeline(self) -> None:
        """Test complete pipeline for mu operator."""
        text = "mu x : N | x^2 = 4 and x > 0"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Quantifier)
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)
        assert r"\mu x \colon N \bullet" in latex
        assert r"x^2 = 4" in latex
        assert r"\land" in latex
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
        assert r"x \neq 0" in latex

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
        assert r"x \notin S" in latex

    def test_complex_equality_reasoning(self) -> None:
        """Test one-point rule style reasoning with equality."""
        text = "exists y : N | y = 0 and x != y"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Quantifier)
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)
        assert r"\exists y \colon N \bullet" in latex
        assert "y = 0" in latex
        assert r"\land" in latex
        assert r"x \neq y" in latex

    def test_document_with_phase7_features(self) -> None:
        """Test document generation with Phase 7 features."""
        text = "mu x : N | x > 0"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Quantifier)
        gen = LaTeXGenerator()
        doc = gen.generate_document(ast)
        assert r"\documentclass[fleqn]{article}" in doc
        assert r"\usepackage{zed-cm}" in doc
        assert r"\mu x \colon N \bullet x > 0" in doc
        assert r"\end{document}" in doc

    def test_membership_in_document(self) -> None:
        """Test membership operators in complete document."""
        text = "x in S and y notin T"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, BinaryOp)
        gen = LaTeXGenerator()
        doc = gen.generate_document(ast)
        assert r"x \in S" in doc
        assert r"y \notin T" in doc
