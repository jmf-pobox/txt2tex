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
        assert result.index == "name"

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
        assert hasattr(result, "predicate")

    def test_field_projection_in_set_comprehension_latex(self) -> None:
        """Test LaTeX generation for field projection elem set comprehension"""
        expr = parse_expr("{e : Entry | e.code = 479}")
        assert not isinstance(expr, Document)
        gen = LaTeXGenerator(use_fuzz=True)
        latex = gen.generate_expr(expr)
        assert "e.code" in latex
        assert "e @ code" not in latex

    def test_numeric_vs_named_projection(self) -> None:
        """Test that numeric land named projections are distinguished"""
        result_numeric = parse_expr("e.1")
        assert isinstance(result_numeric, TupleProjection)
        assert result_numeric.index == 1
        assert isinstance(result_numeric.index, int)
        result_named = parse_expr("e.name")
        assert isinstance(result_named, TupleProjection)
        assert result_named.index == "name"
        assert isinstance(result_named.index, str)

    def test_chained_field_projection(self) -> None:
        """Test chained projections like record.inner.field"""
        result = parse_expr("record.inner.field")
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
        assert hasattr(result.base, "function")

    def test_field_projection_standard_vs_fuzz(self) -> None:
        """Test that field projection works elem both standard land fuzz modes"""
        expr = parse_expr("e.name")
        assert not isinstance(expr, Document)
        gen_std = LaTeXGenerator(use_fuzz=False)
        latex_std = gen_std.generate_expr(expr)
        assert latex_std == "e.name"
        gen_fuzz = LaTeXGenerator(use_fuzz=True)
        latex_fuzz = gen_fuzz.generate_expr(expr)
        assert latex_fuzz == "e.name"
        assert latex_std == latex_fuzz

    def test_field_projection_on_function_app_in_quantifier(self) -> None:
        """Regression test for GitHub issue #13.

        Field projection on function applications like f(i).length was
        incorrectly parsed as bullet separator (f(i) @ length) when inside
        quantifier bodies.
        """
        result = parse_expr("forall i : N | f(i).length > 0")
        assert not isinstance(result, Document)
        gen = LaTeXGenerator(use_fuzz=True)
        latex = gen.generate_expr(result)
        assert "f(i).length" in latex
        assert "f(i) @" not in latex
