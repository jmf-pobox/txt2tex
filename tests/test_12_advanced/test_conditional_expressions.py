"""Tests for Phase 16: Conditional Expressions (if/then/else)."""

from txt2tex.ast_nodes import (
    BinaryOp,
    Conditional,
    Document,
    Expr,
    Identifier,
    Number,
    SequenceLiteral,
    UnaryOp,
)
from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser


def parse_expr(text: str) -> Expr | Document:
    """Helper to parse expression."""
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    return parser.parse()


def generate_latex(text: str) -> str:
    """Helper to generate LaTeX from text."""
    ast = parse_expr(text)
    assert not isinstance(ast, Document)
    generator = LaTeXGenerator()
    return generator.generate_expr(ast)


class TestConditionalParsing:
    """Test conditional expression parsing."""

    def test_simple_conditional(self):
        """Test if x > 0 then x else -x."""
        ast = parse_expr("if x > 0 then x else -x")
        assert isinstance(ast, Conditional)
        assert isinstance(ast.condition, BinaryOp)
        assert ast.condition.operator == ">"
        assert isinstance(ast.then_expr, Identifier)
        assert ast.then_expr.name == "x"
        assert isinstance(ast.else_expr, UnaryOp)
        assert ast.else_expr.operator == "-"

    def test_conditional_with_comparison(self):
        """Test if s = <> then 0 else 1."""
        ast = parse_expr("if s = <> then 0 else 1")
        assert isinstance(ast, Conditional)
        assert isinstance(ast.condition, BinaryOp)
        assert ast.condition.operator == "="
        assert isinstance(ast.condition.right, SequenceLiteral)
        assert isinstance(ast.then_expr, Number)
        assert ast.then_expr.value == "0"
        assert isinstance(ast.else_expr, Number)
        assert ast.else_expr.value == "1"

    def test_conditional_with_complex_expressions(self):
        """Test if x > 0 then x * 2 else x - 1."""
        ast = parse_expr("if x > 0 then x * 2 else x - 1")
        assert isinstance(ast, Conditional)
        assert isinstance(ast.then_expr, BinaryOp)
        assert ast.then_expr.operator == "*"
        assert isinstance(ast.else_expr, BinaryOp)
        assert ast.else_expr.operator == "-"

    def test_nested_conditional_then(self):
        """Test if x > 0 then if x > 10 then 10 else x else 0."""
        ast = parse_expr("if x > 0 then if x > 10 then 10 else x else 0")
        assert isinstance(ast, Conditional)
        assert isinstance(ast.then_expr, Conditional)
        assert isinstance(ast.else_expr, Number)

    def test_nested_conditional_else(self):
        """Test if x > 0 then 1 else if x < 0 then -1 else 0."""
        ast = parse_expr("if x > 0 then 1 else if x < 0 then -1 else 0")
        assert isinstance(ast, Conditional)
        assert isinstance(ast.else_expr, Conditional)
        assert isinstance(ast.then_expr, Number)

    def test_conditional_in_binary_op(self):
        """Test y + if x > 0 then 1 else 0."""
        ast = parse_expr("y + if x > 0 then 1 else 0")
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "+"
        assert isinstance(ast.right, Conditional)


class TestConditionalLaTeX:
    """Test conditional expression LaTeX generation."""

    def test_simple_conditional_latex(self):
        """Test if x > 0 then x else -x → LaTeX."""
        result = generate_latex("if x > 0 then x else -x")
        assert "\\mbox{if }" in result
        assert "\\mbox{ then }" in result
        assert "\\mbox{ else }" in result
        assert "x > 0" in result
        assert "\\lnot" in result or "-x" in result

    def test_conditional_empty_sequence_latex(self):
        """Test if s = <> then 0 else 1 → LaTeX."""
        result = generate_latex("if s = <> then 0 else 1")
        assert "\\mbox{if }" in result
        assert "s = \\langle \\rangle" in result
        assert "\\mbox{ then } 0" in result
        assert "\\mbox{ else } 1" in result

    def test_conditional_with_arithmetic_latex(self):
        """Test if x > 0 then x * 2 else x - 1 → LaTeX."""
        result = generate_latex("if x > 0 then x * 2 else x - 1")
        assert "\\mbox{if }" in result
        assert "x > 0" in result
        assert "x * 2" in result or "x \\cdot 2" in result
        assert "x - 1" in result

    def test_nested_conditional_latex(self):
        """Test nested conditional generates valid LaTeX."""
        result = generate_latex("if x > 0 then if x > 10 then 10 else x else 0")
        assert result.count("\\mbox{if }") == 2
        assert result.count("\\mbox{ then }") == 2
        assert result.count("\\mbox{ else }") == 2

    def test_conditional_parenthesized(self):
        """Test that conditionals are wrapped elem parentheses."""
        result = generate_latex("if x > 0 then x else -x")
        assert result.startswith("(\\mbox{if }")
        assert result.endswith(")")


class TestConditionalPrecedence:
    """Test conditional expression precedence land associativity."""

    def test_conditional_binds_loosely(self):
        """Test that conditionals have low precedence."""
        ast = parse_expr("if x > 0 then 1 else 0")
        assert isinstance(ast, Conditional)
        assert isinstance(ast.condition, BinaryOp)
        assert ast.condition.operator == ">"

    def test_conditional_in_comparison(self):
        """Test conditional as subexpression."""
        ast = parse_expr("y = if x > 0 then 1 else 0")
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "="
        assert isinstance(ast.right, Conditional)

    def test_conditional_with_logical_ops(self):
        """Test if x land y then 1 else 0."""
        ast = parse_expr("if x land y then 1 else 0")
        assert isinstance(ast, Conditional)
        assert isinstance(ast.condition, BinaryOp)
        assert ast.condition.operator == "land"


class TestPhase16Integration:
    """Integration tests for Phase 16."""

    def test_absolute_value_function(self):
        """Test abs(x) = if x > 0 then x else -x."""
        latex = generate_latex("abs(x) = if x > 0 then x else -x")
        assert "abs(x) =" in latex
        assert "\\mbox{if }" in latex

    def test_conditional_in_recursive_function(self):
        """Test conditional in recursive function."""
        text = "f(n) = if n = 0 then 1 else n * f(n - 1)"
        ast = parse_expr(text)
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "="
        assert isinstance(ast.right, Conditional)
        latex = generate_latex(text)
        assert "\\mbox{if }" in latex
        assert "n = 0" in latex
        assert "f(n - 1)" in latex

    def test_max_function(self):
        """Test max(x, y) = if x > y then x else y."""
        latex = generate_latex("max(x, y) = if x > y then x else y")
        assert "max(x, y)" in latex
        assert "\\mbox{if }" in latex
        assert "x > y" in latex

    def test_sign_function(self):
        """Test sign(x) with nested conditionals."""
        text = "sign(x) = if x > 0 then 1 else if x < 0 then -1 else 0"
        ast = parse_expr(text)
        assert isinstance(ast, BinaryOp)
        assert isinstance(ast.right, Conditional)
        assert isinstance(ast.right.else_expr, Conditional)
        latex = generate_latex(text)
        assert latex.count("\\mbox{if }") == 2

    def test_conditional_in_set_comprehension(self):
        """Test { x : N | pred . if x > 0 then x else 0 }."""
        text = "{ x : N | x < 10 . if x > 0 then x else 0 }"
        latex = generate_latex(text)
        assert "\\{" in latex
        assert "\\mbox{if }" in latex
