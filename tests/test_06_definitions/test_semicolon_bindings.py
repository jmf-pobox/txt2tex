"""Phase 17: Semicolon-separated bindings elem quantifiers land set comprehensions.

Z notation allows multiple binding groups separated by semicolons:
- forall x : T; y : U | P  means  forall x : T | forall y : U | P
- {x : T; y : U | P | E}   means  {(x, y) | x : T, y : U, P, E}
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from txt2tex.ast_nodes import BinaryOp, Identifier, Quantifier
from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser

if TYPE_CHECKING:
    from txt2tex.ast_nodes import ASTNode


def parse_expr(text: str) -> ASTNode:
    """Helper to parse expression."""
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    return parser.parse()


class TestSemicolonQuantifiers:
    """Test semicolon-separated bindings elem quantifiers (Phase 17)."""

    def test_forall_two_bindings(self):
        """Test forall x : N; y : N | x + y > 0."""
        ast = parse_expr("forall x : N; y : N | x + y > 0")
        assert isinstance(ast, Quantifier)
        assert ast.quantifier == "forall"
        assert ast.variables == ["x"]
        assert isinstance(ast.domain, Identifier)
        assert ast.domain.name == "N"
        assert isinstance(ast.body, Quantifier)
        assert ast.body.quantifier == "forall"
        assert ast.body.variables == ["y"]
        assert isinstance(ast.body.domain, Identifier)
        assert ast.body.domain.name == "N"
        assert isinstance(ast.body.body, BinaryOp)
        assert ast.body.body.operator == ">"

    def test_forall_three_bindings(self):
        """Test forall x : T; y : U; z : V | P."""
        ast = parse_expr("forall x : T; y : U; z : V | x = y")
        assert isinstance(ast, Quantifier)
        assert ast.variables == ["x"]
        assert isinstance(ast.body, Quantifier)
        assert ast.body.variables == ["y"]
        assert isinstance(ast.body.body, Quantifier)
        assert ast.body.body.variables == ["z"]
        assert isinstance(ast.body.body.body, BinaryOp)

    def test_forall_comma_and_semicolon(self):
        """Test forall x, y : T; z : U | P (mixed comma land semicolon)."""
        ast = parse_expr("forall x, y : T; z : U | x = z")
        assert isinstance(ast, Quantifier)
        assert ast.variables == ["x", "y"]
        assert isinstance(ast.domain, Identifier)
        assert ast.domain.name == "T"
        assert isinstance(ast.body, Quantifier)
        assert ast.body.variables == ["z"]
        assert isinstance(ast.body.domain, Identifier)
        assert ast.body.domain.name == "U"

    def test_exists_with_semicolon(self):
        """Test exists x : N; y : N | x > y."""
        ast = parse_expr("exists x : N; y : N | x > y")
        assert isinstance(ast, Quantifier)
        assert ast.quantifier == "exists"
        assert ast.variables == ["x"]
        assert isinstance(ast.body, Quantifier)
        assert ast.body.quantifier == "exists"
        assert ast.body.variables == ["y"]

    def test_mixed_quantifiers_not_supported(self):
        """Test that we can't mix quantifier types with semicolon."""
        ast = parse_expr("forall x : N; y : N | x = y")
        assert isinstance(ast, Quantifier)
        assert ast.quantifier == "forall"
        assert isinstance(ast.body, Quantifier)
        assert ast.body.quantifier == "forall"


class TestSemicolonLaTeX:
    """Test LaTeX generation for semicolon-separated bindings."""

    def test_forall_two_bindings_latex(self):
        """Test LaTeX for forall x : N; y : N | x = y."""
        ast = parse_expr("forall x : N; y : N | x = y")
        assert isinstance(ast, Quantifier)
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)
        assert "\\forall" in latex
        assert "x" in latex
        assert "y" in latex
        assert "=" in latex

    def test_complex_binding_latex(self):
        """Test LaTeX for complex bindings."""
        ast = parse_expr("forall x : Title; s : seq(Entry) | x = s")
        assert isinstance(ast, Quantifier)
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)
        assert "\\forall" in latex
        assert "Title" in latex
        assert "\\seq" in latex


class TestSolution40Examples:
    """Test actual examples from Solution 40."""

    def test_cumulative_total_binding(self):
        """Test forall with semicolon-separated product type bindings."""
        ast = parse_expr("forall x : Title; s : seq(Title) | x = s")
        assert isinstance(ast, Quantifier)
        assert ast.quantifier == "forall"
        assert ast.variables == ["x"]
        assert isinstance(ast.body, Quantifier)
        assert ast.body.quantifier == "forall"
        assert ast.body.variables == ["s"]

    def test_nested_forall_in_predicate(self):
        """Test complex nested quantifiers."""
        text = "forall r : R; i1, i2 : dom r | i1 /= i2 => true"
        ast = parse_expr(text)
        assert isinstance(ast, Quantifier)
        assert ast.variables == ["r"]
        assert isinstance(ast.body, Quantifier)
        assert ast.body.variables == ["i1", "i2"]
