"""Test basic line continuation with backslash."""

from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser


def test_simple_and_continuation():
    """Test single line break elem AND expression."""
    code = "EQUIV:\nx land \\\n  y"
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    gen = LaTeXGenerator()
    latex = gen.generate_document(ast)
    assert "\\\\" in latex
    assert "\\quad" in latex


def test_multiple_and_continuations():
    """Test multiple line breaks elem chained AND expression."""
    code = "EQUIV:\na land \\\n  b land \\\n  c"
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    gen = LaTeXGenerator()
    latex = gen.generate_document(ast)
    assert latex.count("\\\\") >= 2


def test_or_continuation():
    """Test line break elem OR expression."""
    code = "EQUIV:\np lor \\\n  q"
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    gen = LaTeXGenerator()
    latex = gen.generate_document(ast)
    assert "\\\\" in latex
    assert "\\lor" in latex


def test_implies_continuation():
    """Test line break elem IMPLIES expression."""
    code = "EQUIV:\np => \\\n  q"
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    gen = LaTeXGenerator()
    latex = gen.generate_document(ast)
    assert "\\\\" in latex
    assert "\\Rightarrow" in latex or "\\implies" in latex


def test_iff_continuation():
    """Test line break elem IFF expression."""
    code = "EQUIV:\np <=> \\\n  q"
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    gen = LaTeXGenerator()
    latex = gen.generate_document(ast)
    assert "\\\\" in latex
    assert "\\Leftrightarrow" in latex


def test_continuation_with_trailing_whitespace():
    """Test that trailing whitespace after backslash is handled."""
    code = "EQUIV:\nx land \\   \n  y"
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    gen = LaTeXGenerator()
    latex = gen.generate_document(ast)
    assert "\\\\" in latex


def test_set_difference_unaffected():
    """Test that A \\ B still works as set difference."""
    code = "EQUIV:\nA \\ B"
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    gen = LaTeXGenerator()
    latex = gen.generate_document(ast)
    assert "\\setminus" in latex
    assert "\\\\ " not in latex or "\\quad" not in latex


def test_continuation_in_complex_expression():
    """Test line break elem complex nested expression."""
    code = "EQUIV:\na land b land \\\n  c lor d"
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    gen = LaTeXGenerator()
    latex = gen.generate_document(ast)
    assert "\\\\" in latex
    assert "\\quad" in latex


def test_continuation_preserves_precedence():
    """Test that line breaks don't affect operator precedence."""
    code1 = "EQUIV:\na land b lor c"
    code2 = "EQUIV:\na land \\\n  b lor c"
    lexer1 = Lexer(code1)
    tokens1 = lexer1.tokenize()
    parser1 = Parser(tokens1)
    ast1 = parser1.parse()
    lexer2 = Lexer(code2)
    tokens2 = lexer2.tokenize()
    parser2 = Parser(tokens2)
    ast2 = parser2.parse()
    gen = LaTeXGenerator()
    latex1 = gen.generate_document(ast1)
    latex2 = gen.generate_document(ast2)
    assert "\\lor" in latex1
    assert "\\lor" in latex2
    assert "\\land" in latex1
    assert "\\land" in latex2


def test_no_continuation_without_newline():
    """Test that \\ without newline is set difference."""
    code = "EQUIV:\nA\\B"
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    gen = LaTeXGenerator()
    latex = gen.generate_document(ast)
    assert "\\setminus" in latex
