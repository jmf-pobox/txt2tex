"""Test basic line continuation with backslash."""

from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser


def test_simple_and_continuation():
    """Test single line break in AND expression."""
    code = r"""EQUIV:
x and \
  y"""
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()

    # Generate LaTeX and check for line break
    gen = LaTeXGenerator()
    latex = gen.generate_document(ast)

    # Should contain \\ for line break
    assert r"\\" in latex
    # Should contain \quad for indentation
    assert r"\quad" in latex


def test_multiple_and_continuations():
    """Test multiple line breaks in chained AND expression."""
    code = r"""EQUIV:
a and \
  b and \
  c"""
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()

    gen = LaTeXGenerator()
    latex = gen.generate_document(ast)

    # Should have multiple line breaks
    assert latex.count(r"\\") >= 2


def test_or_continuation():
    """Test line break in OR expression."""
    code = r"""EQUIV:
p or \
  q"""
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()

    gen = LaTeXGenerator()
    latex = gen.generate_document(ast)

    assert r"\\" in latex
    assert r"\lor" in latex


def test_implies_continuation():
    """Test line break in IMPLIES expression."""
    code = r"""EQUIV:
p => \
  q"""
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()

    gen = LaTeXGenerator()
    latex = gen.generate_document(ast)

    assert r"\\" in latex
    assert r"\Rightarrow" in latex or r"\implies" in latex


def test_iff_continuation():
    """Test line break in IFF expression."""
    code = r"""EQUIV:
p <=> \
  q"""
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()

    gen = LaTeXGenerator()
    latex = gen.generate_document(ast)

    assert r"\\" in latex
    assert r"\Leftrightarrow" in latex


def test_continuation_with_trailing_whitespace():
    """Test that trailing whitespace after backslash is handled."""
    code = "EQUIV:\nx and \\   \n  y"
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()

    gen = LaTeXGenerator()
    latex = gen.generate_document(ast)

    assert r"\\" in latex


def test_set_difference_unaffected():
    """Test that A \\ B still works as set difference."""
    code = r"""EQUIV:
A \ B"""
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()

    gen = LaTeXGenerator()
    latex = gen.generate_document(ast)

    # Should use \setminus, not line break
    assert r"\setminus" in latex
    # Should NOT have \\ followed by \quad (line break pattern)
    assert r"\\ " not in latex or r"\quad" not in latex


def test_continuation_in_complex_expression():
    """Test line break in complex nested expression."""
    code = r"""EQUIV:
a and b and \
  c or d"""
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()

    gen = LaTeXGenerator()
    latex = gen.generate_document(ast)

    assert r"\\" in latex
    assert r"\quad" in latex


def test_continuation_preserves_precedence():
    """Test that line breaks don't affect operator precedence."""
    code1 = "EQUIV:\na and b or c"
    code2 = r"""EQUIV:
a and \
  b or c"""

    # Parse both
    lexer1 = Lexer(code1)
    tokens1 = lexer1.tokenize()
    parser1 = Parser(tokens1)
    ast1 = parser1.parse()

    lexer2 = Lexer(code2)
    tokens2 = lexer2.tokenize()
    parser2 = Parser(tokens2)
    ast2 = parser2.parse()

    # Generate LaTeX for both
    gen = LaTeXGenerator()
    latex1 = gen.generate_document(ast1)
    latex2 = gen.generate_document(ast2)

    # Both should have OR and AND operators
    assert r"\lor" in latex1 and r"\lor" in latex2
    assert r"\land" in latex1 and r"\land" in latex2


def test_no_continuation_without_newline():
    """Test that \\ without newline is set difference."""
    code = "EQUIV:\nA\\B"
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()

    gen = LaTeXGenerator()
    latex = gen.generate_document(ast)

    # Should be set difference
    assert r"\setminus" in latex
