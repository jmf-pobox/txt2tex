"""Tests for named field projection (e.fieldname) feature.

This tests the fix for the parser bug where e.fieldname was incorrectly
generating e @ fieldname instead of e.fieldname.
"""

from txt2tex.ast_nodes import Document, Expr, Identifier, TupleProjection
from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser


def parse_expr(text: str) -> Expr | Document:
    """Helper to parse expression."""
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    return parser.parse()


class TestNamedFieldProjection:
    """Test named field projection: e.name, record.status, etc."""

    def test_simple_field_projection(self) -> None:
        """Test simple field projection: e.name"""
        result = parse_expr("e.name")

        assert isinstance(result, TupleProjection)
        assert isinstance(result.base, Identifier)
        assert result.base.name == "e"
        assert result.index == "name"  # Field name as string

    def test_field_projection_latex(self) -> None:
        """Test LaTeX generation for field projection"""
        expr = parse_expr("e.name")
        assert not isinstance(expr, Document)
        gen = LaTeXGenerator(use_fuzz=True)
        latex = gen.generate_expr(expr)

        assert latex == "e.name"

    def test_multiple_fields(self) -> None:
        """Test different field names"""
        test_cases = [
            ("record.status", "record", "status"),
            ("person.age", "person", "age"),
            ("entry.course", "entry", "course"),
            ("x.field", "x", "field"),
        ]

        for input_text, expected_base, expected_field in test_cases:
            result = parse_expr(input_text)

            assert isinstance(result, TupleProjection)
            assert isinstance(result.base, Identifier)
            assert result.base.name == expected_base
            assert result.index == expected_field

    def test_field_projection_in_set_comprehension(self) -> None:
        """Test field projection inside set comprehension"""
        result = parse_expr("{e : Entry | e.code = 479}")

        # The set comprehension body should contain a comparison
        # with e.code on the left side
        assert hasattr(result, "predicate")

    def test_field_projection_in_set_comprehension_latex(self) -> None:
        """Test LaTeX generation for field projection in set comprehension"""
        expr = parse_expr("{e : Entry | e.code = 479}")
        assert not isinstance(expr, Document)
        gen = LaTeXGenerator(use_fuzz=True)
        latex = gen.generate_expr(expr)

        # Should generate valid LaTeX with e.code (not e @ code)
        assert "e.code" in latex
        assert "e @ code" not in latex

    def test_numeric_vs_named_projection(self) -> None:
        """Test that numeric and named projections are distinguished"""
        # Numeric projection
        result_numeric = parse_expr("e.1")
        assert isinstance(result_numeric, TupleProjection)
        assert result_numeric.index == 1  # Integer
        assert isinstance(result_numeric.index, int)

        # Named projection
        result_named = parse_expr("e.name")
        assert isinstance(result_named, TupleProjection)
        assert result_named.index == "name"  # String
        assert isinstance(result_named.index, str)

    def test_chained_field_projection(self) -> None:
        """Test chained projections like record.inner.field"""
        result = parse_expr("record.inner.field")

        # Should parse as (record.inner).field
        assert isinstance(result, TupleProjection)
        assert result.index == "field"
        assert isinstance(result.base, TupleProjection)
        assert result.base.index == "inner"
        assert isinstance(result.base.base, Identifier)
        assert result.base.base.name == "record"

    def test_field_projection_with_function_app(self) -> None:
        """Test projection on function application: f(x).name"""
        result = parse_expr("f(x).status")

        assert isinstance(result, TupleProjection)
        assert result.index == "status"
        # base should be a FunctionApp
        assert hasattr(result.base, "function")

    def test_field_projection_standard_vs_fuzz(self) -> None:
        """Test that field projection works in both standard and fuzz modes"""
        expr = parse_expr("e.name")
        assert not isinstance(expr, Document)

        # Standard mode
        gen_std = LaTeXGenerator(use_fuzz=False)
        latex_std = gen_std.generate_expr(expr)
        assert latex_std == "e.name"

        # Fuzz mode
        gen_fuzz = LaTeXGenerator(use_fuzz=True)
        latex_fuzz = gen_fuzz.generate_expr(expr)
        assert latex_fuzz == "e.name"

        # Should be identical (works in both modes)
        assert latex_std == latex_fuzz

    def test_field_projection_on_function_app_in_quantifier(self) -> None:
        """Regression test for GitHub issue #13.

        Field projection on function applications like f(i).length was
        incorrectly parsed as bullet separator (f(i) @ length) when inside
        quantifier bodies.
        """
        # Test the specific case from the bug report
        result = parse_expr("forall i : N | f(i).length > 0")

        # The body should contain f(i).length, not f(i) @ length
        assert not isinstance(result, Document)
        gen = LaTeXGenerator(use_fuzz=True)
        latex = gen.generate_expr(result)

        # Should have proper field projection
        assert "f(i).length" in latex
        # Should NOT have bullet separator where field projection should be
        assert "f(i) @" not in latex
