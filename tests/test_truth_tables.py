"""Tests for truth table parsing and generation (Phase 1)."""

from __future__ import annotations

from txt2tex.ast_nodes import Document, TruthTable
from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser


def parse_truth_table(text: str) -> TruthTable:
    """Helper to parse truth table."""
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    result = parser.parse()
    # Find truth table in document
    if isinstance(result, Document):
        for item in result.items:
            if isinstance(item, TruthTable):
                return item
    raise ValueError("No truth table found")


def test_simple_truth_table() -> None:
    """Test basic truth table with two columns."""
    text = """
TRUTH TABLE:
p | not p
T | F
F | T
"""
    table = parse_truth_table(text)
    assert table.headers == ["p", "not p"]
    assert table.rows == [["T", "F"], ["F", "T"]]


def test_truth_table_with_and() -> None:
    """Test truth table with AND operator."""
    text = """
TRUTH TABLE:
p | q | p and q
T | T | T
T | F | F
F | T | F
F | F | F
"""
    table = parse_truth_table(text)
    assert table.headers == ["p", "q", "p and q"]
    assert len(table.rows) == 4
    assert table.rows[0] == ["T", "T", "T"]
    assert table.rows[3] == ["F", "F", "F"]


def test_truth_table_with_implies() -> None:
    """Test truth table with implication."""
    text = """
TRUTH TABLE:
p | q | p => q
T | T | T
T | F | F
F | T | T
F | F | T
"""
    table = parse_truth_table(text)
    assert table.headers == ["p", "q", "p => q"]
    assert len(table.rows) == 4


def test_truth_table_complex_header() -> None:
    """Test truth table with complex expressions in header."""
    text = """
TRUTH TABLE:
p | q | p and q | (p and q) => p
T | T | T | T
T | F | F | T
F | T | F | T
F | F | F | T
"""
    table = parse_truth_table(text)
    assert len(table.headers) == 4
    # Parser preserves spacing between tokens
    assert table.headers[3] == "( p and q ) => p"


def test_truth_table_with_lowercase() -> None:
    """Test truth table with lowercase t/f values."""
    text = """
TRUTH TABLE:
p | q
t | t
t | f
f | t
f | f
"""
    table = parse_truth_table(text)
    # Values should be normalized to uppercase
    assert table.rows[0] == ["T", "T"]
    assert table.rows[1] == ["T", "F"]


def test_truth_table_with_iff() -> None:
    """Test truth table with biconditional."""
    text = """
TRUTH TABLE:
p | q | p <=> q
T | T | T
T | F | F
F | T | F
F | F | T
"""
    table = parse_truth_table(text)
    assert table.headers == ["p", "q", "p <=> q"]
    assert table.rows[0] == ["T", "T", "T"]
    assert table.rows[1] == ["T", "F", "F"]


def test_truth_table_latex_generation() -> None:
    """Test LaTeX generation for truth tables."""
    text = """
TRUTH TABLE:
p | q | p and q
T | T | T
T | F | F
F | T | F
F | F | F
"""
    table = parse_truth_table(text)
    generator = LaTeXGenerator()
    latex_lines = generator._generate_truth_table(table)
    latex = "\n".join(latex_lines)

    # Check for tabular environment
    assert "\\begin{tabular}" in latex
    assert "\\end{tabular}" in latex

    # Check for headers
    assert "p" in latex
    assert "q" in latex
    assert "p and q" in latex or "p \\land q" in latex

    # Check for horizontal line after header
    assert "\\hline" in latex


def test_truth_table_with_or() -> None:
    """Test truth table with OR operator."""
    text = """
TRUTH TABLE:
p | q | p or q
T | T | T
T | F | T
F | T | T
F | F | F
"""
    table = parse_truth_table(text)
    assert table.headers == ["p", "q", "p or q"]
    assert table.rows[0] == ["T", "T", "T"]
    assert table.rows[3] == ["F", "F", "F"]


def test_truth_table_with_not() -> None:
    """Test truth table with NOT operator."""
    text = """
TRUTH TABLE:
p | not p | not (not p)
T | F | T
F | T | F
"""
    table = parse_truth_table(text)
    assert len(table.headers) == 3
    assert len(table.rows) == 2


def test_truth_table_three_variables() -> None:
    """Test truth table with three variables."""
    text = """
TRUTH TABLE:
p | q | r | p and q and r
T | T | T | T
T | T | F | F
T | F | T | F
T | F | F | F
F | T | T | F
F | T | F | F
F | F | T | F
F | F | F | F
"""
    table = parse_truth_table(text)
    assert len(table.headers) == 4
    assert len(table.rows) == 8
    assert table.rows[0] == ["T", "T", "T", "T"]
    assert table.rows[7] == ["F", "F", "F", "F"]


def test_truth_table_phase19_f_token() -> None:
    """Test that F token (from Phase 19 FINSET) works in truth tables."""
    text = """
TRUTH TABLE:
p | q
F | F
F | T
T | F
T | T
"""
    table = parse_truth_table(text)
    # F should be recognized as truth value despite being FINSET keyword
    assert table.rows[0] == ["F", "F"]
    assert table.rows[1] == ["F", "T"]
    assert table.rows[2] == ["T", "F"]
    assert table.rows[3] == ["T", "T"]
