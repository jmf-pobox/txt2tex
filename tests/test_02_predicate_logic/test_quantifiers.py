"""Tests for quantifiers, subscripts, superscripts, and math operators."""

from __future__ import annotations

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
    """Tests for quantifier lexer features."""

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
        types = [t.type.name for t in tokens[:-1][1::2]]
        assert types == [
            "LESS_THAN",
            "LESS_EQUAL",
            "GREATER_THAN",
            "GREATER_EQUAL",
            "EQUALS",
        ]

    def test_set_operators(self) -> None:
        """Test lexing set operators."""
        lexer = Lexer("x elem A subset B union C intersect D")
        tokens = lexer.tokenize()
        types = [t.type.name for t in tokens[:-1][1::2]]
        assert types == ["IN", "SUBSET", "UNION", "INTERSECT"]

    def test_caret_and_underscore(self) -> None:
        """Test lexing caret (underscore is now part of identifiers)."""
        lexer = Lexer("x^2 a_1")
        tokens = lexer.tokenize()
        assert tokens[1].type.name == "CARET"
        assert tokens[3].type.name == "IDENTIFIER"
        assert tokens[3].value == "a_1"

    def test_numbers(self) -> None:
        """Test lexing numbers."""
        lexer = Lexer("1 42 999")
        tokens = lexer.tokenize()
        assert tokens[0].type.name == "NUMBER"
        assert tokens[0].value == "1"
        assert tokens[1].value == "42"
        assert tokens[2].value == "999"


class TestParser:
    """Tests for quantifier parser features."""

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
        """Test parsing subscript (underscore in identifiers)."""
        lexer = Lexer("a_1")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Identifier)
        assert ast.name == "a_1"

    def test_multiple_postfix(self) -> None:
        """Test parsing multiple postfix operators."""
        lexer = Lexer("x_i^2")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Superscript)
        assert isinstance(ast.base, Identifier)
        assert ast.base.name == "x_i"

    def test_comparison_less_than(self) -> None:
        """Test parsing less than comparison."""
        lexer = Lexer("x < 10")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "<"

    def test_comparison_greater_equal(self) -> None:
        """Test parsing greater than lor equal comparison."""
        lexer = Lexer("x >= 0")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, BinaryOp)
        assert ast.operator == ">="

    def test_set_operator_in(self) -> None:
        """Test parsing 'elem' operator."""
        lexer = Lexer("x elem N")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "elem"

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
        assert ast.variables == ["x"]
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
        assert ast.variables == ["x"]
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
        assert ast.variables == ["y"]

    def test_quantifier_multi_variable(self) -> None:
        """Test parsing forall with multiple variables."""
        lexer = Lexer("forall x, y : N | x > y")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Quantifier)
        assert ast.quantifier == "forall"
        assert ast.variables == ["x", "y"]
        assert isinstance(ast.domain, Identifier)
        assert ast.domain.name == "N"

    def test_quantifier_exists1(self) -> None:
        """Test parsing exists1 (unique existence)."""
        lexer = Lexer("exists1 x : N | x = 0")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Quantifier)
        assert ast.quantifier == "exists1"
        assert ast.variables == ["x"]

    def test_quantifier_multi_variable_no_domain(self) -> None:
        """Test parsing multi-variable quantifier without domain."""
        lexer = Lexer("exists x, y | x > y")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Quantifier)
        assert ast.quantifier == "exists"
        assert ast.variables == ["x", "y"]
        assert ast.domain is None

    def test_complex_quantified_expr(self) -> None:
        """Test parsing complex quantified expression."""
        lexer = Lexer("forall n : N | n >= 0 land n < 100")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Quantifier)
        assert isinstance(ast.body, BinaryOp)
        assert ast.body.operator == "land"


