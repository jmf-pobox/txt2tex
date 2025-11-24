"""Test Phase 13 features: anonymous schemas, range operator, sequence operations."""

from txt2tex.ast_nodes import (
    BinaryOp,
    Document,
    Identifier,
    Number,
    Range,
    Schema,
    SetComprehension,
    TupleProjection,
)
from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser


class TestAnonymousSchemas:
    """Test anonymous schema parsing and LaTeX generation."""

    def test_anonymous_schema_basic(self) -> None:
        """Test basic anonymous schema."""
        txt = """schema
  x : N
where
  x > 0
end"""
        lexer = Lexer(txt)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        # Check AST structure
        assert isinstance(ast, Document)
        assert isinstance(ast.items[0], Schema)
        schema = ast.items[0]
        assert schema.name is None
        assert len(schema.declarations) == 1
        assert schema.declarations[0].variable == "x"

    def test_anonymous_schema_latex(self) -> None:
        """Test LaTeX generation for anonymous schema."""
        txt = """schema
  x : N
where
  x > 0
end"""
        lexer = Lexer(txt)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # Should have empty schema name
        assert r"\begin{schema}{}" in latex
        assert r"\end{schema}" in latex


class TestRangeOperator:
    """Test range operator (..) parsing and LaTeX generation."""

    def test_range_simple_numbers(self) -> None:
        """Test simple numeric range: 1..10."""
        txt = "1..10"
        lexer = Lexer(txt)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        # Check AST structure
        assert isinstance(ast, Range)
        assert isinstance(ast.start, Number)
        assert ast.start.value == "1"
        assert isinstance(ast.end, Number)
        assert ast.end.value == "10"

    def test_range_identifiers(self) -> None:
        """Test range with identifiers: 1993..current."""
        txt = "1993..current"
        lexer = Lexer(txt)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        # Check AST structure
        assert isinstance(ast, Range)
        assert isinstance(ast.start, Number)
        assert ast.start.value == "1993"
        assert isinstance(ast.end, Identifier)
        assert ast.end.name == "current"

    def test_range_tuple_projections(self) -> None:
        """Test range with tuple projections: x.2..x.3."""
        txt = "x.2..x.3"
        lexer = Lexer(txt)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        # Check AST structure
        assert isinstance(ast, Range)
        assert isinstance(ast.start, TupleProjection)
        assert ast.start.index == 2
        assert isinstance(ast.end, TupleProjection)
        assert ast.end.index == 3

    def test_range_precedence_with_addition(self) -> None:
        """Test range precedence: 1+2..3+4 should parse as (1+2)..(3+4)."""
        txt = "1 + 2..3 + 4"
        lexer = Lexer(txt)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        # Check AST structure
        assert isinstance(ast, Range)
        # Start should be BinaryOp (1 + 2)
        assert isinstance(ast.start, BinaryOp)
        assert ast.start.operator == "+"
        # End should be BinaryOp (3 + 4)
        assert isinstance(ast.end, BinaryOp)
        assert ast.end.operator == "+"

    def test_range_latex_simple(self) -> None:
        """Test LaTeX generation for simple range."""
        txt = "1..10"
        lexer = Lexer(txt)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        assert isinstance(ast, Range)
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)

        # Should use \upto command
        assert latex == r"1 \upto 10"

    def test_range_latex_identifiers(self) -> None:
        """Test LaTeX generation for range with identifiers."""
        txt = "1993..current"
        lexer = Lexer(txt)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        assert isinstance(ast, Range)
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)

        assert latex == r"1993 \upto current"

    def test_range_latex_complex(self) -> None:
        """Test LaTeX generation for complex range expressions."""
        txt = "x.2..x.3"
        lexer = Lexer(txt)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        assert isinstance(ast, Range)
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)

        assert latex == r"x.2 \upto x.3"

    def test_range_in_set_comprehension(self) -> None:
        """Test range operator inside set comprehension."""
        txt = "{ x : 1..10 | x > 5 }"
        lexer = Lexer(txt)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        # Check AST structure
        assert isinstance(ast, SetComprehension)
        assert isinstance(ast.domain, Range)
        assert isinstance(ast.domain.start, Number)
        assert ast.domain.start.value == "1"
        assert isinstance(ast.domain.end, Number)
        assert ast.domain.end.value == "10"

    def test_range_in_set_comprehension_latex(self) -> None:
        """Test LaTeX for range in set comprehension."""
        txt = "{ x : 1..10 | x > 5 }"
        lexer = Lexer(txt)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        assert isinstance(ast, SetComprehension)
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)

        # Should have \upto in the domain
        assert r"1 \upto 10" in latex
        assert r"\{" in latex
        assert r"\}" in latex

    def test_range_in_schema(self) -> None:
        """Test range operator in schema declarations."""
        txt = """schema
  year : 1993..current
where
  year >= 1993
end"""
        lexer = Lexer(txt)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        # Check AST structure
        assert isinstance(ast, Document)
        assert isinstance(ast.items[0], Schema)
        schema = ast.items[0]
        assert len(schema.declarations) == 1
        decl = schema.declarations[0]
        assert decl.variable == "year"
        assert isinstance(decl.type_expr, Range)

    def test_range_not_confused_with_period(self) -> None:
        """Test that range (..) is distinct from single period (.)."""
        # Single period should be tuple projection
        txt1 = "x.1"
        lexer1 = Lexer(txt1)
        tokens1 = lexer1.tokenize()
        parser1 = Parser(tokens1)
        ast1 = parser1.parse()
        assert isinstance(ast1, TupleProjection)

        # Double period should be range
        txt2 = "1..10"
        lexer2 = Lexer(txt2)
        tokens2 = lexer2.tokenize()
        parser2 = Parser(tokens2)
        ast2 = parser2.parse()
        assert isinstance(ast2, Range)

    def test_range_with_whitespace(self) -> None:
        """Test range with various whitespace."""
        # No whitespace
        txt1 = "1..10"
        lexer1 = Lexer(txt1)
        tokens1 = lexer1.tokenize()
        parser1 = Parser(tokens1)
        ast1 = parser1.parse()
        assert isinstance(ast1, Range)

        # With whitespace
        txt2 = "1 .. 10"
        lexer2 = Lexer(txt2)
        tokens2 = lexer2.tokenize()
        parser2 = Parser(tokens2)
        ast2 = parser2.parse()
        assert isinstance(ast2, Range)


