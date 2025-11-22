"""Tests for Phase 1: Multi-line document support and truth tables."""

from __future__ import annotations

from txt2tex.ast_nodes import (
    BinaryOp,
    Document,
    Identifier,
    Paragraph,
    TruthTable,
    UnaryOp,
)
from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser


class TestPhase1Parsing:
    """Test parsing of multi-line documents."""

    def test_empty_document(self) -> None:
        """Test parsing empty input."""
        lexer = Lexer("")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        assert isinstance(ast, Document)
        assert ast.items == []

    def test_single_expression_returns_expr(self) -> None:
        """Test that single expression still returns Expr (backward compatible)."""
        lexer = Lexer("p and q")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        # Phase 0 behavior: single expression returns Expr, not Document
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "and"

    def test_two_expressions(self) -> None:
        """Test parsing two expressions separated by newline."""
        lexer = Lexer("p and q\np or q")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        assert isinstance(ast, Document)
        assert len(ast.items) == 2

        # First expression: p and q
        expr1 = ast.items[0]
        assert isinstance(expr1, BinaryOp)
        assert expr1.operator == "and"

        # Second expression: p or q
        expr2 = ast.items[1]
        assert isinstance(expr2, BinaryOp)
        assert expr2.operator == "or"

    def test_multiple_expressions_with_blank_lines(self) -> None:
        """Test parsing multiple expressions with blank lines."""
        lexer = Lexer("p\n\nq\n\nr")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        assert isinstance(ast, Document)
        assert len(ast.items) == 3

        assert isinstance(ast.items[0], Identifier)
        assert ast.items[0].name == "p"

        assert isinstance(ast.items[1], Identifier)
        assert ast.items[1].name == "q"

        assert isinstance(ast.items[2], Identifier)
        assert ast.items[2].name == "r"

    def test_complex_multiline(self) -> None:
        """Test parsing complex multi-line document."""
        text = """p and q
not p
p => q
p <=> q"""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        assert isinstance(ast, Document)
        assert len(ast.items) == 4

        # p and q
        assert isinstance(ast.items[0], BinaryOp)
        assert ast.items[0].operator == "and"

        # not p
        assert isinstance(ast.items[1], UnaryOp)
        assert ast.items[1].operator == "not"

        # p => q
        assert isinstance(ast.items[2], BinaryOp)
        assert ast.items[2].operator == "=>"

        # p <=> q
        assert isinstance(ast.items[3], BinaryOp)
        assert ast.items[3].operator == "<=>"


class TestPhase1LaTeXGeneration:
    """Test LaTeX generation for multi-line documents."""

    def test_generate_single_expr_backward_compatible(self) -> None:
        """Test that single expression generation still works (backward compatible)."""
        gen = LaTeXGenerator()
        expr = BinaryOp(
            operator="and",
            left=Identifier(name="p", line=1, column=1),
            right=Identifier(name="q", line=1, column=5),
            line=1,
            column=3,
        )

        latex = gen.generate_document(expr)

        assert r"\documentclass[a4paper,10pt,fleqn]{article}" in latex
        assert r"\usepackage{zed-cm}" in latex
        assert r"$p \land q$" in latex
        assert r"\end{document}" in latex

    def test_generate_document_with_two_expressions(self) -> None:
        """Test LaTeX generation for document with two expressions."""
        gen = LaTeXGenerator()
        doc = Document(
            items=[
                BinaryOp(
                    operator="and",
                    left=Identifier(name="p", line=1, column=1),
                    right=Identifier(name="q", line=1, column=5),
                    line=1,
                    column=3,
                ),
                BinaryOp(
                    operator="or",
                    left=Identifier(name="p", line=2, column=1),
                    right=Identifier(name="q", line=2, column=4),
                    line=2,
                    column=3,
                ),
            ],
            line=1,
            column=1,
        )

        latex = gen.generate_document(doc)

        assert r"\documentclass[a4paper,10pt,fleqn]{article}" in latex
        assert r"\usepackage{zed-cm}" in latex
        # Standalone expressions are left-aligned, not centered
        assert r"\noindent" in latex
        assert r"p \land q" in latex
        assert r"p \lor q" in latex
        assert r"\end{document}" in latex

    def test_generate_empty_document(self) -> None:
        """Test LaTeX generation for empty document."""
        gen = LaTeXGenerator()
        doc = Document(items=[], line=1, column=1)

        latex = gen.generate_document(doc)

        assert r"\documentclass[a4paper,10pt,fleqn]{article}" in latex
        assert r"\begin{document}" in latex
        assert r"\end{document}" in latex

    def test_generate_document_with_fuzz(self) -> None:
        """Test LaTeX generation with fuzz package option."""
        gen = LaTeXGenerator(use_fuzz=True)
        doc = Document(
            items=[Identifier(name="p", line=1, column=1)],
            line=1,
            column=1,
        )

        latex = gen.generate_document(doc)

        assert r"\usepackage{fuzz}" in latex
        assert r"\usepackage{zed-cm}" not in latex


class TestPhase1Integration:
    """Integration tests for Phase 1."""

    def test_end_to_end_multiline(self) -> None:
        """Test complete pipeline from text to LaTeX for multi-line input."""
        text = "p and q\np or q\nnot p"

        # Lex
        lexer = Lexer(text)
        tokens = lexer.tokenize()

        # Parse
        parser = Parser(tokens)
        ast = parser.parse()

        # Generate
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # Verify
        assert isinstance(ast, Document)
        assert len(ast.items) == 3
        # Standalone expressions are left-aligned, not centered
        assert r"\noindent" in latex
        assert r"p \land q" in latex
        assert r"p \lor q" in latex
        assert r"\lnot p" in latex

    def test_solutions_expressions(self) -> None:
        """Test expressions from actual homework Solutions 1-3."""
        text = """p and q => p
p => (q => r)
not (p and q)"""

        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        assert isinstance(ast, Document)
        assert len(ast.items) == 3

        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # Standalone expressions are left-aligned, not centered
        assert r"\noindent" in latex
        assert r"p \land q \Rightarrow p" in latex
        # Nested implications now have explicit parentheses for clarity
        assert r"p \Rightarrow (q \Rightarrow r)" in latex
        # Fixed: Parentheses required around binary operand of not
        assert r"\lnot (p \land q)" in latex

    def test_paragraph_parsing(self) -> None:
        """Test parsing text paragraphs with TEXT: keyword."""
        text = "TEXT: In one direction we have"

        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        assert isinstance(ast, Document)
        assert len(ast.items) == 1
        assert isinstance(ast.items[0], Paragraph)
        assert ast.items[0].text == "In one direction we have"

    def test_paragraph_generation(self) -> None:
        """Test LaTeX generation for paragraphs."""
        gen = LaTeXGenerator()
        doc = Document(
            items=[
                Paragraph(text="In one direction:", line=1, column=1),
            ],
            line=1,
            column=1,
        )

        latex = gen.generate_document(doc)

        assert "In one direction:" in latex
        assert r"\documentclass[a4paper,10pt,fleqn]{article}" in latex
        assert r"\end{document}" in latex
        assert r"\bigskip" in latex

    def test_paragraph_with_symbols(self) -> None:
        """Test paragraph with operators and punctuation."""
        text = "TEXT: We combine these two proofs with the <=> intro rule."

        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        assert isinstance(ast, Document)
        assert len(ast.items) == 1
        assert isinstance(ast.items[0], Paragraph)
        # Text is captured raw, including <=> and period
        assert (
            ast.items[0].text == "We combine these two proofs with the <=> intro rule."
        )


# Truth table tests


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
