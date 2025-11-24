"""Tests for semicolon-separated declarations in gendef, axdef, and schema.

This feature allows multiple declarations to be specified on one line using
semicolons as separators, which is required for fuzz compatibility.
"""

from txt2tex.ast_nodes import AxDef, Document, GenDef, Schema
from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser


class TestSemicolonDeclarationsParsing:
    """Test parsing of semicolon-separated declarations."""

    def test_gendef_single_declaration(self) -> None:
        """Test gendef with single declaration (no semicolons)."""
        source = """gendef [X]
  f : X -> X
end"""
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        assert isinstance(ast, Document)
        assert len(ast.items) == 1
        assert isinstance(ast.items[0], GenDef)
        gendef = ast.items[0]
        assert len(gendef.declarations) == 1
        assert gendef.declarations[0].variable == "f"

    def test_gendef_two_declarations_with_semicolon(self) -> None:
        """Test gendef with two declarations separated by semicolon."""
        source = """gendef [X]
  f : X -> X; g : X -> X
end"""
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        assert isinstance(ast, Document)
        assert len(ast.items) == 1
        assert isinstance(ast.items[0], GenDef)
        gendef = ast.items[0]
        assert len(gendef.declarations) == 2
        assert gendef.declarations[0].variable == "f"
        assert gendef.declarations[1].variable == "g"

    def test_gendef_three_declarations_with_semicolons(self) -> None:
        """Test gendef with three declarations separated by semicolons."""
        source = """gendef [X]
  f : X -> X; g : X -> X; h : X -> X
end"""
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        assert isinstance(ast, Document)
        assert len(ast.items) == 1
        assert isinstance(ast.items[0], GenDef)
        gendef = ast.items[0]
        assert len(gendef.declarations) == 3
        assert gendef.declarations[0].variable == "f"
        assert gendef.declarations[1].variable == "g"
        assert gendef.declarations[2].variable == "h"

    def test_axdef_two_declarations_with_semicolon(self) -> None:
        """Test axdef with two declarations separated by semicolon."""
        source = """axdef
  x : N; y : N
where
  x > y
end"""
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        assert isinstance(ast, Document)
        assert len(ast.items) == 1
        assert isinstance(ast.items[0], AxDef)
        axdef = ast.items[0]
        assert len(axdef.declarations) == 2
        assert axdef.declarations[0].variable == "x"
        assert axdef.declarations[1].variable == "y"

    def test_axdef_with_generics_and_semicolon(self) -> None:
        """Test axdef with generic parameters and semicolon declarations."""
        source = """axdef [X]
  f : X; g : X
end"""
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        assert isinstance(ast, Document)
        assert len(ast.items) == 1
        assert isinstance(ast.items[0], AxDef)
        axdef = ast.items[0]
        assert len(axdef.declarations) == 2
        assert axdef.generic_params == ["X"]

    def test_schema_two_declarations_with_semicolon(self) -> None:
        """Test schema with two declarations separated by semicolon."""
        source = """schema State
  x : N; y : N
where
  x > y
end"""
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        assert isinstance(ast, Document)
        assert len(ast.items) == 1
        assert isinstance(ast.items[0], Schema)
        schema = ast.items[0]
        assert len(schema.declarations) == 2
        assert schema.declarations[0].variable == "x"
        assert schema.declarations[1].variable == "y"

    def test_schema_with_generics_and_semicolon(self) -> None:
        """Test schema with generic parameters and semicolon declarations."""
        source = """schema Pair[X, Y]
  first : X; second : Y
end"""
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        assert isinstance(ast, Document)
        assert len(ast.items) == 1
        assert isinstance(ast.items[0], Schema)
        schema = ast.items[0]
        assert len(schema.declarations) == 2
        assert schema.generic_params == ["X", "Y"]


