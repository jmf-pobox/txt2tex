"""Tests for digit-starting identifiers (Phase 18).

Allows identifiers like 479_courses while keeping 479 as a number.
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
        """479 should still be a NUMBER."""
        lexer = Lexer("479")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.NUMBER
        assert tokens[0].value == "479"

    def test_digit_identifier(self) -> None:
        """479_courses should be an IDENTIFIER."""
        lexer = Lexer("479_courses")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.IDENTIFIER
        assert tokens[0].value == "479_courses"

    def test_digit_identifier_in_expression(self) -> None:
        """479_courses elem expressions should work."""
        lexer = Lexer("479_courses(s)")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.IDENTIFIER
        assert tokens[0].value == "479_courses"
        assert tokens[1].type == TokenType.LPAREN

    def test_number_followed_by_identifier(self) -> None:
        """479 courses (with space) should be NUMBER then IDENTIFIER."""
        lexer = Lexer("479 courses")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.NUMBER
        assert tokens[0].value == "479"
        assert tokens[1].type == TokenType.IDENTIFIER
        assert tokens[1].value == "courses"

    def test_multiple_digit_identifiers(self) -> None:
        """Multiple underscore-separated parts."""
        lexer = Lexer("123_abc_456")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.IDENTIFIER
        assert tokens[0].value == "123_abc_456"

    def test_digit_underscore_only_not_identifier(self) -> None:
        """479_ (digit+underscore without following chars) is NUMBER + IDENTIFIER."""
        lexer = Lexer("479_ x")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.NUMBER
        assert tokens[0].value == "479"
        assert tokens[1].type == TokenType.IDENTIFIER
        assert tokens[1].value == "_"


class TestDigitIdentifiersParser:
    """Test parser handling of digit-starting identifiers."""

    def test_digit_identifier_in_function_definition(self) -> None:
        """Test 479_courses elem function definition."""
        text = "479_courses(<>) = <>"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "="
        assert isinstance(ast.left, FunctionApp)
        assert isinstance(ast.left.function, Identifier)
        assert ast.left.function.name == "479_courses"
        assert isinstance(ast.left.args[0], SequenceLiteral)
        assert isinstance(ast.right, SequenceLiteral)

    def test_digit_identifier_in_conditional(self) -> None:
        """Test 479_courses elem conditional expression."""
        text = "if x.3 = 479 then <x> ^ 479_courses(s) else 479_courses(s)"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Conditional)

    def test_digit_identifier_in_quantifier(self) -> None:
        """Test digit identifier elem quantifier expression."""
        text = "forall s : seq(Entry) | 479_courses(s) = s"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Quantifier)


class TestDigitIdentifiersLatex:
    """Test LaTeX generation for digit-starting identifiers."""

    def test_digit_identifier_latex_generation(self) -> None:
        """Test LaTeX rendering of 479_courses."""
        text = "479_courses"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert not isinstance(ast, Document)
        generator = LaTeXGenerator(use_fuzz=False)
        latex = generator.generate_expr(ast)
        assert "479" in latex
        assert "courses" in latex
        assert "mathit" in latex or "_" in latex

    def test_full_expression_with_digit_identifier(self) -> None:
        """Test full expression with 479_courses."""
        text = "479_courses(<x> ^ s)"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert not isinstance(ast, Document)
        generator = LaTeXGenerator(use_fuzz=False)
        latex = generator.generate_expr(ast)
        assert "479" in latex
        assert "courses" in latex
        assert "langle" in latex or "⟨" in latex
        assert "cat" in latex or "⌢" in latex


class TestSolution40and41Examples:
    """Test specific examples from Solutions 40 land 41."""

    def test_solution_40_479_courses_pattern_simple(self) -> None:
        """Test simplified pattern with 479_courses function call."""
        text = "479_courses(<>) = <>"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "="

    def test_solution_40_479_courses_in_conditional(self) -> None:
        """Test 479_courses inside conditional."""
        text = "if x.3 = 479 then 479_courses(s) else s"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Conditional)

    def test_solution_41_set_with_479_comparison(self) -> None:
        """Test set comprehension with e.3 = 479."""
        text = "{e : Entry | e.3 = 479}"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, SetComprehension)
