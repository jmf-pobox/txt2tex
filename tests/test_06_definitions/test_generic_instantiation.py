"""Tests for generic type instantiation (Phase 11.9)."""

from __future__ import annotations

from txt2tex.ast_nodes import (
    BinaryOp,
    Document,
    GenericInstantiation,
    Identifier,
)
from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser


class TestGenericInstantiationParser:
    """Test parsing generic type instantiation."""

    def test_simple_generic_instantiation(self) -> None:
        """Test simple generic instantiation: Type[N]."""
        lexer = Lexer("Type[N]")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        result = parser.parse()

        assert isinstance(result, GenericInstantiation)
        assert isinstance(result.base, Identifier)
        assert result.base.name == "Type"
        assert len(result.type_params) == 1
        param0 = result.type_params[0]
        assert isinstance(param0, Identifier)
        assert param0.name == "N"

    def test_multi_param_generic_instantiation(self) -> None:
        """Test multiple type parameters: Type[A, B, C]."""
        lexer = Lexer("Type[A, B, C]")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        result = parser.parse()

        assert isinstance(result, GenericInstantiation)
        assert isinstance(result.base, Identifier)
        assert result.base.name == "Type"
        assert len(result.type_params) == 3
        assert all(isinstance(param, Identifier) for param in result.type_params)
        param0 = result.type_params[0]
        param1 = result.type_params[1]
        param2 = result.type_params[2]
        assert isinstance(param0, Identifier)
        assert isinstance(param1, Identifier)
        assert isinstance(param2, Identifier)
        assert param0.name == "A"
        assert param1.name == "B"
        assert param2.name == "C"

    def test_generic_with_complex_type_param(self) -> None:
        """Test complex type parameter: Type[N cross N]."""
        lexer = Lexer("Type[N cross N]")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        result = parser.parse()

        assert isinstance(result, GenericInstantiation)
        assert isinstance(result.base, Identifier)
        assert result.base.name == "Type"
        assert len(result.type_params) == 1
        param0 = result.type_params[0]
        assert isinstance(param0, BinaryOp)
        assert param0.operator == "cross"

    def test_empty_set_generic(self) -> None:
        """Test empty set with type parameter: emptyset[N]."""
        lexer = Lexer("emptyset[N]")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        result = parser.parse()

        assert isinstance(result, GenericInstantiation)
        assert isinstance(result.base, Identifier)
        assert result.base.name == "emptyset"
        assert len(result.type_params) == 1
        param0 = result.type_params[0]
        assert isinstance(param0, Identifier)
        assert param0.name == "N"

    def test_seq_generic(self) -> None:
        """Test sequence with type parameter: seq[N]."""
        lexer = Lexer("seq[N]")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        result = parser.parse()

        assert isinstance(result, GenericInstantiation)
        assert isinstance(result.base, Identifier)
        assert result.base.name == "seq"
        assert len(result.type_params) == 1

    def test_power_set_generic(self) -> None:
        """Test power set with type parameter: P[X]."""
        lexer = Lexer("P[X]")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        result = parser.parse()

        assert isinstance(result, GenericInstantiation)
        # P might be parsed as prefix operator or identifier
        # Check either case
        assert len(result.type_params) == 1
        param0 = result.type_params[0]
        assert isinstance(param0, Identifier)
        assert param0.name == "X"

    def test_nested_generic_instantiation(self) -> None:
        """Test nested generic: Type[List[N]]."""
        lexer = Lexer("Type[List[N]]")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        result = parser.parse()

        assert isinstance(result, GenericInstantiation)
        assert isinstance(result.base, Identifier)
        assert result.base.name == "Type"
        assert len(result.type_params) == 1
        param0 = result.type_params[0]
        assert isinstance(param0, GenericInstantiation)
        nested_base = param0.base
        assert isinstance(nested_base, Identifier)
        assert nested_base.name == "List"

    def test_chained_generic_instantiation(self) -> None:
        """Test chained generic: Type[N][M] (should parse as (Type[N])[M])."""
        lexer = Lexer("Type[N][M]")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        result = parser.parse()

        # Should parse as (Type[N])[M] due to left-to-right postfix
        assert isinstance(result, GenericInstantiation)
        outer_base = result.base
        assert isinstance(outer_base, GenericInstantiation)
        inner_base = outer_base.base
        assert isinstance(inner_base, Identifier)
        assert inner_base.name == "Type"
        inner_param0 = outer_base.type_params[0]
        assert isinstance(inner_param0, Identifier)
        assert inner_param0.name == "N"
        outer_param0 = result.type_params[0]
        assert isinstance(outer_param0, Identifier)
        assert outer_param0.name == "M"


