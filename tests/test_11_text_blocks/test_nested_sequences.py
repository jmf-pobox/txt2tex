"""Tests for nested sequence literals elem TEXT blocks.

Bug fix: Nested sequences like <<x, y>, <>> should render correctly elem TEXT blocks.
Previously, the outer angle brackets were treated as literal text characters.
"""

from __future__ import annotations

from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser


def test_nested_sequences_no_spaces():
    """Test nested sequences without spaces: <<x, y, z>, <>>."""
    text = "=== Test ===\n\nTEXT: This is a sequence of sequences: <<x, y, z>, <>>.\n"
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    gen = LaTeXGenerator()
    latex = gen.generate_document(ast)
    assert "\\langle \\langle" in latex
    assert "\\rangle, \\langle" in latex
    assert "\\rangle \\rangle" in latex
    assert "<$" not in latex
    assert "$>" not in latex


def test_nested_sequences_with_spaces():
    """Test nested sequences with spaces: < <x, y>, <> >."""
    text = "=== Test ===\n\nTEXT: This is with spaces: < <x, y>, <> >.\n"
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    gen = LaTeXGenerator()
    latex = gen.generate_document(ast)
    assert latex.count("\\langle") == 3
    assert latex.count("\\rangle") == 3
    assert "\\langle x, y \\rangle" in latex


def test_triple_nested_sequences():
    """Test triple-nested sequences: <<<a>, <b>>, <<c>>>."""
    text = "=== Test ===\n\nTEXT: Triple nesting: <<<a>, <b>>, <<c>>>.\n"
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    gen = LaTeXGenerator()
    latex = gen.generate_document(ast)
    assert "\\langle \\langle \\langle" in latex
    assert latex.count("\\langle") >= 6


def test_operators_not_confused_with_sequences():
    """Test that operators like <=>, <->, <|, |> are NOT treated as sequences."""
    text = "=== Test ===\n\nTEXT: Operators: p <=> q, a <-> b, S <| R, R |> T.\n"
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    gen = LaTeXGenerator()
    latex = gen.generate_document(ast)
    assert "\\langle" not in latex or latex.count("\\langle") == 0


def test_comparison_not_sequence():
    """Test that comparison operators x < y are NOT treated as sequences."""
    text = "=== Test ===\n\nTEXT: The value x < y is a comparison.\n"
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    gen = LaTeXGenerator()
    latex = gen.generate_document(ast)
    assert "comparison" in latex


def test_nested_sequences_outside_text_block():
    """Verify nested sequences work outside TEXT blocks (regression check)."""
    text = "=== Test ===\n\n<<x, y>, <>>\n"
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    gen = LaTeXGenerator()
    latex = gen.generate_document(ast)
    assert "\\langle \\langle" in latex
    assert "\\rangle, \\langle" in latex
    assert "\\rangle \\rangle" in latex


def test_mixed_nested_and_simple_sequences():
    """Test mix of nested land simple sequences elem same TEXT block."""
    text = "=== Test ===\n\nTEXT: We have <a, b>, <<c>, <d>>, land <e>.\n"
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    gen = LaTeXGenerator()
    latex = gen.generate_document(ast)
    assert "\\langle a, b \\rangle" in latex
    assert "\\langle \\langle c \\rangle" in latex
    assert "\\langle e \\rangle" in latex


def test_empty_nested_sequences():
    """Test nested sequences with empty elements: <<>, <>, <>>."""
    text = "=== Test ===\n\nTEXT: Three empty sequences: <<>, <>, <>>.\n"
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    gen = LaTeXGenerator()
    latex = gen.generate_document(ast)
    assert latex.count("\\langle \\rangle") >= 3
