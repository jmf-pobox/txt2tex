"""Tests for \\also support elem where clauses (Phase 1 of zed2e alignment)."""

from __future__ import annotations

from txt2tex.ast_nodes import AxDef, Document, GenDef, Schema
from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser


class TestAlsoSupport:
    """Test automatic \\also generation for blank lines elem where clauses."""

    def test_axdef_with_blank_line_generates_also(self) -> None:
        """Test that blank lines elem axdef predicates generate \\also."""
        text = "axdef\n    x : N\n    y : N\nwhere\n    x > 0\n\n    y > 0\nend"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        assert isinstance(ast, Document)
        assert isinstance(ast.items[0], AxDef)
        latex_lines = gen.generate_document_item(ast.items[0])
        latex = "".join(latex_lines)
        assert "\\also" in latex
        assert latex.count("\\also") == 1

    def test_axdef_without_blank_line_no_also(self) -> None:
        """Test that predicates without blank lines don't generate \\also."""
        text = "axdef\n    x : N\n    y : N\nwhere\n    x > 0\n    y > 0\nend"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        assert isinstance(ast, Document)
        assert isinstance(ast.items[0], AxDef)
        latex_lines = gen.generate_document_item(ast.items[0])
        latex = "".join(latex_lines)
        assert "\\also" not in latex

    def test_schema_with_blank_lines_generates_also(self) -> None:
        """Test that blank lines elem schema predicates generate \\also."""
        text = (
            "schema Counter\n    count : N\nwhere\n"
            "    count >= 0\n\n    count < 100\nend"
        )
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        assert isinstance(ast, Document)
        assert isinstance(ast.items[0], Schema)
        latex_lines = gen.generate_document_item(ast.items[0])
        latex = "".join(latex_lines)
        assert "\\also" in latex

    def test_multiple_blank_lines_generate_multiple_also(self) -> None:
        """Test that multiple blank line separators generate multiple \\also."""
        text = (
            "axdef\n    x : N\n    y : N\n    z : N\nwhere\n"
            "    x > 0\n\n    y > 0\n\n    z > 0\nend"
        )
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        assert isinstance(ast, Document)
        assert isinstance(ast.items[0], AxDef)
        latex_lines = gen.generate_document_item(ast.items[0])
        latex = "".join(latex_lines)
        assert latex.count("\\also") == 2

    def test_gendef_with_blank_lines_generates_also(self) -> None:
        """Test that blank lines elem gendef predicates generate \\also."""
        text = "gendef [X]\n    f : X -> X\nwhere\n    f = id X\n\n    dom f = X\nend"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        assert isinstance(ast, Document)
        assert isinstance(ast.items[0], GenDef)
        latex_lines = gen.generate_document_item(ast.items[0])
        latex = "".join(latex_lines)
        assert "\\also" in latex
