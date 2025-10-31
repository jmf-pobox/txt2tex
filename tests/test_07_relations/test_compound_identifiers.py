"""Tests for Bug #3: Compound identifiers with postfix operators.

Bug #3 was caused by the parser not recognizing postfix operators (+, *, ~)
as part of identifier names in abbreviation and schema definitions.

Example:
    R+ == {a, b : N | b > a}  # R+ is the abbreviation name
    R* == R+ o9 R+             # R* is the abbreviation name

This module tests the fix that allows compound identifiers in:
1. Abbreviation definitions
2. Schema names
3. LaTeX rendering of these compound names
"""

from __future__ import annotations

from txt2tex.ast_nodes import Abbreviation, Document
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
        types = [t.type for t in tokens[:-1]]  # Exclude EOF
        assert types == [TokenType.IDENTIFIER, TokenType.PLUS]
        assert tokens[0].value == "R"
        assert tokens[1].value == "+"

    def test_lexing_r_star(self) -> None:
        """Test that R* lexes as IDENTIFIER followed by STAR."""
        lexer = Lexer("R*")
        tokens = lexer.tokenize()
        types = [t.type for t in tokens[:-1]]  # Exclude EOF
        assert types == [TokenType.IDENTIFIER, TokenType.STAR]
        assert tokens[0].value == "R"
        assert tokens[1].value == "*"

    def test_lexing_r_tilde(self) -> None:
        """Test that R~ lexes as IDENTIFIER followed by TILDE."""
        lexer = Lexer("R~")
        tokens = lexer.tokenize()
        types = [t.type for t in tokens[:-1]]  # Exclude EOF
        assert types == [TokenType.IDENTIFIER, TokenType.TILDE]
        assert tokens[0].value == "R"
        assert tokens[1].value == "~"


class TestCompoundIdentifierParsing:
    """Test parser behavior for compound identifiers in definitions."""

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
        input_text = """schema S+
  x : N
end"""
        lexer = Lexer(input_text)
        parser = Parser(lexer.tokenize())
        ast = parser.parse()
        assert isinstance(ast, Document)

        # Document.items contains all top-level items
        assert len(ast.items) == 1
        schema = ast.items[0]
        assert schema.__class__.__name__ == "Schema"
        assert schema.name == "S+"  # type: ignore[union-attr]

    def test_parse_schema_with_star(self) -> None:
        """Test parsing schema S* with compound name."""
        input_text = """schema S*
  y : N
end"""
        lexer = Lexer(input_text)
        parser = Parser(lexer.tokenize())
        ast = parser.parse()
        assert isinstance(ast, Document)

        # Document.items contains all top-level items
        assert len(ast.items) == 1
        schema = ast.items[0]
        assert schema.__class__.__name__ == "Schema"
        assert schema.name == "S*"  # type: ignore[union-attr]


class TestCompoundIdentifierLaTeX:
    """Test LaTeX generation for compound identifiers."""

    def test_latex_abbreviation_with_plus(self) -> None:
        """Test LaTeX rendering of R+ in abbreviation."""
        input_text = "R+ == {1, 2, 3}"
        lexer = Lexer(input_text)
        parser = Parser(lexer.tokenize())
        ast = parser.parse()
        assert isinstance(ast, Document)
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # Should render as R^+ in LaTeX
        assert "R^+" in latex
        # Should appear in zed environment
        assert r"\begin{zed}" in latex

    def test_latex_abbreviation_with_star(self) -> None:
        """Test LaTeX rendering of R* in abbreviation."""
        input_text = "R* == {4, 5, 6}"
        lexer = Lexer(input_text)
        parser = Parser(lexer.tokenize())
        ast = parser.parse()
        assert isinstance(ast, Document)
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # Should render as R^* in LaTeX
        assert "R^*" in latex

    def test_latex_abbreviation_with_tilde(self) -> None:
        """Test LaTeX rendering of R~ in abbreviation (relational inverse)."""
        input_text = "R~ == inv R"
        lexer = Lexer(input_text)
        parser = Parser(lexer.tokenize())
        ast = parser.parse()
        assert isinstance(ast, Document)
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # Should render as R^{-1} in standard LaTeX
        assert "R^{-1}" in latex

    def test_latex_schema_with_plus(self) -> None:
        """Test LaTeX rendering of S+ in schema name."""
        input_text = """schema S+
  x : N
end"""
        lexer = Lexer(input_text)
        parser = Parser(lexer.tokenize())
        ast = parser.parse()
        assert isinstance(ast, Document)
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # Should render schema name as S^+
        assert "S^+" in latex
        assert r"\begin{schema}{S^+}" in latex


class TestCompoundIdentifierIntegration:
    """Integration tests for Bug #3 fix."""

    def test_bug3_test_case(self) -> None:
        """Test the original Bug #3 test case."""
        input_text = """R+ == {a, b : N | b > a}"""
        lexer = Lexer(input_text)
        parser = Parser(lexer.tokenize())
        ast = parser.parse()
        assert isinstance(ast, Document)
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # Should compile without errors
        assert r"\begin{zed}" in latex
        assert "R^+" in latex
        assert r"\{" in latex  # Set comprehension

    def test_all_three_closures(self) -> None:
        """Test all three closure abbreviations: +, *, ~."""
        input_text = """R+ == {a, b : N | b > a}
R* == R+ union id[N]
R~ == inv R"""
        lexer = Lexer(input_text)
        parser = Parser(lexer.tokenize())
        ast = parser.parse()
        assert isinstance(ast, Document)
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # All three should render correctly
        assert "R^+" in latex
        assert "R^*" in latex
        assert "R^{-1}" in latex

    def test_compound_id_in_expression_context(self) -> None:
        """Test that R+ still works in expression context (not just names)."""
        # In expression context, R+ should parse as UnaryOp(+, Identifier(R))
        # This is different from: R+ == S (where R+ is the abbreviation name)
        input_text = "S == R+"
        lexer = Lexer(input_text)
        parser = Parser(lexer.tokenize())
        ast = parser.parse()
        assert isinstance(ast, Document)

        # The abbreviation name is "S" (simple identifier)
        # The expression is R+ (UnaryOp with + applied to R, transitive closure)
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # Should compile without errors
        assert r"\begin{zed}" in latex
        # S is the abbreviation name (no superscript)
        assert "S ==" in latex
        # R+ in expression context renders as R^{+} (closure operator)
        assert "R^{+}" in latex or "R^+" in latex


class TestCompoundIdentifierEdgeCases:
    """Test edge cases and potential conflicts."""

    def test_plus_as_arithmetic_vs_closure(self) -> None:
        """Test that R + S (arithmetic) is different from R+ (closure name)."""
        # R + S should parse as binary addition
        input_text1 = "R + S"
        lexer1 = Lexer(input_text1)
        parser1 = Parser(lexer1.tokenize())
        expr1 = parser1._parse_expr()

        # Should be BinaryOp
        assert expr1.__class__.__name__ == "BinaryOp"

        # R+ == expr should parse R+ as compound identifier name
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

        # Parse again for LaTeX generation (need fresh parser)
        lexer2 = Lexer(input_text)
        parser2 = Parser(lexer2.tokenize())
        ast = parser2.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # Should render as rel_1^+ (with underscore preserved)
        assert "rel_1^+" in latex
