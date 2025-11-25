"""Tests for \\bsup...\\esup superscript generation (Phase: exponentiation support)."""

from __future__ import annotations

from typing import cast

from txt2tex.ast_nodes import Expr, Identifier, Number, Superscript
from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser


class TestBsupEsupGeneration:
    """Test that exponentiation generates \\bsup...\\esup for fuzz compatibility."""

    def test_simple_numeric_exponent(self) -> None:
        """Test x^2 generates x \\bsup 2 \\esup."""
        node = Superscript(
            base=Identifier(line=1, column=1, name="x"),
            exponent=Number(line=1, column=3, value="2"),
            line=1,
            column=1,
        )
        gen = LaTeXGenerator(use_fuzz=True)
        result = gen._generate_superscript(node, parent=None)
        assert result == r"x \bsup 2 \esup"

    def test_simple_variable_exponent(self) -> None:
        """Test 2^n generates 2 \\bsup n \\esup."""
        node = Superscript(
            base=Number(line=1, column=1, value="2"),
            exponent=Identifier(line=1, column=3, name="n"),
            line=1,
            column=1,
        )
        gen = LaTeXGenerator(use_fuzz=True)
        result = gen._generate_superscript(node, parent=None)
        assert result == r"2 \bsup n \esup"

    def test_relation_iteration(self) -> None:
        """Test R^n generates R \\bsup n \\esup (relation iteration)."""
        node = Superscript(
            base=Identifier(line=1, column=1, name="R"),
            exponent=Identifier(line=1, column=3, name="n"),
            line=1,
            column=1,
        )
        gen = LaTeXGenerator(use_fuzz=True)
        result = gen._generate_superscript(node, parent=None)
        assert result == r"R \bsup n \esup"

    def test_zed_mode_also_uses_bsup(self) -> None:
        """Test that zed mode (--zed flag) also uses \\bsup...\\esup."""
        node = Superscript(
            base=Identifier(line=1, column=1, name="R"),
            exponent=Identifier(line=1, column=3, name="n"),
            line=1,
            column=1,
        )
        gen = LaTeXGenerator(use_fuzz=False)  # zed mode
        result = gen._generate_superscript(node, parent=None)
        assert result == r"R \bsup n \esup"


class TestBsupEsupIntegration:
    """Integration tests for exponentiation through full pipeline."""

    def test_simple_exponent_full_pipeline(self) -> None:
        """Test x^2 through lexer, parser, and generator."""
        text = "x^2"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator(use_fuzz=True)
        result = gen.generate_expr(cast("Expr", ast))
        assert result == r"x \bsup 2 \esup"

    def test_power_of_ten(self) -> None:
        """Test 10^6 through full pipeline."""
        text = "10^6"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator(use_fuzz=True)
        result = gen.generate_expr(cast("Expr", ast))
        assert result == r"10 \bsup 6 \esup"

    def test_complex_exponent(self) -> None:
        """Test R^(n+1) generates R \\bsup (n + 1) \\esup."""
        text = "R^(n+1)"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator(use_fuzz=True)
        result = gen.generate_expr(cast("Expr", ast))
        assert result == r"R \bsup (n + 1) \esup"

    def test_nested_exponentiation(self) -> None:
        """Test (x^2)^3 generates nested \\bsup."""
        text = "(x^2)^3"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator(use_fuzz=True)
        result = gen.generate_expr(cast("Expr", ast))
        # Should generate: (x \bsup 2 \esup) \bsup 3 \esup
        assert r"\bsup" in result
        assert r"\esup" in result
        assert result.count(r"\bsup") == 2  # Two levels of exponentiation

    def test_exponent_with_closure_operator(self) -> None:
        """Test R+^n (transitive closure then iteration)."""
        text = "R+^n"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator(use_fuzz=True)
        result = gen.generate_expr(cast("Expr", ast))
        # R+ becomes R^{+}, then ^n adds \bsup n \esup
        assert r"\bsup" in result
        assert r"\esup" in result
