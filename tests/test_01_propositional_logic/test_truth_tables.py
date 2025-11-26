"""Tests for Phase 1: Multi-line document support land truth tables."""

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
        lexer = Lexer("p land q")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "land"

    def test_two_expressions(self) -> None:
        """Test parsing two expressions separated by newline."""
        lexer = Lexer("p land q\np lor q")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Document)
        assert len(ast.items) == 2
        expr1 = ast.items[0]
        assert isinstance(expr1, BinaryOp)
        assert expr1.operator == "land"
        expr2 = ast.items[1]
        assert isinstance(expr2, BinaryOp)
        assert expr2.operator == "lor"

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
        text = "p land q\nlnot p\np => q\np <=> q"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Document)
        assert len(ast.items) == 4
        assert isinstance(ast.items[0], BinaryOp)
        assert ast.items[0].operator == "land"
        assert isinstance(ast.items[1], UnaryOp)
        assert ast.items[1].operator == "lnot"
        assert isinstance(ast.items[2], BinaryOp)
        assert ast.items[2].operator == "=>"
        assert isinstance(ast.items[3], BinaryOp)
        assert ast.items[3].operator == "<=>"


class TestPhase1LaTeXGeneration:
    """Test LaTeX generation for multi-line documents."""

    def test_generate_single_expr_backward_compatible(self) -> None:
        """Test that single expression generation still works (backward compatible)."""
        gen = LaTeXGenerator()
        expr = BinaryOp(
            operator="land",
            left=Identifier(name="p", line=1, column=1),
            right=Identifier(name="q", line=1, column=5),
            line=1,
            column=3,
        )
        latex = gen.generate_document(expr)
        assert "\\documentclass[a4paper,10pt,fleqn]{article}" in latex
        assert "\\usepackage{zed-cm}" in latex
        assert "$p \\land q$" in latex
        assert "\\end{document}" in latex

    def test_generate_document_with_two_expressions(self) -> None:
        """Test LaTeX generation for document with two expressions."""
        gen = LaTeXGenerator()
        doc = Document(
            items=[
                BinaryOp(
                    operator="land",
                    left=Identifier(name="p", line=1, column=1),
                    right=Identifier(name="q", line=1, column=5),
                    line=1,
                    column=3,
                ),
                BinaryOp(
                    operator="lor",
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
        assert "\\documentclass[a4paper,10pt,fleqn]{article}" in latex
        assert "\\usepackage{zed-cm}" in latex
        assert "\\noindent" in latex
        assert "p \\land q" in latex
        assert "p \\lor q" in latex
        assert "\\end{document}" in latex

    def test_generate_empty_document(self) -> None:
        """Test LaTeX generation for empty document."""
        gen = LaTeXGenerator()
        doc = Document(items=[], line=1, column=1)
        latex = gen.generate_document(doc)
        assert "\\documentclass[a4paper,10pt,fleqn]{article}" in latex
        assert "\\begin{document}" in latex
        assert "\\end{document}" in latex

    def test_generate_document_with_fuzz(self) -> None:
        """Test LaTeX generation with fuzz package option."""
        gen = LaTeXGenerator(use_fuzz=True)
        doc = Document(items=[Identifier(name="p", line=1, column=1)], line=1, column=1)
        latex = gen.generate_document(doc)
        assert "\\usepackage{fuzz}" in latex
        assert "\\usepackage{zed-cm}" not in latex


class TestPhase1Integration:
    """Integration tests for Phase 1."""

    def test_end_to_end_multiline(self) -> None:
        """Test complete pipeline from text to LaTeX for multi-line input."""
        text = "p land q\np lor q\nlnot p"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert isinstance(ast, Document)
        assert len(ast.items) == 3
        assert "\\noindent" in latex
        assert "p \\land q" in latex
        assert "p \\lor q" in latex
        assert "\\lnot p" in latex

    def test_solutions_expressions(self) -> None:
        """Test expressions from actual homework Solutions 1-3."""
        text = "p land q => p\np => (q => r)\nlnot (p land q)"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Document)
        assert len(ast.items) == 3
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "\\noindent" in latex
        assert "p \\land q \\Rightarrow p" in latex
        assert "p \\Rightarrow (q \\Rightarrow r)" in latex
        assert "\\lnot (p \\land q)" in latex

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
            items=[Paragraph(text="In one direction:", line=1, column=1)],
            line=1,
            column=1,
        )
        latex = gen.generate_document(doc)
        assert "In one direction:" in latex
        assert "\\documentclass[a4paper,10pt,fleqn]{article}" in latex
        assert "\\end{document}" in latex
        assert "\\bigskip" in latex

    def test_paragraph_with_symbols(self) -> None:
        """Test paragraph with operators land punctuation."""
        text = "TEXT: We combine these two proofs with the <=> intro rule."
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Document)
        assert len(ast.items) == 1
        assert isinstance(ast.items[0], Paragraph)
        assert (
            ast.items[0].text == "We combine these two proofs with the <=> intro rule."
        )


