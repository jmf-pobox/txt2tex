"""Tests for Phase 3: Quantifiers, subscripts, superscripts, and mathematical notation."""

from __future__ import annotations

import pytest

from txt2tex.ast_nodes import (
    BinaryOp,
    Identifier,
    Number,
    Quantifier,
    Subscript,
    Superscript,
)
from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser


class TestLexer:
    """Tests for Phase 3 lexer features."""

    def test_forall_keyword(self) -> None:
        """Test lexing forall keyword."""
        lexer = Lexer("forall x")
        tokens = lexer.tokenize()
        assert tokens[0].type.name == "FORALL"
        assert tokens[1].type.name == "IDENTIFIER"

    def test_exists_keyword(self) -> None:
        """Test lexing exists keyword."""
        lexer = Lexer("exists y")
        tokens = lexer.tokenize()
        assert tokens[0].type.name == "EXISTS"

    def test_colon(self) -> None:
        """Test lexing colon."""
        lexer = Lexer("x : N")
        tokens = lexer.tokenize()
        assert tokens[1].type.name == "COLON"

    def test_comparison_operators(self) -> None:
        """Test lexing comparison operators."""
        lexer = Lexer("x < y <= z > w >= v = u")
        tokens = lexer.tokenize()
        types = [t.type.name for t in tokens[:-1][1::2]]  # Exclude EOF, every other is operator
        assert types == [
            "LESS_THAN",
            "LESS_EQUAL",
            "GREATER_THAN",
            "GREATER_EQUAL",
            "EQUALS",
        ]

    def test_set_operators(self) -> None:
        """Test lexing set operators."""
        lexer = Lexer("x in A subset B union C intersect D")
        tokens = lexer.tokenize()
        types = [t.type.name for t in tokens[:-1][1::2]]  # Exclude EOF
        assert types == ["IN", "SUBSET", "UNION", "INTERSECT"]

    def test_caret_and_underscore(self) -> None:
        """Test lexing caret and underscore."""
        lexer = Lexer("x^2 a_1")
        tokens = lexer.tokenize()
        # x ^ 2 a _ 1 EOF
        assert tokens[1].type.name == "CARET"
        assert tokens[4].type.name == "UNDERSCORE"

    def test_numbers(self) -> None:
        """Test lexing numbers."""
        lexer = Lexer("1 42 999")
        tokens = lexer.tokenize()
        assert tokens[0].type.name == "NUMBER"
        assert tokens[0].value == "1"
        assert tokens[1].value == "42"
        assert tokens[2].value == "999"


class TestParser:
    """Tests for Phase 3 parser features."""

    def test_number(self) -> None:
        """Test parsing number."""
        lexer = Lexer("42")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Number)
        assert ast.value == "42"

    def test_superscript(self) -> None:
        """Test parsing superscript."""
        lexer = Lexer("x^2")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Superscript)
        assert isinstance(ast.base, Identifier)
        assert ast.base.name == "x"
        assert isinstance(ast.exponent, Number)
        assert ast.exponent.value == "2"

    def test_subscript(self) -> None:
        """Test parsing subscript."""
        lexer = Lexer("a_1")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Subscript)
        assert isinstance(ast.base, Identifier)
        assert ast.base.name == "a"
        assert isinstance(ast.index, Number)
        assert ast.index.value == "1"

    def test_multiple_postfix(self) -> None:
        """Test parsing multiple postfix operators."""
        lexer = Lexer("x_i^2")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        # Should parse as (x_i)^2
        assert isinstance(ast, Superscript)
        assert isinstance(ast.base, Subscript)
        assert ast.base.base.name == "x"

    def test_comparison_less_than(self) -> None:
        """Test parsing less than comparison."""
        lexer = Lexer("x < 10")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "<"

    def test_comparison_greater_equal(self) -> None:
        """Test parsing greater than or equal comparison."""
        lexer = Lexer("x >= 0")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, BinaryOp)
        assert ast.operator == ">="

    def test_set_operator_in(self) -> None:
        """Test parsing 'in' operator."""
        lexer = Lexer("x in N")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "in"

    def test_set_operator_union(self) -> None:
        """Test parsing 'union' operator."""
        lexer = Lexer("A union B")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "union"

    def test_quantifier_forall_no_domain(self) -> None:
        """Test parsing forall without domain."""
        lexer = Lexer("forall x | x > 0")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Quantifier)
        assert ast.quantifier == "forall"
        assert ast.variable == "x"
        assert ast.domain is None
        assert isinstance(ast.body, BinaryOp)

    def test_quantifier_forall_with_domain(self) -> None:
        """Test parsing forall with domain."""
        lexer = Lexer("forall x : N | x > 0")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Quantifier)
        assert ast.quantifier == "forall"
        assert ast.variable == "x"
        assert isinstance(ast.domain, Identifier)
        assert ast.domain.name == "N"

    def test_quantifier_exists(self) -> None:
        """Test parsing exists."""
        lexer = Lexer("exists y : N | y = 0")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Quantifier)
        assert ast.quantifier == "exists"
        assert ast.variable == "y"

    def test_complex_quantified_expr(self) -> None:
        """Test parsing complex quantified expression."""
        lexer = Lexer("forall n : N | n >= 0 and n < 100")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Quantifier)
        assert isinstance(ast.body, BinaryOp)
        assert ast.body.operator == "and"


