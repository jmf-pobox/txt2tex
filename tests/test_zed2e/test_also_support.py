"""Tests for \\also support in where clauses (Phase 1 of zed2e alignment)."""

from __future__ import annotations

from txt2tex.ast_nodes import AxDef, Document, GenDef, Schema
from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser


class TestAlsoSupport:
    """Test automatic \\also generation for blank lines in where clauses."""

    def test_axdef_with_blank_line_generates_also(self) -> None:
        """Test that blank lines in axdef predicates generate \\also."""
        text = """axdef
    x : N
    y : N
where
    x > 0

    y > 0
end"""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        gen = LaTeXGenerator()
        assert isinstance(ast, Document)
        assert isinstance(ast.items[0], AxDef)
        latex_lines = gen.generate_document_item(ast.items[0])
        latex = "".join(latex_lines)

        # Should contain \also between predicate groups
        assert r"\also" in latex
        assert latex.count(r"\also") == 1

    def test_axdef_without_blank_line_no_also(self) -> None:
        """Test that predicates without blank lines don't generate \\also."""
        text = """axdef
    x : N
    y : N
where
    x > 0
    y > 0
end"""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        gen = LaTeXGenerator()
        assert isinstance(ast, Document)
        assert isinstance(ast.items[0], AxDef)
        latex_lines = gen.generate_document_item(ast.items[0])
        latex = "".join(latex_lines)

        # Should NOT contain \also
        assert r"\also" not in latex

    def test_schema_with_blank_lines_generates_also(self) -> None:
        """Test that blank lines in schema predicates generate \\also."""
        text = """schema Counter
    count : N
where
    count >= 0

    count < 100
end"""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        gen = LaTeXGenerator()
        assert isinstance(ast, Document)
        assert isinstance(ast.items[0], Schema)
        latex_lines = gen.generate_document_item(ast.items[0])
        latex = "".join(latex_lines)

        # Should contain \also between predicate groups
        assert r"\also" in latex

    def test_multiple_blank_lines_generate_multiple_also(self) -> None:
        """Test that multiple blank line separators generate multiple \\also."""
        text = """axdef
    x : N
    y : N
    z : N
where
    x > 0

    y > 0

    z > 0
end"""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        gen = LaTeXGenerator()
        assert isinstance(ast, Document)
        assert isinstance(ast.items[0], AxDef)
        latex_lines = gen.generate_document_item(ast.items[0])
        latex = "".join(latex_lines)

        # Should contain 2 \also commands (3 groups, 2 separators)
        assert latex.count(r"\also") == 2

    def test_gendef_with_blank_lines_generates_also(self) -> None:
        """Test that blank lines in gendef predicates generate \\also."""
        text = """gendef [X]
    f : X -> X
where
    f = id X

    dom f = X
end"""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        gen = LaTeXGenerator()
        assert isinstance(ast, Document)
        assert isinstance(ast.items[0], GenDef)
        latex_lines = gen.generate_document_item(ast.items[0])
        latex = "".join(latex_lines)

        # Should contain \also between predicate groups
        assert r"\also" in latex
