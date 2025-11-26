"""Tests for relational image (Phase 11.8)."""

from __future__ import annotations

from txt2tex.ast_nodes import BinaryOp, Identifier, RelationalImage, SetLiteral, UnaryOp
from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser


class TestRelationalImageParser:
    """Test parsing of relational image expressions."""

    def test_simple_relational_image(self) -> None:
        """Test parsing simple relational image R(| S |)."""
        tokens = Lexer("R(| S |)").tokenize()
        ast = Parser(tokens).parse()
        assert isinstance(ast, RelationalImage)
        assert isinstance(ast.relation, Identifier)
        assert ast.relation.name == "R"
        assert isinstance(ast.set, Identifier)
        assert ast.set.name == "S"

    def test_relational_image_with_set_literal(self) -> None:
        """Test relational image with set literal R(| {1, 2} |)."""
        tokens = Lexer("R(| {1, 2} |)").tokenize()
        ast = Parser(tokens).parse()
        assert isinstance(ast, RelationalImage)
        assert isinstance(ast.relation, Identifier)
        assert ast.relation.name == "R"
        assert isinstance(ast.set, SetLiteral)
        assert len(ast.set.elements) == 2

    def test_relational_image_with_singleton_set(self) -> None:
        """Test relational image with singleton set parentOf(| {john} |)."""
        tokens = Lexer("parentOf(| {john} |)").tokenize()
        ast = Parser(tokens).parse()
        assert isinstance(ast, RelationalImage)
        assert isinstance(ast.relation, Identifier)
        assert ast.relation.name == "parentOf"
        assert isinstance(ast.set, SetLiteral)
        assert len(ast.set.elements) == 1
        elem = ast.set.elements[0]
        assert isinstance(elem, Identifier)
        assert elem.name == "john"

    def test_relational_image_with_composition(self) -> None:
        """Test relational image with composed relation (R o9 S)(| A |)."""
        tokens = Lexer("(R o9 S)(| A |)").tokenize()
        ast = Parser(tokens).parse()
        assert isinstance(ast, RelationalImage)
        assert isinstance(ast.relation, BinaryOp)
        assert ast.relation.operator == "o9"
        assert isinstance(ast.set, Identifier)
        assert ast.set.name == "A"

    def test_relational_image_with_inverse(self) -> None:
        """Test relational image with inverse relation R~(| S |)."""
        tokens = Lexer("R~(| S |)").tokenize()
        ast = Parser(tokens).parse()
        assert isinstance(ast, RelationalImage)
        assert isinstance(ast.relation, UnaryOp)
        assert ast.relation.operator == "~"
        assert isinstance(ast.relation.operand, Identifier)
        assert ast.relation.operand.name == "R"
        assert isinstance(ast.set, Identifier)
        assert ast.set.name == "S"

    def test_solution_35_example(self) -> None:
        """Test Solution 35 example pattern."""
        tokens = Lexer("parentOf(| {p} |)").tokenize()
        ast = Parser(tokens).parse()
        assert isinstance(ast, RelationalImage)
        assert isinstance(ast.relation, Identifier)
        assert ast.relation.name == "parentOf"
        assert isinstance(ast.set, SetLiteral)
        assert len(ast.set.elements) == 1

    def test_chained_relational_images(self) -> None:
        """Test chained relational images R(| S |)(| T |)."""
        tokens = Lexer("R(| S |)(| T |)").tokenize()
        ast = Parser(tokens).parse()
        assert isinstance(ast, RelationalImage)
        assert isinstance(ast.relation, RelationalImage)
        assert isinstance(ast.relation.relation, Identifier)
        assert ast.relation.relation.name == "R"
        assert isinstance(ast.set, Identifier)
        assert ast.set.name == "T"


class TestRelationalImageLatex:
    """Test LaTeX generation for relational image expressions."""

    def test_simple_relational_image_latex(self) -> None:
        """Test LaTeX generation for R(| S |)."""
        tokens = Lexer("R(| S |)").tokenize()
        ast = Parser(tokens).parse()
        assert isinstance(ast, RelationalImage)
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)
        assert "\\limg" in latex
        assert "\\rimg" in latex
        assert "R" in latex
        assert "S" in latex
        assert latex == "(R \\limg S \\rimg)"

    def test_relational_image_with_set_literal_latex(self) -> None:
        """Test LaTeX generation for R(| {1, 2} |)."""
        tokens = Lexer("R(| {1, 2} |)").tokenize()
        ast = Parser(tokens).parse()
        assert isinstance(ast, RelationalImage)
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)
        assert "\\limg" in latex
        assert "\\rimg" in latex
        assert "\\{" in latex
        assert "\\}" in latex
        assert latex == "(R \\limg \\{1, 2\\} \\rimg)"

    def test_relational_image_with_composition_latex(self) -> None:
        """Test LaTeX generation for (R o9 S)(| A |)."""
        tokens = Lexer("(R o9 S)(| A |)").tokenize()
        ast = Parser(tokens).parse()
        assert isinstance(ast, RelationalImage)
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)
        assert "\\circ" in latex
        assert "\\limg" in latex
        assert "\\rimg" in latex
        assert "R" in latex
        assert "S" in latex
        assert "A" in latex

    def test_solution_35_latex(self) -> None:
        """Test LaTeX generation for Solution 35 pattern."""
        tokens = Lexer("parentOf(| {john} |)").tokenize()
        ast = Parser(tokens).parse()
        assert isinstance(ast, RelationalImage)
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)
        assert "parentOf" in latex
        assert "\\limg" in latex
        assert "\\rimg" in latex
        assert "john" in latex
        assert latex == "(parentOf \\limg \\{john\\} \\rimg)"

    def test_relational_image_with_inverse_latex(self) -> None:
        """Test LaTeX generation for R~(| S |)."""
        tokens = Lexer("R~(| S |)").tokenize()
        ast = Parser(tokens).parse()
        assert isinstance(ast, RelationalImage)
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)
        assert "R^{-1}" in latex
        assert "\\limg" in latex
        assert "\\rimg" in latex
        assert latex == "(R^{-1} \\limg S \\rimg)"


class TestRelationalImageEdgeCases:
    """Test edge cases for relational image."""

    def test_relational_image_with_complex_set_expression(self) -> None:
        """Test relational image with complex set expression."""
        tokens = Lexer("R(| A union B |)").tokenize()
        ast = Parser(tokens).parse()
        assert isinstance(ast, RelationalImage)
        assert isinstance(ast.set, BinaryOp)
        assert ast.set.operator == "union"

    def test_relational_image_with_domain_restriction(self) -> None:
        """Test relational image with domain-restricted relation."""
        tokens = Lexer("(S <| R)(| A |)").tokenize()
        ast = Parser(tokens).parse()
        assert isinstance(ast, RelationalImage)
        assert isinstance(ast.relation, BinaryOp)
        assert ast.relation.operator == "<|"

    def test_relational_image_preserves_line_column(self) -> None:
        """Test that relational image preserves line land column info."""
        tokens = Lexer("R(| S |)").tokenize()
        ast = Parser(tokens).parse()
        assert isinstance(ast, RelationalImage)
        assert ast.line == 1
        assert ast.column >= 1