class TestLaTeXGenerator:
    """Tests for Phase 3 LaTeX generator."""

    def test_number(self) -> None:
        """Test generating number."""
        gen = LaTeXGenerator()
        ast = Number(value="42", line=1, column=1)
        latex = gen.generate_expr(ast)
        assert latex == "42"

    def test_superscript(self) -> None:
        """Test generating superscript."""
        gen = LaTeXGenerator()
        ast = Superscript(
            base=Identifier(name="x", line=1, column=1),
            exponent=Number(value="2", line=1, column=3),
            line=1,
            column=2,
        )
        latex = gen.generate_expr(ast)
        assert latex == "x^2"

    def test_superscript_multichar(self) -> None:
        """Test generating superscript with multi-character exponent."""
        gen = LaTeXGenerator()
        ast = Superscript(
            base=Identifier(name="x", line=1, column=1),
            exponent=Identifier(name="ab", line=1, column=3),
            line=1,
            column=2,
        )
        latex = gen.generate_expr(ast)
        assert latex == "x^{ab}"

    def test_subscript(self) -> None:
        """Test generating subscript."""
        gen = LaTeXGenerator()
        ast = Subscript(
            base=Identifier(name="a", line=1, column=1),
            index=Number(value="1", line=1, column=3),
            line=1,
            column=2,
        )
        latex = gen.generate_expr(ast)
        assert latex == "a_1"

    def test_subscript_multichar(self) -> None:
        """Test generating subscript with multi-character index."""
        gen = LaTeXGenerator()
        ast = Subscript(
            base=Identifier(name="x", line=1, column=1),
            index=Identifier(name="max", line=1, column=3),
            line=1,
            column=2,
        )
        latex = gen.generate_expr(ast)
        assert latex == "x_{max}"

    def test_comparison_less_than(self) -> None:
        """Test generating less than."""
        gen = LaTeXGenerator()
        ast = BinaryOp(
            operator="<",
            left=Identifier(name="x", line=1, column=1),
            right=Number(value="10", line=1, column=5),
            line=1,
            column=3,
        )
        latex = gen.generate_expr(ast)
        assert latex == "x < 10"

    def test_comparison_less_equal(self) -> None:
        """Test generating less than or equal."""
        gen = LaTeXGenerator()
        ast = BinaryOp(
            operator="<=",
            left=Identifier(name="x", line=1, column=1),
            right=Number(value="10", line=1, column=6),
            line=1,
            column=3,
        )
        latex = gen.generate_expr(ast)
        assert latex == r"x \leq 10"

    def test_set_operator_in(self) -> None:
        """Test generating 'in' operator."""
        gen = LaTeXGenerator()
        ast = BinaryOp(
            operator="in",
            left=Identifier(name="x", line=1, column=1),
            right=Identifier(name="N", line=1, column=6),
            line=1,
            column=3,
        )
        latex = gen.generate_expr(ast)
        assert latex == r"x \in N"

    def test_set_operator_subset(self) -> None:
        """Test generating 'subset' operator."""
        gen = LaTeXGenerator()
        ast = BinaryOp(
            operator="subset",
            left=Identifier(name="A", line=1, column=1),
            right=Identifier(name="B", line=1, column=10),
            line=1,
            column=3,
        )
        latex = gen.generate_expr(ast)
        assert latex == r"A \subseteq B"

    def test_set_operator_union(self) -> None:
        """Test generating 'union' operator."""
        gen = LaTeXGenerator()
        ast = BinaryOp(
            operator="union",
            left=Identifier(name="A", line=1, column=1),
            right=Identifier(name="B", line=1, column=9),
            line=1,
            column=3,
        )
        latex = gen.generate_expr(ast)
        assert latex == r"A \cup B"

    def test_set_operator_intersect(self) -> None:
        """Test generating 'intersect' operator."""
        gen = LaTeXGenerator()
        ast = BinaryOp(
            operator="intersect",
            left=Identifier(name="A", line=1, column=1),
            right=Identifier(name="B", line=1, column=13),
            line=1,
            column=3,
        )
        latex = gen.generate_expr(ast)
        assert latex == r"A \cap B"

    def test_quantifier_forall_no_domain(self) -> None:
        """Test generating forall without domain."""
        gen = LaTeXGenerator()
        ast = Quantifier(
            quantifier="forall",
            variable="x",
            domain=None,
            body=BinaryOp(
                operator=">",
                left=Identifier(name="x", line=1, column=15),
                right=Number(value="0", line=1, column=19),
                line=1,
                column=17,
            ),
            line=1,
            column=1,
        )
        latex = gen.generate_expr(ast)
        assert latex == r"\forall x \bullet x > 0"

    def test_quantifier_forall_with_domain(self) -> None:
        """Test generating forall with domain."""
        gen = LaTeXGenerator()
        ast = Quantifier(
            quantifier="forall",
            variable="x",
            domain=Identifier(name="N", line=1, column=11),
            body=BinaryOp(
                operator=">",
                left=Identifier(name="x", line=1, column=15),
                right=Number(value="0", line=1, column=19),
                line=1,
                column=17,
            ),
            line=1,
            column=1,
        )
        latex = gen.generate_expr(ast)
        assert latex == r"\forall x \colon N \bullet x > 0"

    def test_quantifier_exists(self) -> None:
        """Test generating exists."""
        gen = LaTeXGenerator()
        ast = Quantifier(
            quantifier="exists",
            variable="y",
            domain=Identifier(name="N", line=1, column=11),
            body=BinaryOp(
                operator="=",
                left=Identifier(name="y", line=1, column=15),
                right=Number(value="0", line=1, column=19),
                line=1,
                column=17,
            ),
            line=1,
            column=1,
        )
        latex = gen.generate_expr(ast)
        assert latex == r"\exists y \colon N \bullet y = 0"


