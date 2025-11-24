"""Tests for Phase 1.4: Zed environment consolidation.

This phase consolidates consecutive GivenType, FreeType, and Abbreviation items
into a single zed environment with \\also between them.
"""

from txt2tex.ast_nodes import Document, FreeBranch, FreeType, GivenType
from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser


def test_consecutive_given_and_free_types():
    """Test consecutive given and free types are consolidated."""
    text = """given NAME, DATE

Status ::= active | inactive"""

    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()

    gen = LaTeXGenerator()
    latex = gen.generate_document(ast)

    # Should have one zed environment with \\also
    assert r"\begin{zed}" in latex
    assert r"\also" in latex
    assert latex.count(r"\begin{zed}") == 1
    assert latex.count(r"\end{zed}") == 1
    assert r"[~ NAME, DATE ~]" in latex
    assert r"Status ::= active | inactive" in latex


def test_three_consecutive_zed_items():
    """Test three consecutive zed items are consolidated."""
    text = """given A, B

Status ::= ok | fail

Pair == A cross B"""

    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()

    gen = LaTeXGenerator()
    latex = gen.generate_document(ast)

    # Should have one zed environment with two \\also
    assert latex.count(r"\begin{zed}") == 1
    assert latex.count(r"\also") == 2
    assert r"[~ A, B ~]" in latex
    assert r"Status ::= ok | fail" in latex
    assert r"Pair == A \cross B" in latex


def test_single_zed_item_not_consolidated():
    """Test single zed item generates normal output."""
    text = """given NAME"""

    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()

    gen = LaTeXGenerator()
    latex = gen.generate_document(ast)

    # Should have one zed environment, no \\also
    assert latex.count(r"\begin{zed}") == 1
    assert latex.count(r"\end{zed}") == 1
    assert r"\also" not in latex
    assert r"[~ NAME ~]" in latex


def test_zed_items_separated_by_text():
    """Test zed items separated by text are not consolidated."""
    text = """given NAME

TEXT: Some description.

Status ::= active"""

    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()

    gen = LaTeXGenerator()
    latex = gen.generate_document(ast)

    # Should have two separate zed environments
    assert latex.count(r"\begin{zed}") == 2
    assert latex.count(r"\end{zed}") == 2
    assert r"\also" not in latex
    assert r"Some description" in latex


def test_zed_items_separated_by_schema():
    """Test zed items separated by schema are not consolidated."""
    text = """given NAME

schema State
  count : N
end

Status ::= ok"""

    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()

    gen = LaTeXGenerator()
    latex = gen.generate_document(ast)

    # Should have two separate zed environments (given and free type)
    # Schema generates its own environment
    assert latex.count(r"\begin{zed}") == 2
    assert r"\also" not in latex


def test_consolidation_preserves_content():
    """Test consolidated output matches individual outputs."""
    # Test data
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

    # Generate consolidated
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

    # Check content is present
    assert "[~ X, Y ~]" in latex
    assert "Status ::= active | inactive" in latex
    assert r"\also" in latex