class TestLaTeXGenerator:
    """Tests for quantifier LaTeX generation."""

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
        assert latex == "x \\bsup 2 \\esup"

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
        assert latex == "x \\bsup ab \\esup"

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
        """Test generating less than lor equal."""
        gen = LaTeXGenerator()
        ast = BinaryOp(
            operator="<=",
            left=Identifier(name="x", line=1, column=1),
            right=Number(value="10", line=1, column=6),
            line=1,
            column=3,
        )
        latex = gen.generate_expr(ast)
        assert latex == "x \\leq 10"

    def test_set_operator_in(self) -> None:
        """Test generating 'elem' operator."""
        gen = LaTeXGenerator()
        ast = BinaryOp(
            operator="elem",
            left=Identifier(name="x", line=1, column=1),
            right=Identifier(name="N", line=1, column=6),
            line=1,
            column=3,
        )
        latex = gen.generate_expr(ast)
        assert latex == "x \\in \\mathbb{N}"

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
        assert latex == "A \\subseteq B"

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
        assert latex == "A \\cup B"

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
        assert latex == "A \\cap B"

    def test_quantifier_forall_no_domain(self) -> None:
        """Test generating forall without domain."""
        gen = LaTeXGenerator()
        ast = Quantifier(
            quantifier="forall",
            variables=["x"],
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
        assert latex == "\\forall x \\bullet x > 0"

    def test_quantifier_forall_with_domain(self) -> None:
        """Test generating forall with domain."""
        gen = LaTeXGenerator()
        ast = Quantifier(
            quantifier="forall",
            variables=["x"],
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
        assert latex == "\\forall x \\colon \\mathbb{N} \\bullet x > 0"

    def test_quantifier_exists(self) -> None:
        """Test generating exists."""
        gen = LaTeXGenerator()
        ast = Quantifier(
            quantifier="exists",
            variables=["y"],
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
        assert latex == "\\exists y \\colon \\mathbb{N} \\bullet y = 0"

    def test_quantifier_multi_variable(self) -> None:
        """Test generating multi-variable forall."""
        gen = LaTeXGenerator()
        ast = Quantifier(
            quantifier="forall",
            variables=["x", "y"],
            domain=Identifier(name="N", line=1, column=14),
            body=BinaryOp(
                operator=">",
                left=Identifier(name="x", line=1, column=18),
                right=Identifier(name="y", line=1, column=22),
                line=1,
                column=20,
            ),
            line=1,
            column=1,
        )
        latex = gen.generate_expr(ast)
        assert latex == "\\forall x, y \\colon \\mathbb{N} \\bullet x > y"

    def test_quantifier_exists1(self) -> None:
        """Test generating exists1."""
        gen = LaTeXGenerator()
        ast = Quantifier(
            quantifier="exists1",
            variables=["x"],
            domain=Identifier(name="N", line=1, column=12),
            body=BinaryOp(
                operator="=",
                left=Identifier(name="x", line=1, column=16),
                right=Number(value="0", line=1, column=20),
                line=1,
                column=18,
            ),
            line=1,
            column=1,
        )
        latex = gen.generate_expr(ast)
        assert latex == "\\exists_1 x \\colon \\mathbb{N} \\bullet x = 0"


class TestIntegration:
    """End-to-end integration tests for quantifiers."""

    def test_simple_superscript(self) -> None:
        """Test complete pipeline for superscript."""
        text = "x^2"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Superscript)
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)
        assert latex == "x \\bsup 2 \\esup"

    def test_simple_subscript(self) -> None:
        """Test complete pipeline for subscript."""
        text = "a_1"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Identifier)
        assert ast.name == "a_1"
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)
        assert latex == "a_1"

    def test_comparison_expression(self) -> None:
        """Test complete pipeline for comparison."""
        text = "x >= 0 land x < 10"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, BinaryOp)
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)
        assert latex == "x \\geq 0 \\land x < 10"

    def test_set_membership(self) -> None:
        """Test complete pipeline for set membership."""
        text = "x elem N land x > 0"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, BinaryOp)
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)
        assert latex == "x \\in \\mathbb{N} \\land x > 0"

    def test_quantifier_expression(self) -> None:
        """Test complete pipeline for quantifier."""
        text = "forall x : N | x >= 0"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Quantifier)
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)
        assert latex == "\\forall x \\colon \\mathbb{N} \\bullet x \\geq 0"

    def test_complex_quantified_expression(self) -> None:
        """Test complete pipeline for complex quantified expression."""
        text = "forall n : N | n >= 0 land n < 100"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Quantifier)
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)
        assert (
            latex == "\\forall n \\colon \\mathbb{N} \\bullet n \\geq 0 \\land n < 100"
        )

    def test_subscript_with_identifier_index(self) -> None:
        """Test subscript with identifier index."""
        text = "x_i"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Identifier)
        assert ast.name == "x_i"
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)
        assert latex == "x_i"

    def test_multi_variable_quantifier(self) -> None:
        """Test complete pipeline for multi-variable quantifier."""
        text = "forall x, y : N | x > y"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Quantifier)
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)
        assert latex == "\\forall x, y \\colon \\mathbb{N} \\bullet x > y"

    def test_exists1_quantifier(self) -> None:
        """Test complete pipeline for exists1 quantifier."""
        text = "exists1 x : N | x = 0"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Quantifier)
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)
        assert latex == "\\exists_1 x \\colon \\mathbb{N} \\bullet x = 0"

    def test_complex_multi_variable_expression(self) -> None:
        """Test complete pipeline for complex multi-variable expression."""
        text = "exists x, y : N | x > 0 land y > 0 land x > y"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Quantifier)
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)
        assert latex == (
            "\\exists x, y \\colon \\mathbb{N} \\bullet x > 0 \\land y > 0 \\land x > y"
        )