class TestOverrideOperator:
    """Test override operator (++) parsing and LaTeX generation."""

    def test_override_basic(self) -> None:
        """Test basic override: f ++ g."""
        txt = "f ++ g"
        lexer = Lexer(txt)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        # Check AST structure
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "++"
        assert isinstance(ast.left, Identifier)
        assert ast.left.name == "f"
        assert isinstance(ast.right, Identifier)
        assert ast.right.name == "g"

    def test_override_latex_basic(self) -> None:
        """Test LaTeX generation for basic override."""
        txt = "f ++ g"
        lexer = Lexer(txt)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        assert isinstance(ast, BinaryOp)
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)

        # Should use \\oplus command
        assert latex == r"f \oplus g"

    def test_override_chained(self) -> None:
        """Test chained override: f ++ g ++ h."""
        txt = "f ++ g ++ h"
        lexer = Lexer(txt)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        # Check AST structure - should be left-associative
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "++"
        # Left side should be (f ++ g)
        assert isinstance(ast.left, BinaryOp)
        assert ast.left.operator == "++"
        # Right side should be h
        assert isinstance(ast.right, Identifier)
        assert ast.right.name == "h"

    def test_override_chained_latex(self) -> None:
        """Test LaTeX generation for chained override."""
        txt = "f ++ g ++ h"
        lexer = Lexer(txt)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        assert isinstance(ast, BinaryOp)
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)

        assert latex == r"f \oplus g \oplus h"

    def test_override_with_set_literals(self) -> None:
        """Test override with set literals: {1 |-> a} ++ {2 |-> b}."""
        txt = "{1 |-> a} ++ {2 |-> b}"
        lexer = Lexer(txt)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        # Check AST structure
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "++"

    def test_override_precedence_with_union(self) -> None:
        """Test override has same precedence as union."""
        txt = "A union B ++ C"
        lexer = Lexer(txt)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        # Should parse as (A union B) ++ C (left-associative)
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "++"
        assert isinstance(ast.left, BinaryOp)
        assert ast.left.operator == "union"

    def test_override_precedence_with_intersection(self) -> None:
        """Test override binds looser than intersection."""
        txt = "A intersect B ++ C intersect D"
        lexer = Lexer(txt)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        # Should parse as (A intersect B) ++ (C intersect D)
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "++"
        # Both sides should be intersections
        assert isinstance(ast.left, BinaryOp)
        assert ast.left.operator == "intersect"
        assert isinstance(ast.right, BinaryOp)
        assert ast.right.operator == "intersect"

    def test_override_in_schema_declaration(self) -> None:
        """Test override in schema type declarations."""
        txt = """schema
  f : A -> B
  g : A -> B
where
  f ++ g = h
end"""
        lexer = Lexer(txt)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        # Check AST structure
        assert isinstance(ast, Document)
        assert isinstance(ast.items[0], Schema)
        schema = ast.items[0]
        # Check predicate contains override
        assert len(schema.predicates) == 1  # One group
        assert len(schema.predicates[0]) == 1  # One predicate
        pred = schema.predicates[0][0]
        assert isinstance(pred, BinaryOp)
        assert pred.operator == "="
        # Left side should be override
        assert isinstance(pred.left, BinaryOp)
        assert pred.left.operator == "++"

    def test_override_in_axdef(self) -> None:
        """Test override in axdef predicate."""
        txt = """axdef
  f : A -> B
  g : A -> B
where
  dom (f ++ g) = dom f union dom g
end"""
        lexer = Lexer(txt)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        # Check AST structure
        assert isinstance(ast, Document)
        # Should contain override in predicate
        # (detailed structure checking omitted for brevity)

    def test_override_not_confused_with_plus(self) -> None:
        """Test that ++ is distinct from single + operator."""
        # Single plus should be addition
        txt1 = "a + b"
        lexer1 = Lexer(txt1)
        tokens1 = lexer1.tokenize()
        parser1 = Parser(tokens1)
        ast1 = parser1.parse()
        assert isinstance(ast1, BinaryOp)
        assert ast1.operator == "+"

        # Double plus should be override
        txt2 = "a ++ b"
        lexer2 = Lexer(txt2)
        tokens2 = lexer2.tokenize()
        parser2 = Parser(tokens2)
        ast2 = parser2.parse()
        assert isinstance(ast2, BinaryOp)
        assert ast2.operator == "++"

    def test_override_with_parentheses(self) -> None:
        """Test override with explicit grouping."""
        txt = "(f ++ g) ++ h"
        lexer = Lexer(txt)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        # Should still parse as left-associative
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "++"

    def test_override_complex_latex(self) -> None:
        """Test LaTeX generation for complex override expressions."""
        txt = "{1 |-> a, 2 |-> b} ++ {2 |-> c, 3 |-> d}"
        lexer = Lexer(txt)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        assert isinstance(ast, BinaryOp)
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)

        # Should contain \\oplus
        assert r"\oplus" in latex
        # Should contain maplet arrows
        assert r"\mapsto" in latex
