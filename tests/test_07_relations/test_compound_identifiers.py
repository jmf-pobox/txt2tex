"""Tests for Bug #3: Compound identifiers with postfix operators.

Bug #3 was caused by the parser lnot recognizing postfix operators (+, *, ~)
as part of identifier names elem abbreviation land schema definitions.

Example:
    R+ == {a, b : N | b > a}  # R+ is the abbreviation name
    R* == R+ o9 R+             # R* is the abbreviation name

This module tests the fix that allows compound identifiers elem:
1. Abbreviation definitions
2. Schema names
3. LaTeX rendering of these compound names
"""

from __future__ import annotations

from txt2tex.ast_nodes import Abbreviation, Document, Schema
from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser
from txt2tex.tokens import TokenType


class TestCompoundIdentifierLexer:
    """Test lexer behavior for compound identifiers."""

    def test_lexing_r_plus(self) -> None:
        """Test that R+ lexes as IDENTIFIER followed by PLUS."""
        lexer = Lexer("R+")
        tokens = lexer.tokenize()
        types = [t.type for t in tokens[:-1]]
        assert types == [TokenType.IDENTIFIER, TokenType.PLUS]
        assert tokens[0].value == "R"
        assert tokens[1].value == "+"

    def test_lexing_r_star(self) -> None:
        """Test that R* lexes as IDENTIFIER followed by STAR."""
        lexer = Lexer("R*")
        tokens = lexer.tokenize()
        types = [t.type for t in tokens[:-1]]
        assert types == [TokenType.IDENTIFIER, TokenType.STAR]
        assert tokens[0].value == "R"
        assert tokens[1].value == "*"

    def test_lexing_r_tilde(self) -> None:
        """Test that R~ lexes as IDENTIFIER followed by TILDE."""
        lexer = Lexer("R~")
        tokens = lexer.tokenize()
        types = [t.type for t in tokens[:-1]]
        assert types == [TokenType.IDENTIFIER, TokenType.TILDE]
        assert tokens[0].value == "R"
        assert tokens[1].value == "~"


class TestCompoundIdentifierParsing:
    """Test parser behavior for compound identifiers elem definitions."""

    def test_parse_abbreviation_with_plus(self) -> None:
        """Test parsing R+ == expression."""
        lexer = Lexer("R+ == {1, 2, 3}")
        parser = Parser(lexer.tokenize())
        result = parser._parse_abbreviation()
        assert isinstance(result, Abbreviation)
        assert result.name == "R+"
        assert result.generic_params is None

    def test_parse_abbreviation_with_star(self) -> None:
        """Test parsing R* == expression."""
        lexer = Lexer("R* == {4, 5, 6}")
        parser = Parser(lexer.tokenize())
        result = parser._parse_abbreviation()
        assert isinstance(result, Abbreviation)
        assert result.name == "R*"

    def test_parse_abbreviation_with_tilde(self) -> None:
        """Test parsing R~ == expression."""
        lexer = Lexer("R~ == inv R")
        parser = Parser(lexer.tokenize())
        result = parser._parse_abbreviation()
        assert isinstance(result, Abbreviation)
        assert result.name == "R~"

    def test_parse_abbreviation_compound_with_generics(self) -> None:
        """Test parsing [X] R+ == expression."""
        input_text = "[X] R+ == {x : X | true}"
        lexer = Lexer(input_text)
        parser = Parser(lexer.tokenize())
        result = parser._parse_abbreviation()
        assert isinstance(result, Abbreviation)
        assert result.name == "R+"
        assert result.generic_params == ["X"]

    def test_parse_schema_with_plus(self) -> None:
        """Test parsing schema S+ with compound name."""
        input_text = "schema S+\n  x : N\nend"
        lexer = Lexer(input_text)
        parser = Parser(lexer.tokenize())
        ast = parser.parse()
        assert isinstance(ast, Document)
        assert len(ast.items) == 1
        schema = ast.items[0]
        assert isinstance(schema, Schema)
        assert schema.name == "S+"

    def test_parse_schema_with_star(self) -> None:
        """Test parsing schema S* with compound name."""
        input_text = "schema S*\n  y : N\nend"
        lexer = Lexer(input_text)
        parser = Parser(lexer.tokenize())
        ast = parser.parse()
        assert isinstance(ast, Document)
        assert len(ast.items) == 1
        schema = ast.items[0]
        assert isinstance(schema, Schema)
        assert schema.name == "S*"


