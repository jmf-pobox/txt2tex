"""Tests for Phase 1: Multi-line document support."""

from txt2tex.ast_nodes import BinaryOp, Document, Identifier, UnaryOp
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

        assert r"\documentclass{article}" in latex
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

        assert r"\documentclass{article}" in latex
        assert r"\usepackage{zed-cm}" in latex
        assert r"$p \land q$" in latex
        assert r"$p \lor q$" in latex
        assert r"\end{document}" in latex

    def test_generate_empty_document(self) -> None:
        """Test LaTeX generation for empty document."""
        gen = LaTeXGenerator()
        doc = Document(items=[], line=1, column=1)

        latex = gen.generate_document(doc)

        assert r"\documentclass{article}" in latex
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
        assert r"$p \land q$" in latex
        assert r"$p \lor q$" in latex
        assert r"$\lnot p$" in latex

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

        assert r"$p \land q \Rightarrow p$" in latex
        # Nested implications now have explicit parentheses for clarity
        assert r"$p \Rightarrow (q \Rightarrow r)$" in latex
        assert r"$\lnot p \land q$" in latex
