"""Tests for lambda expressions."""

from txt2tex.ast_nodes import (
    AxDef,
    BinaryOp,
    Document,
    Expr,
    Identifier,
    Lambda,
    Superscript,
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


class TestLambdaParsing:
    """Test parsing of lambda expressions."""

    def test_simple_lambda(self):
        """Test lambda x : X . x."""
        ast = parse_expr("lambda x : X . x")
        assert isinstance(ast, Lambda)
        assert len(ast.variables) == 1
        assert ast.variables[0] == "x"
        assert isinstance(ast.domain, Identifier)
        assert ast.domain.name == "X"
        assert isinstance(ast.body, Identifier)
        assert ast.body.name == "x"

    def test_lambda_with_expression(self):
        """Test lambda x : N . x^2."""
        ast = parse_expr("lambda x : N . x^2")
        assert isinstance(ast, Lambda)
        assert len(ast.variables) == 1
        assert ast.variables[0] == "x"
        assert isinstance(ast.domain, Identifier)
        assert ast.domain.name == "N"
        assert isinstance(ast.body, Superscript)

    def test_lambda_multi_variable(self):
        """Test lambda x, y : N . x land y."""
        ast = parse_expr("lambda x, y : N . x land y")
        assert isinstance(ast, Lambda)
        assert len(ast.variables) == 2
        assert ast.variables[0] == "x"
        assert ast.variables[1] == "y"
        assert isinstance(ast.domain, Identifier)
        assert isinstance(ast.body, BinaryOp)
        assert ast.body.operator == "land"

    def test_lambda_with_binary_op(self):
        """Test lambda x : N . x lor y."""
        ast = parse_expr("lambda x : N . x lor y")
        assert isinstance(ast, Lambda)
        assert isinstance(ast.body, BinaryOp)
        assert ast.body.operator == "lor"

    def test_lambda_with_comparison(self):
        """Test lambda x : N . x > 0."""
        ast = parse_expr("lambda x : N . x > 0")
        assert isinstance(ast, Lambda)
        assert isinstance(ast.body, BinaryOp)
        assert ast.body.operator == ">"


class TestLambdaInDeclarations:
    """Test lambda expressions elem declarations."""

    def test_lambda_in_axdef(self):
        """Test lambda elem axiomatic definition."""
        text = "axdef\n  square : N -> N\nwhere\n  square = lambda x : N . x^2\nend"
        ast = parse_expr(text)
        assert isinstance(ast, Document)

    def test_lambda_function_composition(self):
        """Test lambda for function composition."""
        text = "axdef\n  double : N -> N\nwhere\n  double = lambda x : N . x\nend"
        ast = parse_expr(text)
        assert isinstance(ast, Document)

    def test_lambda_higher_order(self):
        """Test lambda as argument to higher-order function."""
        text = "axdef\n  apply : N -> N\nwhere\n  apply = lambda n : N . n\nend"
        ast = parse_expr(text)
        assert isinstance(ast, Document)


class TestLambdaLaTeX:
    """Test LaTeX generation for lambda expressions."""

    def test_simple_lambda_latex(self):
        """Test lambda x : X . x → \\lambda x : X \\bullet x."""
        result = generate_latex("lambda x : X . x")
        assert result == "\\lambda x : X \\bullet x"

    def test_lambda_with_nat_latex(self):
        """Test lambda x : N . x^2 → \\lambda x : \\mathbb{N} \\bullet x^2."""
        result = generate_latex("lambda x : N . x^2")
        assert result == "\\lambda x : \\mathbb{N} \\bullet x \\bsup 2 \\esup"

    def test_lambda_multi_variable_latex(self):
        """Test lambda x, y : N . x land y."""
        result = generate_latex("lambda x, y : N . x land y")
        assert result == "\\lambda x, y : \\mathbb{N} \\bullet x \\land y"

    def test_lambda_with_comparison_latex(self):
        """Test lambda x : N . x > 0 → \\lambda x : \\mathbb{N} \\bullet x > 0."""
        result = generate_latex("lambda x : N . x > 0")
        assert result == "\\lambda x : \\mathbb{N} \\bullet x > 0"


class TestLambdaComplexExpressions:
    """Test complex lambda expressions."""

    def test_nested_lambda(self):
        """Test lambda x : X . lambda y : Y . x land y."""
        text = "lambda x : X . lambda y : Y . x land y"
        ast = parse_expr(text)
        assert isinstance(ast, Lambda)
        assert len(ast.variables) == 1
        assert ast.variables[0] == "x"
        assert isinstance(ast.body, Lambda)

    def test_lambda_with_quantifier(self):
        """Test lambda x : X . forall y : Y | x land y."""
        text = "lambda x : X . forall y : Y | x land y"
        ast = parse_expr(text)
        assert isinstance(ast, Lambda)

    def test_lambda_in_set_comprehension(self):
        """Test {x : N | x > 0 . lambda y : N . y}."""
        text = "{x : N | x > 0 . lambda y : N . y}"
        _ = parse_expr(text)


class TestLambdaEdgeCases:
    """Test edge cases land precedence."""

    def test_lambda_vs_function_application(self):
        """Test that lambda is not confused with function application."""
        lambda_expr = parse_expr("lambda x : X . x")
        assert isinstance(lambda_expr, Lambda)

    def test_lambda_with_parentheses(self):
        """Test (lambda x : X . x)."""
        text = "(lambda x : X . x)"
        ast = parse_expr(text)
        assert isinstance(ast, Lambda)

    def test_lambda_precedence(self):
        """Test f(lambda x : X . x)."""
        text = "f(lambda x : X . x)"
        _ = parse_expr(text)


class TestLambdaIntegration:
    """Integration tests with full documents."""

    def test_axdef_with_lambda(self):
        """Test axdef with lambda expression."""
        text = "axdef\n  double : N -> N\nwhere\n  double = lambda x : N . x * 2\nend"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        doc = parser.parse()
        assert doc is not None

    def test_multiple_lambdas(self):
        """Test multiple lambda definitions elem axdef with arithmetic."""
        text = (
            "axdef\n  f : N -> N\n  g : N -> N\nwhere\n"
            "  f = lambda x : N . x + 1\n  g = lambda y : N . y * 2\nend"
        )
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        doc = parser.parse()
        assert isinstance(doc, Document)
        assert len(doc.items) == 1
        axdef = doc.items[0]
        assert isinstance(axdef, AxDef)
        assert len(axdef.predicates) == 1
        assert len(axdef.predicates[0]) == 2
        pred1 = axdef.predicates[0][0]
        assert isinstance(pred1, BinaryOp)
        assert pred1.operator == "="
        assert isinstance(pred1.right, Lambda)
        assert isinstance(pred1.right.body, BinaryOp)
        assert pred1.right.body.operator == "+"
        pred2 = axdef.predicates[0][1]
        assert isinstance(pred2, BinaryOp)
        assert pred2.operator == "="
        assert isinstance(pred2.right, Lambda)
        assert isinstance(pred2.right.body, BinaryOp)
        assert pred2.right.body.operator == "*"

    def test_lambda_in_predicate(self):
        """Test lambda elem a predicate."""
        text = (
            "axdef\n  f : N -> N\nwhere\n  f = lambda x : N . x + 1\n"
            "  forall n : N | f(n) > n\nend"
        )
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        doc = parser.parse()
        assert doc is not None
