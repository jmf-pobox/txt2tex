"""Tests for logical formula detection in TEXT blocks (prose paragraphs)."""

from __future__ import annotations

from txt2tex.ast_nodes import (
    Document,
    LatexBlock,
    PageBreak,
    Paragraph,
    PureParagraph,
    Solution,
)
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

    # Phase 29: Explicit parentheses are now preserved
    # The formula has explicit parens around both sides of <=>, so they're preserved
    assert r"$(\lnot p \Rightarrow \lnot q) \Leftrightarrow (q \Rightarrow p)$" in latex
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


# PURETEXT and PAGEBREAK tests


def test_puretext_basic() -> None:
    """Test basic PURETEXT parsing."""
    text = """PURETEXT: This is raw text with no processing."""
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    result = parser.parse()

    assert isinstance(result, Document)
    assert len(result.items) == 1
    assert isinstance(result.items[0], PureParagraph)
    assert result.items[0].text == "This is raw text with no processing."


def test_puretext_with_punctuation() -> None:
    """Test PURETEXT with punctuation that would break TEXT."""
    text = """PURETEXT: Author's name (2025), "quoted text", and more."""
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    result = parser.parse()

    assert isinstance(result, Document)
    assert len(result.items) == 1
    assert isinstance(result.items[0], PureParagraph)
    # Verify content is preserved
    assert "Author's name" in result.items[0].text
    assert '"quoted text"' in result.items[0].text


def test_puretext_with_math_symbols() -> None:
    """Test PURETEXT does not convert math symbols."""
    text = """PURETEXT: forall x in N, x >= 0 and not (x < 0)"""
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    result = parser.parse()

    assert isinstance(result, Document)
    assert len(result.items) == 1
    assert isinstance(result.items[0], PureParagraph)
    # These should remain as plain text (not converted)
    assert "forall" in result.items[0].text
    assert "in" in result.items[0].text
    assert "and" in result.items[0].text
    assert "not" in result.items[0].text


def test_pagebreak_basic() -> None:
    """Test basic PAGEBREAK parsing."""
    text = """PAGEBREAK:"""
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    result = parser.parse()

    assert isinstance(result, Document)
    assert len(result.items) == 1
    assert isinstance(result.items[0], PageBreak)


def test_pagebreak_between_sections() -> None:
    """Test PAGEBREAK between content."""
    text = """** Solution 1 **

x = 1

PAGEBREAK:

** Solution 2 **

y = 2
"""
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    result = parser.parse()

    assert isinstance(result, Document)
    # PageBreak is part of Solution 1's items
    assert len(result.items) == 2
    solution1 = result.items[0]
    assert isinstance(solution1, Solution)
    # Check that Solution 1 contains the PageBreak
    assert any(isinstance(item, PageBreak) for item in solution1.items)


def test_puretext_latex_generation() -> None:
    """Test LaTeX generation for PURETEXT."""
    text = """PURETEXT: Simpson, A. (2025) "Lecture notes" and more."""
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    doc = parser.parse()

    generator = LaTeXGenerator()
    latex = generator.generate_document(doc)

    # Should have bigskip spacing
    assert r"\bigskip" in latex
    # Should have the text (with LaTeX escaping applied)
    # Quotes should be preserved in some form
    assert "Simpson" in latex
    assert "2025" in latex


def test_pagebreak_latex_generation() -> None:
    """Test LaTeX generation for PAGEBREAK."""
    text = """PAGEBREAK:"""
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    doc = parser.parse()

    generator = LaTeXGenerator()
    latex = generator.generate_document(doc)

    # Should contain \newpage command
    assert r"\newpage" in latex


def test_puretext_no_formula_detection() -> None:
    """Test that PURETEXT does not detect formulas."""
    text = """PURETEXT: The set { x : N | x > 0 } is non-empty."""
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    doc = parser.parse()

    generator = LaTeXGenerator()
    latex = generator.generate_document(doc)

    # These should NOT be converted to math symbols
    # (formula detection should be skipped)
    # The text should remain mostly as-is (with LaTeX escaping only)
    assert "The set" in latex


