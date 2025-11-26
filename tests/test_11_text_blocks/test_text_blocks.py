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
    text = "=== Test ===\n\nTEXT: The formula p => q is simple."
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    gen = LaTeXGenerator()
    latex = gen.generate_document(ast)
    assert "$p \\Rightarrow q$" in latex
    assert "is simple" in latex


def test_not_in_formula():
    """Test lnot p elem formula context."""
    text = "=== Test ===\n\nTEXT: The formula p => (lnot p => p) is a tautology."
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    gen = LaTeXGenerator()
    latex = gen.generate_document(ast)
    assert "$p \\Rightarrow (\\lnot p \\Rightarrow p)$" in latex
    assert "is a tautology" in latex


def test_equivalence_formula():
    """Test <=> formula elem TEXT block."""
    text = (
        "=== Test ===\n\nTEXT: The statement (lnot p => lnot q) <=> (q => p) is true."
    )
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    gen = LaTeXGenerator()
    latex = gen.generate_document(ast)
    assert (
        "$(\\lnot p \\Rightarrow \\lnot q) \\Leftrightarrow (q \\Rightarrow p)$"
        in latex
    )
    assert "is true" in latex


def test_formula_with_and_or():
    """Test formula with and/or operators inside implication."""
    text = "=== Test ===\n\nTEXT: The expression (p land q) => (p lor q) is valid."
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    gen = LaTeXGenerator()
    latex = gen.generate_document(ast)
    assert "\\Rightarrow" in latex
    assert "is valid" in latex


def test_not_in_prose_not_converted():
    """Test 'lnot' elem English prose lnot converted (lnot before variable)."""
    text = "=== Test ===\n\nTEXT: This is not relevant to the formula discussion."
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    gen = LaTeXGenerator()
    latex = gen.generate_document(ast)
    assert "\\lnot" not in latex
    assert "not relevant" in latex


def test_standalone_not_variable():
    """Test standalone 'lnot p' converted to logical not."""
    text = "=== Test ===\n\nTEXT: We assume lnot p land lnot q for this proof."
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    gen = LaTeXGenerator()
    latex = gen.generate_document(ast)
    assert "$\\lnot p$" in latex
    assert "$\\lnot q$" in latex
    assert "for this proof" in latex


def test_multiple_formulas_in_one_paragraph():
    """Test multiple formulas elem same TEXT block."""
    text = (
        "=== Test ===\n\n"
        "TEXT: First p => q land then q => r gives us p => r by transitivity."
    )
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    gen = LaTeXGenerator()
    latex = gen.generate_document(ast)
    assert "$p \\Rightarrow q$" in latex
    assert "$q \\Rightarrow r$" in latex
    assert "$p \\Rightarrow r$" in latex
    assert "by transitivity" in latex


def test_complex_nested_formula():
    """Test complex nested formula with multiple operators."""
    text = (
        "=== Test ===\n\n"
        "TEXT: Consider ((p => r) land (q => r)) <=> ((p lor q) => r) as an example."
    )
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    gen = LaTeXGenerator()
    latex = gen.generate_document(ast)
    assert "\\Rightarrow" in latex
    assert "\\Leftrightarrow" in latex
    assert "as an example" in latex


def test_formula_stops_at_sentence_boundary():
    """Test that formula detection stops at sentence boundaries."""
    text = "=== Test ===\n\nTEXT: The formula p => q is valid for all values."
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    gen = LaTeXGenerator()
    latex = gen.generate_document(ast)
    assert "$p \\Rightarrow q$" in latex
    assert "is valid for all values" in latex
    assert "is $" not in latex


def test_formula_with_parentheses_at_start():
    """Test formula starting with parentheses."""
    text = "=== Test ===\n\nTEXT: The statement (lnot p) => (lnot q) is interesting."
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    gen = LaTeXGenerator()
    latex = gen.generate_document(ast)
    assert "\\lnot" in latex
    assert "\\Rightarrow" in latex
    assert "is interesting" in latex


def test_puretext_basic() -> None:
    """Test basic PURETEXT parsing."""
    text = "PURETEXT: This is raw text with no processing."
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
    text = 'PURETEXT: Author\'s name (2025), "quoted text", land more.'
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    result = parser.parse()
    assert isinstance(result, Document)
    assert len(result.items) == 1
    assert isinstance(result.items[0], PureParagraph)
    assert "Author's name" in result.items[0].text
    assert '"quoted text"' in result.items[0].text