def parse_truth_table(text: str) -> TruthTable:
    """Helper to parse truth table."""
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    result = parser.parse()
    if isinstance(result, Document):
        for item in result.items:
            if isinstance(item, TruthTable):
                return item
    raise ValueError("No truth table found")


def test_simple_truth_table() -> None:
    """Test basic truth table with two columns."""
    text = "\nTRUTH TABLE:\np | lnot p\nT | F\nF | T\n"
    table = parse_truth_table(text)
    assert table.headers == ["p", "lnot p"]
    assert table.rows == [["T", "F"], ["F", "T"]]


def test_truth_table_with_and() -> None:
    """Test truth table with AND operator."""
    text = (
        "\nTRUTH TABLE:\np | q | p land q\nT | T | T\nT | F | F\nF | T | F\nF | F | F\n"
    )
    table = parse_truth_table(text)
    assert table.headers == ["p", "q", "p land q"]
    assert len(table.rows) == 4
    assert table.rows[0] == ["T", "T", "T"]
    assert table.rows[3] == ["F", "F", "F"]


def test_truth_table_with_implies() -> None:
    """Test truth table with implication."""
    text = (
        "\nTRUTH TABLE:\np | q | p => q\nT | T | T\nT | F | F\nF | T | T\nF | F | T\n"
    )
    table = parse_truth_table(text)
    assert table.headers == ["p", "q", "p => q"]
    assert len(table.rows) == 4


def test_truth_table_complex_header() -> None:
    """Test truth table with complex expressions elem header."""
    text = (
        "\nTRUTH TABLE:\np | q | p land q | (p land q) => p\n"
        "T | T | T | T\nT | F | F | T\nF | T | F | T\nF | F | F | T\n"
    )
    table = parse_truth_table(text)
    assert len(table.headers) == 4
    assert table.headers[3] == "( p land q ) => p"


def test_truth_table_with_lowercase() -> None:
    """Test truth table with lowercase t/f values."""
    text = "\nTRUTH TABLE:\np | q\nt | t\nt | f\nf | t\nf | f\n"
    table = parse_truth_table(text)
    assert table.rows[0] == ["T", "T"]
    assert table.rows[1] == ["T", "F"]


def test_truth_table_with_iff() -> None:
    """Test truth table with biconditional."""
    text = (
        "\nTRUTH TABLE:\np | q | p <=> q\nT | T | T\nT | F | F\nF | T | F\nF | F | T\n"
    )
    table = parse_truth_table(text)
    assert table.headers == ["p", "q", "p <=> q"]
    assert table.rows[0] == ["T", "T", "T"]
    assert table.rows[1] == ["T", "F", "F"]


def test_truth_table_latex_generation() -> None:
    """Test LaTeX generation for truth tables."""
    text = (
        "\nTRUTH TABLE:\np | q | p land q\nT | T | T\nT | F | F\nF | T | F\nF | F | F\n"
    )
    table = parse_truth_table(text)
    generator = LaTeXGenerator()
    latex_lines = generator._generate_truth_table(table)
    latex = "\n".join(latex_lines)
    assert "\\begin{tabular}" in latex
    assert "\\end{tabular}" in latex
    assert "p" in latex
    assert "q" in latex
    assert "p land q" in latex or "p \\land q" in latex
    assert "\\hline" in latex


def test_truth_table_with_or() -> None:
    """Test truth table with OR operator."""
    text = (
        "\nTRUTH TABLE:\np | q | p lor q\nT | T | T\nT | F | T\nF | T | T\nF | F | F\n"
    )
    table = parse_truth_table(text)
    assert table.headers == ["p", "q", "p lor q"]
    assert table.rows[0] == ["T", "T", "T"]
    assert table.rows[3] == ["F", "F", "F"]


def test_truth_table_with_not() -> None:
    """Test truth table with NOT operator."""
    text = "\nTRUTH TABLE:\np | lnot p | lnot (lnot p)\nT | F | T\nF | T | F\n"
    table = parse_truth_table(text)
    assert len(table.headers) == 3
    assert len(table.rows) == 2


def test_truth_table_three_variables() -> None:
    """Test truth table with three variables."""
    text = (
        "\nTRUTH TABLE:\np | q | r | p land q land r\n"
        "T | T | T | T\nT | T | F | F\nT | F | T | F\nT | F | F | F\n"
        "F | T | T | F\nF | T | F | F\nF | F | T | F\nF | F | F | F\n"
    )
    table = parse_truth_table(text)
    assert len(table.headers) == 4
    assert len(table.rows) == 8
    assert table.rows[0] == ["T", "T", "T", "T"]
    assert table.rows[7] == ["F", "F", "F", "F"]


def test_truth_table_phase19_f_token() -> None:
    """Test that F token (from Phase 19 FINSET) works elem truth tables."""
    text = "\nTRUTH TABLE:\np | q\nF | F\nF | T\nT | F\nT | T\n"
    table = parse_truth_table(text)
    assert table.rows[0] == ["F", "F"]
    assert table.rows[1] == ["F", "T"]
    assert table.rows[2] == ["T", "F"]
    assert table.rows[3] == ["T", "T"]
