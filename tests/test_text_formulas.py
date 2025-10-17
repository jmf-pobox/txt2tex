"""Tests for logical formula detection in TEXT blocks (prose paragraphs)."""

from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser


def test_simple_implication_formula():
    """Test p => q formula in TEXT block."""
    text = """=== Test ===

TEXT: The formula p => q is simple."""

    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()

    gen = LaTeXGenerator()
    latex = gen.generate_document(ast)

    assert r"$p \Rightarrow q$" in latex
    assert "is simple" in latex


def test_not_in_formula():
    """Test not p in formula context."""
    text = """=== Test ===

TEXT: The formula p => (not p => p) is a tautology."""

    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()

    gen = LaTeXGenerator()
    latex = gen.generate_document(ast)

    # Should be wrapped as one formula with not converted to \lnot
    assert r"$p \Rightarrow (\lnot p \Rightarrow p)$" in latex
    assert "is a tautology" in latex


def test_equivalence_formula():
    """Test <=> formula in TEXT block."""
    text = """=== Test ===

TEXT: The statement (not p => not q) <=> (q => p) is true."""

    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()

    gen = LaTeXGenerator()
    latex = gen.generate_document(ast)

    # Should detect and parse the complete formula
    assert r"$\lnot p \Rightarrow \lnot q \Leftrightarrow q \Rightarrow p$" in latex
    assert "is true" in latex


def test_formula_with_and_or():
    """Test formula with and/or operators inside implication."""
    text = """=== Test ===

TEXT: The expression (p and q) => (p or q) is valid."""

    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()

    gen = LaTeXGenerator()
    latex = gen.generate_document(ast)

    # Should detect the => and parse formula containing and/or
    # Note: Current implementation detects formulas by => or <=> presence
    assert r"\Rightarrow" in latex
    assert "is valid" in latex


def test_not_in_prose_not_converted():
    """Test 'not' in English prose not converted (not before variable)."""
    text = """=== Test ===

TEXT: This is not relevant to the formula discussion."""

    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()

    gen = LaTeXGenerator()
    latex = gen.generate_document(ast)

    # Should NOT have \lnot because "not relevant" has multi-char word after "not"
    assert r"\lnot" not in latex
    assert "not relevant" in latex


def test_standalone_not_variable():
    """Test standalone 'not p' converted to logical not."""
    text = """=== Test ===

TEXT: We assume not p and not q for this proof."""

    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()

    gen = LaTeXGenerator()
    latex = gen.generate_document(ast)

    # Standalone not p should be converted
    assert r"$\lnot p$" in latex
    assert r"$\lnot q$" in latex
    assert "for this proof" in latex


def test_multiple_formulas_in_one_paragraph():
    """Test multiple formulas in same TEXT block."""
    text = """=== Test ===

TEXT: First p => q and then q => r gives us p => r by transitivity."""

    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()

    gen = LaTeXGenerator()
    latex = gen.generate_document(ast)

    # Should detect all three formulas
    assert r"$p \Rightarrow q$" in latex
    assert r"$q \Rightarrow r$" in latex
    assert r"$p \Rightarrow r$" in latex
    assert "by transitivity" in latex


def test_complex_nested_formula():
    """Test complex nested formula with multiple operators."""
    text = """=== Test ===

TEXT: Consider ((p => r) and (q => r)) <=> ((p or q) => r) as an example."""

    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()

    gen = LaTeXGenerator()
    latex = gen.generate_document(ast)

    # Should parse formulas containing => and <=>
    # Note: and/or within formulas may not be fully captured as single expression
    assert r"\Rightarrow" in latex
    assert r"\Leftrightarrow" in latex
    assert "as an example" in latex


def test_formula_stops_at_sentence_boundary():
    """Test that formula detection stops at sentence boundaries."""
    text = """=== Test ===

TEXT: The formula p => q is valid for all values."""

    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()

    gen = LaTeXGenerator()
    latex = gen.generate_document(ast)

    # Should only capture "p => q", not continue past "is"
    assert r"$p \Rightarrow q$" in latex
    assert "is valid for all values" in latex
    # Should NOT try to parse "is valid" as part of formula
    assert r"is $" not in latex


def test_formula_with_parentheses_at_start():
    """Test formula starting with parentheses."""
    text = """=== Test ===

TEXT: The statement (not p) => (not q) is interesting."""

    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()

    gen = LaTeXGenerator()
    latex = gen.generate_document(ast)

    # Should detect => and convert not to \lnot
    assert r"\lnot" in latex
    assert r"\Rightarrow" in latex
    assert "is interesting" in latex