class TestCompoundIdentifierLaTeX:
    """Test LaTeX generation for compound identifiers."""

    def test_latex_abbreviation_with_plus(self) -> None:
        """Test LaTeX rendering of R+ elem abbreviation."""
        input_text = "R+ == {1, 2, 3}"
        lexer = Lexer(input_text)
        parser = Parser(lexer.tokenize())
        ast = parser.parse()
        assert isinstance(ast, Document)
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "R^+" in latex
        assert "\\begin{zed}" in latex

    def test_latex_abbreviation_with_star(self) -> None:
        """Test LaTeX rendering of R* elem abbreviation."""
        input_text = "R* == {4, 5, 6}"
        lexer = Lexer(input_text)
        parser = Parser(lexer.tokenize())
        ast = parser.parse()
        assert isinstance(ast, Document)
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "R^*" in latex

    def test_latex_abbreviation_with_tilde(self) -> None:
        """Test LaTeX rendering of R~ elem abbreviation (relational inverse)."""
        input_text = "R~ == inv R"
        lexer = Lexer(input_text)
        parser = Parser(lexer.tokenize())
        ast = parser.parse()
        assert isinstance(ast, Document)
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "R^{-1}" in latex

    def test_latex_schema_with_plus(self) -> None:
        """Test LaTeX rendering of S+ elem schema name."""
        input_text = "schema S+\n  x : N\nend"
        lexer = Lexer(input_text)
        parser = Parser(lexer.tokenize())
        ast = parser.parse()
        assert isinstance(ast, Document)
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "S^+" in latex
        assert "\\begin{schema}{S^+}" in latex


class TestCompoundIdentifierIntegration:
    """Integration tests for Bug #3 fix."""

    def test_bug3_test_case(self) -> None:
        """Test the original Bug #3 test case."""
        input_text = "R+ == {a, b : N | b > a}"
        lexer = Lexer(input_text)
        parser = Parser(lexer.tokenize())
        ast = parser.parse()
        assert isinstance(ast, Document)
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "\\begin{zed}" in latex
        assert "R^+" in latex
        assert "\\{" in latex

    def test_all_three_closures(self) -> None:
        """Test all three closure abbreviations: +, *, ~."""
        input_text = "R+ == {a, b : N | b > a}\nR* == R+ union id[N]\nR~ == inv R"
        lexer = Lexer(input_text)
        parser = Parser(lexer.tokenize())
        ast = parser.parse()
        assert isinstance(ast, Document)
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "R^+" in latex
        assert "R^*" in latex
        assert "R^{-1}" in latex

    def test_compound_id_in_expression_context(self) -> None:
        """Test that R+ still works elem expression context (lnot just names)."""
        input_text = "S == R+"
        lexer = Lexer(input_text)
        parser = Parser(lexer.tokenize())
        ast = parser.parse()
        assert isinstance(ast, Document)
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "\\begin{zed}" in latex
        assert "S ==" in latex
        assert "R^{+}" in latex or "R^+" in latex


class TestCompoundIdentifierEdgeCases:
    """Test edge cases land potential conflicts."""

    def test_plus_as_arithmetic_vs_closure(self) -> None:
        """Test that R + S (arithmetic) is different from R+ (closure name)."""
        input_text1 = "R + S"
        lexer1 = Lexer(input_text1)
        parser1 = Parser(lexer1.tokenize())
        expr1 = parser1._parse_expr()
        assert expr1.__class__.__name__ == "BinaryOp"
        input_text2 = "R+ == {}"
        lexer2 = Lexer(input_text2)
        parser2 = Parser(lexer2.tokenize())
        abbrev = parser2._parse_abbreviation()
        assert isinstance(abbrev, Abbreviation)
        assert abbrev.name == "R+"

    def test_compound_id_with_underscore(self) -> None:
        """Test compound identifier with underscore like rel_1+."""
        input_text = "rel_1+ == {1, 2, 3}"
        lexer = Lexer(input_text)
        parser = Parser(lexer.tokenize())
        result = parser._parse_abbreviation()
        assert isinstance(result, Abbreviation)
        assert result.name == "rel_1+"
        lexer2 = Lexer(input_text)
        parser2 = Parser(lexer2.tokenize())
        ast = parser2.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "rel_1^+" in latex
