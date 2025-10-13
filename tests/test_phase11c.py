"""Tests for Phase 11c: Function Types (Arrows)."""

from txt2tex.ast_nodes import (
    Document,
    Expr,
    FunctionType,
    Identifier,
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
    # For single expressions, parser returns the expression directly
    assert not isinstance(ast, Document)
    generator = LaTeXGenerator()
    return generator.generate_expr(ast)


class TestPhase11cParsing:
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


class TestPhase11cInDeclarations:
    """Test function types in declarations."""

    def test_simple_function_declaration(self):
        """Test f : X -> Y."""
        text = """axdef
  f : X -> Y
end"""
        ast = parse_expr(text)
        assert isinstance(ast, Document)
        # Check that the declaration contains a function type
        # This will depend on how declarations are parsed

    def test_function_to_set(self):
        """Test children : Person -> P(Person)."""
        text = """axdef
  children : Person -> P(Person)
end"""
        ast = parse_expr(text)
        assert isinstance(ast, Document)

    def test_complex_function_type(self):
        """Test f : (Drivers <-> Cars) -> (Cars -> N)."""
        # This is a function from relations to functions
        # May require careful precedence handling
        text = """axdef
  f : (Drivers <-> Cars) -> (Cars -> N)
end"""
        ast = parse_expr(text)
        assert isinstance(ast, Document)


class TestPhase11cLaTeX:
    """Test LaTeX generation for function arrows."""

    def test_total_function_latex(self):
        """Test X -> Y → X \\fun Y."""
        result = generate_latex("X -> Y")
        assert result == r"X \fun Y"

    def test_partial_function_latex(self):
        """Test X +-> Y → X \\pfun Y."""
        result = generate_latex("X +-> Y")
        assert result == r"X \pfun Y"

    def test_total_injection_latex(self):
        """Test X >-> Y → X \\inj Y."""
        result = generate_latex("X >-> Y")
        assert result == r"X \inj Y"

    def test_partial_injection_latex(self):
        """Test X >+> Y → X \\pinj Y."""
        result = generate_latex("X >+> Y")
        assert result == r"X \pinj Y"

    def test_total_surjection_latex(self):
        """Test X -->> Y → X \\surj Y."""
        result = generate_latex("X -->> Y")
        assert result == r"X \surj Y"

    def test_partial_surjection_latex(self):
        """Test X +->> Y → X \\psurj Y."""
        result = generate_latex("X +->> Y")
        assert result == r"X \psurj Y"

    def test_bijection_latex(self):
        """Test X >->> Y → X \\bij Y."""
        result = generate_latex("X >->> Y")
        assert result == r"X \bij Y"


class TestPhase11cComplexTypes:
    """Test complex function type expressions."""

    def test_function_composition_type(self):
        """Test (X -> Y) -> (Y -> Z) -> (X -> Z)."""
        # Type of function composition operator
        text = "(X -> Y) -> (Y -> Z) -> (X -> Z)"
        ast = parse_expr(text)
        assert isinstance(ast, FunctionType)
        # Left side should be X -> Y
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
        # Should parse as X -> (Y -> Z)
        assert isinstance(ast.domain, Identifier)
        assert ast.domain.name == "X"
        assert isinstance(ast.range, FunctionType)


class TestPhase11cEdgeCases:
    """Test edge cases and precedence."""

    def test_arrow_vs_relation(self):
        """Test that -> is parsed as function, not relation arrow."""
        # X <-> Y is a relation
        # X -> Y is a function
        func = parse_expr("X -> Y")
        assert isinstance(func, FunctionType)
        assert func.arrow == "->"
        # Relation arrows are parsed as BinaryOp (different from FunctionType)

    def test_multiple_arrows_associativity(self):
        """Test A -> B -> C is right-associative."""
        ast = parse_expr("A -> B -> C")
        assert isinstance(ast, FunctionType)
        # Should be A -> (B -> C)
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
        # Should be (A -> B) -> C
        assert isinstance(ast.domain, FunctionType)
        assert isinstance(ast.domain.domain, Identifier)
        assert ast.domain.domain.name == "A"
        assert isinstance(ast.domain.range, Identifier)
        assert ast.domain.range.name == "B"
        assert isinstance(ast.range, Identifier)
        assert ast.range.name == "C"


class TestPhase11cIntegration:
    """Integration tests with full documents."""

    def test_axdef_with_function_type(self):
        """Test axdef with function type declaration."""
        text = """axdef
  square : N -> N
where
  forall n : N | square(n) = n * n
end"""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        doc = parser.parse()
        assert doc is not None

    def test_multiple_function_types(self):
        """Test multiple function declarations."""
        text = """axdef
  f : X -> Y
  g : Y -> Z
  h : X -> Z
where
  forall x : X | h(x) = g(f(x))
end"""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        doc = parser.parse()
        assert doc is not None

    def test_schema_with_function_type(self):
        """Test schema with function type."""
        text = """schema State
  items : seq(N)
  lookup : N -> Item
where
  dom(lookup) = ran(items)
end"""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        doc = parser.parse()
        assert doc is not None
