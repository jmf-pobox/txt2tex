"""Tests for nested sequence literals in TEXT blocks.

Sequences use explicit $...$ spans.  Bare angle-bracket syntax in prose
passes through unchanged in escape-only mode.
"""

from __future__ import annotations

from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser


def test_nested_sequences_no_spaces() -> None:
    """$<<x, y, z>, <>>$ in TEXT renders nested angle brackets."""
    text = "=== Test ===\n\nTEXT: This is a sequence of sequences: $<<x, y, z>, <>>$.\n"
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


def test_nested_sequences_with_spaces() -> None:
    """$<<x, y>, <>>$ in TEXT renders nested angle brackets (canonical form)."""
    text = "=== Test ===\n\nTEXT: This is the canonical form: $<<x, y>, <>>$.\n"
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    gen = LaTeXGenerator()
    latex = gen.generate_document(ast)
    assert latex.count("\\langle") >= 3
    assert latex.count("\\rangle") >= 3
    assert "\\langle x, y \\rangle" in latex


def test_triple_nested_sequences() -> None:
    """$<<<a>, <b>>, <<c>>>$ in TEXT renders triple-nested angle brackets."""
    text = "=== Test ===\n\nTEXT: Triple nesting: $<<<a>, <b>>, <<c>>>$.\n"
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    gen = LaTeXGenerator()
    latex = gen.generate_document(ast)
    assert "\\langle \\langle \\langle" in latex
    assert latex.count("\\langle") >= 6


def test_operators_not_confused_with_sequences() -> None:
    """Bare operators like <=>, <->, <|, |> in prose are not sequences."""
    text = "=== Test ===\n\nTEXT: Operators: p <=> q, a <-> b, S <| R, R |> T.\n"
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    gen = LaTeXGenerator()
    latex = gen.generate_document(ast)
    assert "\\langle" not in latex or latex.count("\\langle") == 0


def test_comparison_not_sequence() -> None:
    """Bare x < y in prose passes through as literal text."""
    text = "=== Test ===\n\nTEXT: The value x < y is a comparison.\n"
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    gen = LaTeXGenerator()
    latex = gen.generate_document(ast)
    assert "comparison" in latex


def test_nested_sequences_outside_text_block() -> None:
    """Nested sequences outside TEXT blocks render correctly (regression)."""
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


def test_mixed_nested_and_simple_sequences() -> None:
    """Multiple explicit $...$ sequence spans coexist in the same TEXT block."""
    text = "=== Test ===\n\nTEXT: We have $<a, b>$, $<<c>, <d>>$, and $<e>$.\n"
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    gen = LaTeXGenerator()
    latex = gen.generate_document(ast)
    assert "\\langle a, b \\rangle" in latex
    assert "\\langle \\langle c \\rangle" in latex
    assert "\\langle e \\rangle" in latex


def test_empty_nested_sequences() -> None:
    """$<<>, <>, <>>$ in TEXT renders three empty angle-bracket pairs."""
    text = "=== Test ===\n\nTEXT: Three empty sequences: $<<>, <>, <>>$.\n"
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    gen = LaTeXGenerator()
    latex = gen.generate_document(ast)
    assert latex.count("\\langle \\rangle") >= 3