class TestGenericInstantiationLatex:
    """Test LaTeX generation for generic instantiation."""

    def test_simple_generic_latex(self) -> None:
        """Test LaTeX for simple generic: Type[N] -> Type[N]."""
        lexer = Lexer("Type[N]")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert not isinstance(ast, Document)
        generator = LaTeXGenerator()
        latex = generator.generate_expr(ast)

        assert latex == "Type[\\mathbb{N}]"

    def test_multi_param_generic_latex(self) -> None:
        """Test LaTeX for multi-param: Type[A, B, C] -> Type[A, B, C]."""
        lexer = Lexer("Type[A, B, C]")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert not isinstance(ast, Document)
        generator = LaTeXGenerator()
        latex = generator.generate_expr(ast)

        assert latex == "Type[A, B, C]"

    def test_complex_type_param_latex(self) -> None:
        """Test LaTeX for complex param: Type[N cross N] -> Type[N x N]."""
        lexer = Lexer("Type[N cross N]")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert not isinstance(ast, Document)
        generator = LaTeXGenerator()
        latex = generator.generate_expr(ast)

        assert latex == r"Type[\mathbb{N} \cross \mathbb{N}]"

    def test_seq_generic_latex(self) -> None:
        """Test LaTeX for seq[N] -> \\seq \\mathbb{N} (no brackets)."""
        lexer = Lexer("seq[N]")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert not isinstance(ast, Document)
        generator = LaTeXGenerator()
        latex = generator.generate_expr(ast)

        # seq[N] with single param renders as \seq \mathbb{N} (no brackets)
        assert "seq" in latex
        assert "N" in latex
        assert "[" not in latex  # No brackets for special Z notation types
        assert latex == "\\seq \\mathbb{N}"

    def test_nested_generic_latex(self) -> None:
        """Test LaTeX for nested: Type[List[N]] -> Type[List[\\mathbb{N}]]."""
        lexer = Lexer("Type[List[N]]")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert not isinstance(ast, Document)
        generator = LaTeXGenerator()
        latex = generator.generate_expr(ast)

        assert latex == "Type[List[\\mathbb{N}]]"


class TestGenericInstantiationEdgeCases:
    """Test edge cases for generic instantiation."""

    def test_generic_in_expression(self) -> None:
        """Test generic within larger expression: x elem Type[N]."""
        lexer = Lexer("x elem Type[N]")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        result = parser.parse()

        assert isinstance(result, BinaryOp)
        assert result.operator == "elem"
        assert isinstance(result.left, Identifier)
        right = result.right
        assert isinstance(right, GenericInstantiation)
        right_base = right.base
        assert isinstance(right_base, Identifier)
        assert right_base.name == "Type"

    def test_generic_with_trailing_comma(self) -> None:
        """Test trailing comma: Type[A,] -> Type[A]."""
        lexer = Lexer("Type[A,]")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        result = parser.parse()

        assert isinstance(result, GenericInstantiation)
        assert len(result.type_params) == 1
        param0 = result.type_params[0]
        assert isinstance(param0, Identifier)
        assert param0.name == "A"

    def test_generic_vs_subscript(self) -> None:
        """Test underscore vs brackets: a_1 is identifier, a[1] generic (Phase 15)."""
        # Subscript (Phase 15: now just identifier with underscore)
        lexer = Lexer("a_1")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        result = parser.parse()

        assert isinstance(result, Identifier)
        assert result.name == "a_1"

        # Generic
        lexer = Lexer("a[1]")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        result = parser.parse()

        assert isinstance(result, GenericInstantiation)
