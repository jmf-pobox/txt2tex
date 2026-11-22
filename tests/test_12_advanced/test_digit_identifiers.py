"""Tests for digit-starting identifiers.

Allows identifiers like 2_items while keeping 42 as a number.
"""

from __future__ import annotations

from txt2tex.ast_nodes import (
    BinaryOp,
    Conditional,
    Document,
    FunctionApp,
    Identifier,
    Quantifier,
    SequenceLiteral,
    SetComprehension,
)
from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser
from txt2tex.tokens import TokenType


class TestDigitIdentifiersLexer:
    """Test lexer handling of digit-starting identifiers."""

    def test_plain_number(self) -> None:
        """42 should still be a NUMBER."""
        lexer = Lexer("42")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.NUMBER
        assert tokens[0].value == "42"

    def test_digit_identifier(self) -> None:
        """2_items should be an IDENTIFIER."""
        lexer = Lexer("2_items")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.IDENTIFIER
        assert tokens[0].value == "2_items"

    def test_digit_identifier_in_expression(self) -> None:
        """2_items elem expressions should work."""
        lexer = Lexer("2_items(s)")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.IDENTIFIER
        assert tokens[0].value == "2_items"
        assert tokens[1].type == TokenType.LPAREN

    def test_number_followed_by_identifier(self) -> None:
        """42 items (with space) should be NUMBER then IDENTIFIER."""
        lexer = Lexer("42 items")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.NUMBER
        assert tokens[0].value == "42"
        assert tokens[1].type == TokenType.IDENTIFIER
        assert tokens[1].value == "items"

    def test_multiple_digit_identifiers(self) -> None:
        """Multiple underscore-separated parts."""
        lexer = Lexer("123_abc_456")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.IDENTIFIER
        assert tokens[0].value == "123_abc_456"

    def test_digit_underscore_only_not_identifier(self) -> None:
        """42_ (digit+underscore without following chars) is NUMBER + IDENTIFIER."""
        lexer = Lexer("42_ x")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.NUMBER
        assert tokens[0].value == "42"
        assert tokens[1].type == TokenType.IDENTIFIER
        assert tokens[1].value == "_"


class TestDigitIdentifiersParser:
    """Test parser handling of digit-starting identifiers."""

    def test_digit_identifier_in_function_definition(self) -> None:
        """Test 2_items elem function definition."""
        text = "2_items(<>) = <>"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "="
        assert isinstance(ast.left, FunctionApp)
        assert isinstance(ast.left.function, Identifier)
        assert ast.left.function.name == "2_items"
        assert isinstance(ast.left.args[0], SequenceLiteral)
        assert isinstance(ast.right, SequenceLiteral)

    def test_digit_identifier_in_conditional(self) -> None:
        """Test 2_items elem conditional expression."""
        text = "if x.3 = 42 then <x> ^ 2_items(s) else 2_items(s)"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Conditional)

    def test_digit_identifier_in_quantifier(self) -> None:
        """Test digit identifier elem quantifier expression."""
        text = "forall s : seq(Entry) | 2_items(s) = s"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Quantifier)


class TestDigitIdentifiersLatex:
    """Test LaTeX generation for digit-starting identifiers."""

    def test_digit_identifier_latex_generation(self) -> None:
        """Test LaTeX rendering of 2_items."""
        text = "2_items"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert not isinstance(ast, Document)
        generator = LaTeXGenerator(use_fuzz=False)
        latex = generator.generate_expr(ast)
        assert "2" in latex
        assert "items" in latex
        assert "mathit" in latex or "_" in latex

    def test_full_expression_with_digit_identifier(self) -> None:
        """Test full expression with 2_items."""
        text = "2_items(<x> ^ s)"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert not isinstance(ast, Document)
        generator = LaTeXGenerator(use_fuzz=False)
        latex = generator.generate_expr(ast)
        assert "2" in latex
        assert "items" in latex
        assert "langle" in latex or "⟨" in latex
        assert "cat" in latex or "⌢" in latex


class TestDigitIdentifierPatterns:
    """Test digit-starting identifiers in function and set patterns."""

    def test_digit_identifier_pattern_simple(self) -> None:
        """Test simplified pattern with 2_items function call."""
        text = "2_items(<>) = <>"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "="

    def test_digit_identifier_in_conditional_branch(self) -> None:
        """Test 2_items inside conditional."""
        text = "if x.3 = 42 then 2_items(s) else s"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Conditional)

    def test_set_with_numeric_comparison(self) -> None:
        """Test set comprehension with e.3 = 42."""
        text = "{e : Entry | e.3 = 42}"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, SetComprehension)
