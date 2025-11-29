"""Tests for partial functions and function type arrows."""

from txt2tex.ast_nodes import Document, Expr, FunctionType, Identifier
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


class TestPartialFunctionParsing:
    """Test parsing of function type arrows."""

    def test_total_function(self):
        """Test X -> Y."""
        ast = parse_expr("X -> Y")
        assert isinstance(ast, FunctionType)
        assert ast.arrow == "->"
        assert isinstance(ast.domain, Identifier)
        assert ast.domain.name == "X"
        assert isinstance(ast.range, Identifier)
        assert ast.range.name == "Y"

    def test_partial_function(self):
        """Test X +-> Y."""
        ast = parse_expr("X +-> Y")
        assert isinstance(ast, FunctionType)
        assert ast.arrow == "+->"
        assert isinstance(ast.domain, Identifier)
        assert isinstance(ast.range, Identifier)

    def test_total_injection(self):
        """Test X >-> Y."""
        ast = parse_expr("X >-> Y")
        assert isinstance(ast, FunctionType)
        assert ast.arrow == ">->"
        assert isinstance(ast.domain, Identifier)
        assert isinstance(ast.range, Identifier)

    def test_partial_injection(self):
        """Test X >+> Y."""
        ast = parse_expr("X >+> Y")
        assert isinstance(ast, FunctionType)
        assert ast.arrow == ">+>"
        assert isinstance(ast.domain, Identifier)
        assert isinstance(ast.range, Identifier)

    def test_total_surjection(self):
        """Test X -->> Y."""
        ast = parse_expr("X -->> Y")
        assert isinstance(ast, FunctionType)
        assert ast.arrow == "-->>"
        assert isinstance(ast.domain, Identifier)
        assert isinstance(ast.range, Identifier)

    def test_partial_surjection(self):
        """Test X +->> Y."""
        ast = parse_expr("X +->> Y")
        assert isinstance(ast, FunctionType)
        assert ast.arrow == "+->>"
        assert isinstance(ast.domain, Identifier)
        assert isinstance(ast.range, Identifier)

    def test_bijection(self):
        """Test X >->> Y."""
        ast = parse_expr("X >->> Y")
        assert isinstance(ast, FunctionType)
        assert ast.arrow == ">->>"
        assert isinstance(ast.domain, Identifier)
        assert isinstance(ast.range, Identifier)


class TestPartialFunctionInDeclarations:
    """Test function types elem declarations."""

    def test_simple_function_declaration(self):
        """Test f : X -> Y."""
        text = "axdef\n  f : X -> Y\nend"
        ast = parse_expr(text)
        assert isinstance(ast, Document)

    def test_function_to_set(self):
        """Test children : Person -> P(Person)."""
        text = "axdef\n  children : Person -> P(Person)\nend"
        ast = parse_expr(text)
        assert isinstance(ast, Document)

    def test_complex_function_type(self):
        """Test f : (Drivers <-> Cars) -> (Cars -> N)."""
        text = "axdef\n  f : (Drivers <-> Cars) -> (Cars -> N)\nend"
        ast = parse_expr(text)
        assert isinstance(ast, Document)


class TestPartialFunctionLaTeX:
    """Test LaTeX generation for function arrows."""

    def test_total_function_latex(self):
        """Test X -> Y → X \\fun Y."""
        result = generate_latex("X -> Y")
        assert result == "X \\fun Y"

    def test_partial_function_latex(self):
        """Test X +-> Y → X \\pfun Y."""
        result = generate_latex("X +-> Y")
        assert result == "X \\pfun Y"

    def test_total_injection_latex(self):
        """Test X >-> Y → X \\inj Y."""
        result = generate_latex("X >-> Y")
        assert result == "X \\inj Y"

    def test_partial_injection_latex(self):
        """Test X >+> Y → X \\pinj Y."""
        result = generate_latex("X >+> Y")
        assert result == "X \\pinj Y"

    def test_total_surjection_latex(self):
        """Test X -->> Y → X \\surj Y."""
        result = generate_latex("X -->> Y")
        assert result == "X \\surj Y"

    def test_partial_surjection_latex(self):
        """Test X +->> Y → X \\psurj Y."""
        result = generate_latex("X +->> Y")
        assert result == "X \\psurj Y"

    def test_bijection_latex(self):
        """Test X >->> Y → X \\bij Y."""
        result = generate_latex("X >->> Y")
        assert result == "X \\bij Y"