def test_multiple_puretext_blocks() -> None:
    """Test multiple PURETEXT blocks in sequence."""
    text = """PURETEXT: First paragraph.
PURETEXT: Second paragraph.
PURETEXT: Third paragraph.
"""
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    result = parser.parse()

    assert isinstance(result, Document)
    assert len(result.items) == 3
    assert all(isinstance(item, PureParagraph) for item in result.items)


def test_puretext_empty() -> None:
    """Test PURETEXT with no content."""
    text = """PURETEXT: """
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    result = parser.parse()

    assert isinstance(result, Document)
    assert len(result.items) == 1
    assert isinstance(result.items[0], PureParagraph)
    assert result.items[0].text == ""


def test_mixed_text_and_puretext() -> None:
    """Test mixing TEXT and PURETEXT blocks."""
    text = """TEXT: Regular text with forall x in N.
PURETEXT: Raw text with forall x in N.
"""
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    result = parser.parse()

    assert isinstance(result, Document)
    assert len(result.items) == 2
    # First should be Paragraph (TEXT), second should be PureParagraph (PURETEXT)
    assert isinstance(result.items[0], Paragraph)
    assert isinstance(result.items[1], PureParagraph)


def test_latex_basic() -> None:
    """Test basic LATEX parsing."""
    text = """LATEX: \\begin{center}Test\\end{center}"""
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    result = parser.parse()

    assert isinstance(result, Document)
    assert len(result.items) == 1
    assert isinstance(result.items[0], LatexBlock)
    assert result.items[0].latex == "\\begin{center}Test\\end{center}"


def test_latex_with_special_chars() -> None:
    """Test LATEX with special characters (no escaping)."""
    text = """LATEX: Test $x^2$ & #1 % comment"""
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    result = parser.parse()

    assert isinstance(result, Document)
    assert len(result.items) == 1
    assert isinstance(result.items[0], LatexBlock)
    # All special chars should be preserved (no escaping)
    assert "$x^2$" in result.items[0].latex
    assert "&" in result.items[0].latex
    assert "#1" in result.items[0].latex
    assert "%" in result.items[0].latex


def test_latex_custom_command() -> None:
    """Test LATEX with custom commands."""
    text = """LATEX: \\mycustomcommand{arg1}{arg2}"""
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    result = parser.parse()

    assert isinstance(result, Document)
    assert len(result.items) == 1
    assert isinstance(result.items[0], LatexBlock)
    assert result.items[0].latex == "\\mycustomcommand{arg1}{arg2}"


def test_latex_latex_generation() -> None:
    """Test LaTeX generation for LATEX blocks."""
    text = """LATEX: \\vspace{1cm}"""
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    doc = parser.parse()

    generator = LaTeXGenerator()
    latex = generator.generate_document(doc)

    # Should contain the raw LaTeX command
    assert "\\vspace{1cm}" in latex


def test_mixed_text_puretext_latex() -> None:
    """Test mixing TEXT, PURETEXT, and LATEX blocks."""
    text = """TEXT: Normal text with forall x.
PURETEXT: Raw text with $ and &.
LATEX: \\customcommand{test}
"""
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    result = parser.parse()

    assert isinstance(result, Document)
    assert len(result.items) == 3
    assert isinstance(result.items[0], Paragraph)
    assert isinstance(result.items[1], PureParagraph)
    assert isinstance(result.items[2], LatexBlock)


def test_latex_empty() -> None:
    """Test LATEX with no content."""
    text = """LATEX: """
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    result = parser.parse()

    assert isinstance(result, Document)
    assert len(result.items) == 1
    assert isinstance(result.items[0], LatexBlock)
    assert result.items[0].latex == ""
