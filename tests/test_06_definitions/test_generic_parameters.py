"""Tests for Phase 9: Z Notation Definitions with Generic Parameters."""

from txt2tex.ast_nodes import Abbreviation, AxDef, Document, Identifier, Schema
from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser


class TestPhase9Parsing:
    """Test parsing Z notation definitions with generic parameters."""

    def test_abbreviation_without_generics(self) -> None:
        """Test parsing simple abbreviation without generics."""
        source = "Nplus == N"
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        assert isinstance(ast, Document)
        assert len(ast.items) == 1
        assert isinstance(ast.items[0], Abbreviation)
        abbrev = ast.items[0]
        assert abbrev.name == "Nplus"
        assert isinstance(abbrev.expression, Identifier)
        assert abbrev.generic_params is None

    def test_abbreviation_with_single_generic(self) -> None:
        """Test parsing abbreviation with single generic parameter."""
        source = "[X] Pair == X"
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        assert isinstance(ast, Document)
        assert len(ast.items) == 1
        assert isinstance(ast.items[0], Abbreviation)
        abbrev = ast.items[0]
        assert abbrev.name == "Pair"
        assert abbrev.generic_params == ["X"]

    def test_abbreviation_with_multiple_generics(self) -> None:
        """Test parsing abbreviation with multiple generic parameters."""
        source = "[X, Y, Z] Triple == X"
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        assert isinstance(ast, Document)
        assert len(ast.items) == 1
        assert isinstance(ast.items[0], Abbreviation)
        abbrev = ast.items[0]
        assert abbrev.name == "Triple"
        assert abbrev.generic_params == ["X", "Y", "Z"]

    def test_axdef_without_generics(self) -> None:
        """Test parsing axiomatic definition without generics."""
        source = """axdef
  x : N
where
  x > 0
end"""
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        assert isinstance(ast, Document)
        assert len(ast.items) == 1
        assert isinstance(ast.items[0], AxDef)
        axdef = ast.items[0]
        assert len(axdef.declarations) == 1
        assert axdef.generic_params is None

    def test_axdef_with_single_generic(self) -> None:
        """Test parsing axdef with single generic parameter."""
        source = """axdef [X]
  f : X
where
  f = f
end"""
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        assert isinstance(ast, Document)
        assert len(ast.items) == 1
        assert isinstance(ast.items[0], AxDef)
        axdef = ast.items[0]
        assert axdef.generic_params == ["X"]

    def test_axdef_with_multiple_generics(self) -> None:
        """Test parsing axdef with multiple generic parameters."""
        source = """axdef [X, Y]
  f : X
  g : Y
end"""
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        assert isinstance(ast, Document)
        assert len(ast.items) == 1
        assert isinstance(ast.items[0], AxDef)
        axdef = ast.items[0]
        assert axdef.generic_params == ["X", "Y"]

    def test_schema_without_generics(self) -> None:
        """Test parsing schema without generics."""
        source = """schema State
  x : N
where
  x > 0
end"""
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        assert isinstance(ast, Document)
        assert len(ast.items) == 1
        assert isinstance(ast.items[0], Schema)
        schema = ast.items[0]
        assert schema.name == "State"
        assert schema.generic_params is None

    def test_schema_with_single_generic(self) -> None:
        """Test parsing schema with single generic parameter."""
        source = """schema Stack[X]
  items : X
end"""
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        assert isinstance(ast, Document)
        assert len(ast.items) == 1
        assert isinstance(ast.items[0], Schema)
        schema = ast.items[0]
        assert schema.name == "Stack"
        assert schema.generic_params == ["X"]

    def test_schema_with_multiple_generics(self) -> None:
        """Test parsing schema with multiple generic parameters."""
        source = """schema Relation[X, Y]
  first : X
  second : Y
end"""
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        assert isinstance(ast, Document)
        assert len(ast.items) == 1
        assert isinstance(ast.items[0], Schema)
        schema = ast.items[0]
        assert schema.name == "Relation"
        assert schema.generic_params == ["X", "Y"]


class TestPhase9LaTeXGeneration:
    """Test LaTeX generation for Z notation with generic parameters."""

    def test_generate_abbreviation_without_generics(self) -> None:
        """Test LaTeX generation for abbreviation without generics."""
        source = "Pair == N"
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        assert "Pair == \\mathbb{N}" in latex
        assert "[X]" not in latex

    def test_generate_abbreviation_with_generics(self) -> None:
        """Test LaTeX generation for abbreviation with generics."""
        source = "[X] Pair == X"
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # Abbreviations now wrapped in zed environment for fuzz compatibility
        # Fuzz requires generics AFTER name: Pair[X] not [X]Pair
        assert r"Pair[X] == X" in latex

    def test_generate_axdef_without_generics(self) -> None:
        """Test LaTeX generation for axdef without generics."""
        source = """axdef
  x : N
end"""
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        assert r"\begin{axdef}" in latex
        assert r"\end{axdef}" in latex
        assert "[X]" not in latex

    def test_generate_axdef_with_generics(self) -> None:
        """Test LaTeX generation for axdef with generics."""
        source = """axdef [X, Y]
  f : X
  g : Y
end"""
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        assert r"\begin{axdef}[X, Y]" in latex
        assert r"\end{axdef}" in latex

    def test_generate_schema_without_generics(self) -> None:
        """Test LaTeX generation for schema without generics."""
        source = """schema State
  x : N
end"""
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        assert r"\begin{schema}{State}" in latex
        assert r"\end{schema}" in latex
        assert "[X]" not in latex

    def test_generate_schema_with_generics(self) -> None:
        """Test LaTeX generation for schema with generics."""
        source = """schema Stack[X]
  items : X
end"""
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        assert r"\begin{schema}{Stack}[X]" in latex
        assert r"\end{schema}" in latex


class TestPhase9Integration:
    """Integration tests for Phase 9."""

    def test_full_document_with_generics(self) -> None:
        """Test complete document with all Z notation features."""
        source = """=== Phase 9 Test ===

given A, B

[X] Pair == X

axdef [T]
  empty : T
end

schema Container[X]
  items : X
end
"""
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # Check all components are present
        assert r"\section*{Phase 9 Test}" in latex
        assert r"\begin{zed}[A, B]\end{zed}" in latex
        # Abbreviations now wrapped in zed environment for fuzz compatibility
        # Fuzz requires generics AFTER name: Pair[X] not [X]Pair
        assert r"Pair[X] == X" in latex
        assert r"\begin{axdef}[T]" in latex
        assert r"\begin{schema}{Container}[X]" in latex