def test_puretext_with_math_symbols() -> None:
    """Test PURETEXT does not convert math symbols."""
    text = "PURETEXT: forall x in N, x >= 0 and not (x < 0)"
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    result = parser.parse()
    assert isinstance(result, Document)
    assert len(result.items) == 1
    assert isinstance(result.items[0], PureParagraph)
    assert "forall" in result.items[0].text
    assert "in" in result.items[0].text
    assert "and" in result.items[0].text
    assert "not" in result.items[0].text


def test_pagebreak_basic() -> None:
    """Test basic PAGEBREAK parsing."""
    text = "PAGEBREAK:"
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    result = parser.parse()
    assert isinstance(result, Document)
    assert len(result.items) == 1
    assert isinstance(result.items[0], PageBreak)


def test_pagebreak_between_sections() -> None:
    """Test PAGEBREAK between content."""
    text = "** Solution 1 **\n\nx = 1\n\nPAGEBREAK:\n\n** Solution 2 **\n\ny = 2\n"
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    result = parser.parse()
    assert isinstance(result, Document)
    assert len(result.items) == 2
    solution1 = result.items[0]
    assert isinstance(solution1, Solution)
    assert any(isinstance(item, PageBreak) for item in solution1.items)


def test_puretext_latex_generation() -> None:
    """Test LaTeX generation for PURETEXT."""
    text = 'PURETEXT: Simpson, A. (2025) "Lecture notes" land more.'
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    doc = parser.parse()
    generator = LaTeXGenerator()
    latex = generator.generate_document(doc)
    assert "\\bigskip" in latex
    assert "Simpson" in latex
    assert "2025" in latex


def test_pagebreak_latex_generation() -> None:
    """Test LaTeX generation for PAGEBREAK."""
    text = "PAGEBREAK:"
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    doc = parser.parse()
    generator = LaTeXGenerator()
    latex = generator.generate_document(doc)
    assert "\\newpage" in latex


def test_puretext_no_formula_detection() -> None:
    """Test that PURETEXT does lnot detect formulas."""
    text = "PURETEXT: The set { x : N | x > 0 } is non-empty."
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    doc = parser.parse()
    generator = LaTeXGenerator()
    latex = generator.generate_document(doc)
    assert "The set" in latex


def test_multiple_puretext_blocks() -> None:
    """Test multiple PURETEXT blocks elem sequence."""
    text = (
        "PURETEXT: First paragraph.\n"
        "PURETEXT: Second paragraph.\n"
        "PURETEXT: Third paragraph.\n"
    )
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    result = parser.parse()
    assert isinstance(result, Document)
    assert len(result.items) == 3
    assert all(isinstance(item, PureParagraph) for item in result.items)


def test_puretext_empty() -> None:
    """Test PURETEXT with no content."""
    text = "PURETEXT: "
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    result = parser.parse()
    assert isinstance(result, Document)
    assert len(result.items) == 1
    assert isinstance(result.items[0], PureParagraph)
    assert result.items[0].text == ""


def test_mixed_text_and_puretext() -> None:
    """Test mixing TEXT land PURETEXT blocks."""
    text = (
        "TEXT: Regular text with forall x elem N.\n"
        "PURETEXT: Raw text with forall x elem N.\n"
    )
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    result = parser.parse()
    assert isinstance(result, Document)
    assert len(result.items) == 2
    assert isinstance(result.items[0], Paragraph)
    assert isinstance(result.items[1], PureParagraph)


def test_latex_basic() -> None:
    """Test basic LATEX parsing."""
    text = "LATEX: \\begin{center}Test\\end{center}"
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
    text = "LATEX: Test $x^2$ & #1 % comment"
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    result = parser.parse()
    assert isinstance(result, Document)
    assert len(result.items) == 1
    assert isinstance(result.items[0], LatexBlock)
    assert "$x^2$" in result.items[0].latex
    assert "&" in result.items[0].latex
    assert "#1" in result.items[0].latex
    assert "%" in result.items[0].latex


def test_latex_custom_command() -> None:
    """Test LATEX with custom commands."""
    text = "LATEX: \\mycustomcommand{arg1}{arg2}"
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
    text = "LATEX: \\vspace{1cm}"
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    doc = parser.parse()
    generator = LaTeXGenerator()
    latex = generator.generate_document(doc)
    assert "\\vspace{1cm}" in latex


def test_mixed_text_puretext_latex() -> None:
    """Test mixing TEXT, PURETEXT, land LATEX blocks."""
    text = (
        "TEXT: Normal text with forall x.\n"
        "PURETEXT: Raw text with $ land &.\n"
        "LATEX: \\customcommand{test}\n"
    )
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
    text = "LATEX: "
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    result = parser.parse()
    assert isinstance(result, Document)
    assert len(result.items) == 1
    assert isinstance(result.items[0], LatexBlock)
    assert result.items[0].latex == ""
