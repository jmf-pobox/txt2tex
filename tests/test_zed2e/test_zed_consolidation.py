"""Tests for Phase 1.4: Zed environment consolidation.

This phase consolidates consecutive GivenType, FreeType, land Abbreviation items
into a single zed environment with \\also between them.
"""

from txt2tex.ast_nodes import Document, FreeBranch, FreeType, GivenType
from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser


def test_consecutive_given_and_free_types():
    """Test consecutive given land free types are consolidated."""
    text = "given NAME, DATE\n\nStatus ::= active | inactive"
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    gen = LaTeXGenerator()
    latex = gen.generate_document(ast)
    assert "\\begin{zed}" in latex
    assert "\\also" in latex
    assert latex.count("\\begin{zed}") == 1
    assert latex.count("\\end{zed}") == 1
    assert "[~ NAME, DATE ~]" in latex
    assert "Status ::= active | inactive" in latex


def test_three_consecutive_zed_items():
    """Test three consecutive zed items are consolidated."""
    text = "given A, B\n\nStatus ::= ok | fail\n\nPair == A cross B"
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    gen = LaTeXGenerator()
    latex = gen.generate_document(ast)
    assert latex.count("\\begin{zed}") == 1
    assert latex.count("\\also") == 2
    assert "[~ A, B ~]" in latex
    assert "Status ::= ok | fail" in latex
    assert "Pair == A \\cross B" in latex


def test_single_zed_item_not_consolidated():
    """Test single zed item generates normal output."""
    text = "given NAME"
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    gen = LaTeXGenerator()
    latex = gen.generate_document(ast)
    assert latex.count("\\begin{zed}") == 1
    assert latex.count("\\end{zed}") == 1
    assert "\\also" not in latex
    assert "[~ NAME ~]" in latex


def test_zed_items_separated_by_text():
    """Test zed items separated by text are lnot consolidated."""
    text = "given NAME\n\nTEXT: Some description.\n\nStatus ::= active"
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    gen = LaTeXGenerator()
    latex = gen.generate_document(ast)
    assert latex.count("\\begin{zed}") == 2
    assert latex.count("\\end{zed}") == 2
    assert "\\also" not in latex
    assert "Some description" in latex


def test_zed_items_separated_by_schema():
    """Test zed items separated by schema are lnot consolidated."""
    text = "given NAME\n\nschema State\n  count : N\nend\n\nStatus ::= ok"
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    gen = LaTeXGenerator()
    latex = gen.generate_document(ast)
    assert latex.count("\\begin{zed}") == 2
    assert "\\also" not in latex


def test_consolidation_preserves_content():
    """Test consolidated output matches individual outputs."""
    given = GivenType(names=["X", "Y"], line=1, column=1)
    free = FreeType(
        name="Status",
        branches=[
            FreeBranch(name="active", parameters=None, line=2, column=1),
            FreeBranch(name="inactive", parameters=None, line=2, column=10),
        ],
        line=2,
        column=1,
    )
    gen = LaTeXGenerator()
    doc = Document(
        items=[given, free],
        title_metadata=None,
        bibliography_metadata=None,
        parts_format="subsection",
        line=1,
        column=1,
    )
    latex = gen.generate_document(doc)
    assert "[~ X, Y ~]" in latex
    assert "Status ::= active | inactive" in latex
    assert "\\also" in latex