class TestSemicolonDeclarationsLaTeXGeneration:
    """Test LaTeX generation for semicolon-separated declarations."""

    def test_gendef_single_declaration_latex(self) -> None:
        """Test LaTeX output for gendef with single declaration."""
        source = """gendef [X]
  f : X -> X
end"""
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # Single declaration should not have semicolon
        assert r"\begin{gendef}[X]" in latex
        assert "f: X \\fun X" in latex
        assert ";" not in latex

    def test_gendef_two_declarations_latex(self) -> None:
        """Test LaTeX output for gendef with two semicolon-separated declarations."""
        source = """gendef [X]
  f : X -> X; g : X -> X
end"""
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # Two declarations should be on separate lines with line break
        assert r"\begin{gendef}[X]" in latex
        assert "f: X \\fun X \\\\" in latex
        assert "g: X \\fun X" in latex
        assert r"\end{gendef}" in latex

    def test_gendef_three_declarations_latex(self) -> None:
        """Test LaTeX output for gendef with three semicolon-separated declarations."""
        source = """gendef [X]
  f : X -> X; g : X -> X; h : X -> X
end"""
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # Three declarations should be on separate lines with line breaks
        assert "f: X \\fun X \\\\" in latex
        assert "g: X \\fun X \\\\" in latex
        assert "h: X \\fun X" in latex

    def test_axdef_two_declarations_latex(self) -> None:
        """Test LaTeX output for axdef with two semicolon-separated declarations."""
        source = """axdef
  x : N; y : N
where
  x > y
end"""
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # Two declarations should be on separate lines with line break
        assert r"\begin{axdef}" in latex
        assert "x : \\mathbb{N} \\\\" in latex
        assert "y : \\mathbb{N}" in latex
        assert r"\where" in latex

    def test_axdef_with_generics_latex(self) -> None:
        """Test LaTeX output for axdef with generics and semicolon declarations."""
        source = """axdef [X, Y]
  f : X; g : Y
end"""
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        assert r"\begin{axdef}[X, Y]" in latex
        assert "f : X \\\\" in latex
        assert "g : Y" in latex

    def test_schema_two_declarations_latex(self) -> None:
        """Test LaTeX output for schema with two semicolon-separated declarations."""
        source = """schema State
  x : N; y : N
where
  x > y
end"""
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # Two declarations should be on separate lines with line break
        assert r"\begin{schema}{State}" in latex
        assert "x : \\mathbb{N} \\\\" in latex
        assert "y : \\mathbb{N}" in latex
        assert r"\where" in latex

    def test_schema_with_generics_latex(self) -> None:
        """Test LaTeX output for schema with generics and semicolon declarations."""
        source = """schema Pair[X, Y]
  first : X; second : Y
end"""
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        assert r"\begin{schema}{Pair}[X, Y]" in latex
        assert "first : X \\\\" in latex
        assert "second : Y" in latex


class TestSemicolonDeclarationsFuzzMode:
    """Test that semicolon declarations work correctly in fuzz mode."""

    def test_gendef_fuzz_mode(self) -> None:
        """Test gendef with semicolon declarations in fuzz mode."""
        source = """gendef [X]
  f : X -> X; g : X -> X
end"""
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        gen = LaTeXGenerator(use_fuzz=True)
        latex = gen.generate_document(ast)

        # In fuzz mode, declarations on separate lines with line breaks
        assert r"\begin{gendef}[X]" in latex
        assert "f: X \\fun X \\\\" in latex
        assert "g: X \\fun X" in latex

    def test_axdef_fuzz_mode(self) -> None:
        """Test axdef with semicolon declarations in fuzz mode."""
        source = """axdef
  x : N; y : N
end"""
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        gen = LaTeXGenerator(use_fuzz=True)
        latex = gen.generate_document(ast)

        # In fuzz mode, N becomes \nat, declarations on separate lines
        assert r"\begin{axdef}" in latex
        assert "x : \\nat \\\\" in latex
        assert "y : \\nat" in latex

    def test_schema_fuzz_mode(self) -> None:
        """Test schema with semicolon declarations in fuzz mode."""
        source = """schema State
  x : N; y : N
end"""
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        gen = LaTeXGenerator(use_fuzz=True)
        latex = gen.generate_document(ast)

        # In fuzz mode, N becomes \nat, declarations on separate lines
        assert r"\begin{schema}{State}" in latex
        assert "x : \\nat \\\\" in latex
        assert "y : \\nat" in latex


class TestSemicolonDeclarationsEdgeCases:
    """Test edge cases for semicolon-separated declarations."""

    def test_gendef_mixed_newlines_and_semicolons(self) -> None:
        """Test gendef with declarations on separate lines (no semicolons)."""
        source = """gendef [X]
  f : X -> X
  g : X -> X
end"""
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        assert isinstance(ast, Document)
        assert len(ast.items) == 1
        assert isinstance(ast.items[0], GenDef)
        gendef = ast.items[0]
        assert len(gendef.declarations) == 2

        # Generate LaTeX - declarations on separate lines with line breaks
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        # Separate lines in input still produce line breaks in output
        assert "f: X \\fun X \\\\" in latex
        assert "g: X \\fun X" in latex

    def test_trailing_semicolon_not_allowed(self) -> None:
        """Test that trailing semicolon after last declaration is handled."""
        source = """gendef [X]
  f : X -> X;
end"""
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)

        # This should parse without error - the semicolon should be consumed
        # and no empty declaration should be created
        ast = parser.parse()
        assert isinstance(ast, Document)
        assert len(ast.items) == 1
        assert isinstance(ast.items[0], GenDef)
        gendef = ast.items[0]
        assert len(gendef.declarations) == 1

    def test_complex_types_with_semicolons(self) -> None:
        """Test complex type expressions with semicolon separators."""
        source = """gendef [X, Y]
  f : X -> Y; g : seq X -> seq Y; h : P X -> P Y
end"""
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        assert isinstance(ast, Document)
        assert len(ast.items) == 1
        assert isinstance(ast.items[0], GenDef)
        gendef = ast.items[0]
        assert len(gendef.declarations) == 3

        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        # Three declarations on separate lines with line breaks
        assert "f: X \\fun Y \\\\" in latex
        assert "g: \\seq~X \\fun \\seq~Y \\\\" in latex
        assert "h: \\power X \\fun \\power Y" in latex