class TestIntegration:
    """End-to-end integration tests for Phase 3."""

    def test_simple_superscript(self) -> None:
        """Test complete pipeline for superscript."""
        text = "x^2"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)
        assert latex == "x^2"

    def test_simple_subscript(self) -> None:
        """Test complete pipeline for subscript."""
        text = "a_1"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)
        assert latex == "a_1"

    def test_comparison_expression(self) -> None:
        """Test complete pipeline for comparison."""
        text = "x >= 0 and x < 10"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)
        assert latex == r"x \geq 0 \land x < 10"

    def test_set_membership(self) -> None:
        """Test complete pipeline for set membership."""
        text = "x in N and x > 0"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)
        assert latex == r"x \in N \land x > 0"

    def test_quantifier_expression(self) -> None:
        """Test complete pipeline for quantifier."""
        text = "forall x : N | x >= 0"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)
        assert latex == r"\forall x \colon N \bullet x \geq 0"

    def test_complex_quantified_expression(self) -> None:
        """Test complete pipeline for complex quantified expression."""
        text = "forall n : N | n >= 0 and n < 100"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)
        assert latex == r"\forall n \colon N \bullet n \geq 0 \land n < 100"

    def test_subscript_with_identifier_index(self) -> None:
        """Test subscript with identifier index."""
        text = "x_i"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)
        assert latex == "x_i"