class TestBulletSeparator:
    """Tests for bullet separator (GitHub issue #8)."""

    def test_forall_with_bullet_simple(self) -> None:
        """Test forall with bullet separator: forall x : N | x > 0 . x < 10."""
        text = "(forall x : N | x > 0 . x < 10)"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Quantifier)
        assert ast.quantifier == "forall"
        assert ast.variables == ["x"]
        assert isinstance(ast.domain, Identifier)
        assert ast.domain.name == "N"
        assert isinstance(ast.body, BinaryOp)
        assert ast.body.operator == ">"
        assert isinstance(ast.expression, BinaryOp)
        assert ast.expression.operator == "<"
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)
        assert latex == "\\forall x \\colon \\mathbb{N} \\mid x > 0 \\bullet x < 10"

    def test_exists_with_bullet(self) -> None:
        """Test exists with bullet separator: exists y : Z | y < 0 . y > -10."""
        text = "(exists y : Z | y < 0 . y > -10)"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Quantifier)
        assert ast.quantifier == "exists"
        assert ast.variables == ["y"]
        assert ast.expression is not None
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)
        assert latex == "\\exists y \\colon \\mathbb{Z} \\mid y < 0 \\bullet y > -10"

    def test_exists1_with_bullet(self) -> None:
        """Test exists1 with bullet separator: exists1 x : N | x * x = 4 . x > 0."""
        text = "(exists1 x : N | x * x = 4 . x > 0)"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Quantifier)
        assert ast.quantifier == "exists1"
        assert ast.variables == ["x"]
        assert ast.expression is not None
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)
        expected = "\\exists_1 x \\colon \\mathbb{N} \\mid x * x = 4 \\bullet x > 0"
        assert latex == expected

    def test_forall_multi_variable_with_bullet(self) -> None:
        """Test forall with multiple variables land bullet separator."""
        text = "(forall x, y : N | x > 0 land y > 0 . x + y > 0)"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Quantifier)
        assert ast.quantifier == "forall"
        assert ast.variables == ["x", "y"]
        assert ast.expression is not None
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)
        expected = (
            "\\forall x, y \\colon \\mathbb{N} \\mid "
            "x > 0 \\land y > 0 \\bullet x + y > 0"
        )
        assert latex == expected

    def test_nested_quantifiers_with_bullet(self) -> None:
        """Test nested quantifiers where inner quantifier has bullet separator."""
        text = "(forall x : N | exists y : N | y > 0 . x + y > 0)"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Quantifier)
        assert ast.quantifier == "forall"
        assert isinstance(ast.body, Quantifier)
        assert ast.body.quantifier == "exists"
        assert ast.body.expression is not None
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)
        expected = (
            "\\forall x \\colon \\mathbb{N} \\bullet "
            "\\exists y \\colon \\mathbb{N} \\mid y > 0 \\bullet x + y > 0"
        )
        assert latex == expected

    def test_forall_without_bullet_still_works(self) -> None:
        """Test backward compatibility: forall without bullet still works."""
        text = "forall x : N | x > 0"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Quantifier)
        assert ast.quantifier == "forall"
        assert ast.expression is None
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)
        assert latex == "\\forall x \\colon \\mathbb{N} \\bullet x > 0"

    def test_mu_with_bullet_still_works(self) -> None:
        """Test backward compatibility: mu with bullet still works."""
        text = "(mu x : N | x > 0 . x * x)"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Quantifier)
        assert ast.quantifier == "mu"
        assert ast.expression is not None
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)
        assert latex == "\\mu x \\colon \\mathbb{N} \\mid x > 0 \\bullet x * x"

    def test_complex_constraint_with_bullet(self) -> None:
        """Test complex constraint expression with bullet separator.

        Based on GitHub issue #8 example.
        """
        text = (
            "(forall e_1, e_2 : ChapterId | (e_1 elem S land e_2 elem S) . "
            "(e_1 < e_2 => f(e_1) <= f(e_2)))"
        )
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Quantifier)
        assert ast.quantifier == "forall"
        assert ast.variables == ["e_1", "e_2"]
        assert ast.expression is not None
        assert isinstance(ast.body, BinaryOp)
        assert ast.body.operator == "land"
        assert isinstance(ast.expression, BinaryOp)
        assert ast.expression.operator == "=>"

    def test_bullet_with_continuation_backslash(self) -> None:
        """Test bullet separator followed by continuation backslash.

        Input: forall x : N | x > 0 . \\
                 x < 10

        Should parse successfully with body=(x > 0) and expression=(x < 10).
        """
        text = "(forall x : N | x > 0 . \\\n  x < 10)"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Quantifier)
        assert ast.quantifier == "forall"
        assert ast.variables == ["x"]
        assert isinstance(ast.body, BinaryOp)
        assert ast.body.operator == ">"
        assert isinstance(ast.expression, BinaryOp)
        assert ast.expression.operator == "<"
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)
        assert "\\mid x > 0" in latex
        assert "\\bullet" in latex
        assert "x < 10" in latex

    def test_bullet_with_newline_no_backslash(self) -> None:
        """Test bullet separator followed by newline (no backslash).

        Input: forall x : N | x > 0 .
                 x < 10

        Should parse successfully - newlines after bullet should be skipped.
        """
        text = "(forall x : N | x > 0 .\n  x < 10)"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Quantifier)
        assert ast.quantifier == "forall"
        assert ast.variables == ["x"]
        assert isinstance(ast.body, BinaryOp)
        assert ast.body.operator == ">"
        assert isinstance(ast.expression, BinaryOp)
        assert ast.expression.operator == "<"

    def test_bullet_multiline_complex_expression(self) -> None:
        """Test multi-line bullet separator with complex body expression.

        Based on real use case from axdef with viewed function.
        """
        text = """(forall r : Recording | r elem ran hd .
          r.viewed = yes => result = r)"""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Quantifier)
        assert ast.quantifier == "forall"
        assert ast.variables == ["r"]
        # Body should be the constraint (r elem ran hd)
        assert isinstance(ast.body, BinaryOp)
        assert ast.body.operator == "elem"
        # Expression should be the implication after bullet
        assert isinstance(ast.expression, BinaryOp)
        assert ast.expression.operator == "=>"

    def test_nested_quantifier_with_bullet_multiline(self) -> None:
        """Test nested quantifiers where inner has multi-line bullet.

        Input:
        forall h : seq N | (forall r : N | r elem ran hd .
          r > 0)
        """
        text = """(forall h : seq N | (forall r : N | r elem ran hd .
          r > 0))"""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Quantifier)
        assert ast.quantifier == "forall"
        # Outer quantifier body should be inner quantifier
        assert isinstance(ast.body, Quantifier)
        inner = ast.body
        assert inner.quantifier == "forall"
        # Inner quantifier should have expression (bullet separator used)
        assert inner.expression is not None
        assert isinstance(inner.body, BinaryOp)
        assert inner.body.operator == "elem"

    def test_bullet_wysiwyg_line_break(self) -> None:
        """Test WYSIWYG line break after bullet separator is preserved.

        When user writes:
        forall x : N | x > 0 .
          x < 10

        The line break after '.' should produce \\\\ in LaTeX output.
        """
        text = "(forall x : N | x > 0 .\n  x < 10)"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Quantifier)
        # Line break after bullet should be detected
        assert ast.line_break_after_bullet is True
        # Generate LaTeX and verify line break is present
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)
        # Should have \\ after bullet separator
        assert "\\bullet \\\\" in latex or "@ \\\\" in latex

    def test_bullet_wysiwyg_line_break_fuzz_mode(self) -> None:
        """Test WYSIWYG line break in fuzz mode produces @ followed by \\\\."""
        text = "(forall r : Recording | r elem ran hd .\n  r.viewed = yes)"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Quantifier)
        assert ast.line_break_after_bullet is True
        gen = LaTeXGenerator(use_fuzz=True)
        latex = gen.generate_expr(ast)
        # In fuzz mode, should have @ \\ with line break
        assert "@ \\\\" in latex
        # Expression should be on next line with indentation
        assert "\\t" in latex or "\\quad" in latex