class TestPartialFunctionComplexTypes:
    """Test complex function type expressions."""

    def test_function_composition_type(self):
        """Test (X -> Y) -> (Y -> Z) -> (X -> Z)."""
        text = "(X -> Y) -> (Y -> Z) -> (X -> Z)"
        ast = parse_expr(text)
        assert isinstance(ast, FunctionType)
        assert isinstance(ast.domain, FunctionType)

    def test_higher_order_function(self):
        """Test (N -> N) -> N."""
        text = "(N -> N) -> N"
        ast = parse_expr(text)
        assert isinstance(ast, FunctionType)
        assert isinstance(ast.domain, FunctionType)
        assert isinstance(ast.range, Identifier)

    def test_curried_function(self):
        """Test X -> Y -> Z (right-associative)."""
        text = "X -> Y -> Z"
        ast = parse_expr(text)
        assert isinstance(ast, FunctionType)
        assert isinstance(ast.domain, Identifier)
        assert ast.domain.name == "X"
        assert isinstance(ast.range, FunctionType)


class TestPartialFunctionEdgeCases:
    """Test edge cases land precedence."""

    def test_arrow_vs_relation(self):
        """Test that -> is parsed as function, lnot relation arrow."""
        func = parse_expr("X -> Y")
        assert isinstance(func, FunctionType)
        assert func.arrow == "->"

    def test_multiple_arrows_associativity(self):
        """Test A -> B -> C is right-associative."""
        ast = parse_expr("A -> B -> C")
        assert isinstance(ast, FunctionType)
        assert isinstance(ast.domain, Identifier)
        assert ast.domain.name == "A"
        assert isinstance(ast.range, FunctionType)
        assert isinstance(ast.range.domain, Identifier)
        assert ast.range.domain.name == "B"
        assert isinstance(ast.range.range, Identifier)
        assert ast.range.range.name == "C"

    def test_parenthesized_function_type(self):
        """Test (A -> B) -> C is left-associative."""
        ast = parse_expr("(A -> B) -> C")
        assert isinstance(ast, FunctionType)
        assert isinstance(ast.domain, FunctionType)
        assert isinstance(ast.domain.domain, Identifier)
        assert ast.domain.domain.name == "A"
        assert isinstance(ast.domain.range, Identifier)
        assert ast.domain.range.name == "B"
        assert isinstance(ast.range, Identifier)
        assert ast.range.name == "C"


class TestPartialFunctionIntegration:
    """Integration tests with full documents."""

    def test_axdef_with_function_type(self):
        """Test axdef with function type declaration."""
        text = (
            "axdef\n  square : N -> N\nwhere\n  forall n : N | square(n) = n * n\nend"
        )
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        doc = parser.parse()
        assert doc is not None

    def test_multiple_function_types(self):
        """Test multiple function declarations."""
        text = (
            "axdef\n  f : X -> Y\n  g : Y -> Z\n  h : X -> Z\n"
            "where\n  forall x : X | h(x) = g(f(x))\nend"
        )
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        doc = parser.parse()
        assert doc is not None

    def test_schema_with_function_type(self):
        """Test schema with function type."""
        text = (
            "schema State\n  items : seq(N)\n  lookup : N -> Item\n"
            "where\n  dom(lookup) = ran(items)\nend"
        )
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        doc = parser.parse()
        assert doc is not None
