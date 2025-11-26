"""Tests for INFRULE: block syntax and shows operator."""

from txt2tex.ast_nodes import BinaryOp, Document, Identifier, InfruleBlock
from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser


class TestInfruleParsing:
    """Test parsing of INFRULE blocks."""

    def test_simple_infrule(self) -> None:
        """Test simple inference rule with one premise."""
        text = """INFRULE:
Premise
---
Conclusion"""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        assert isinstance(ast, Document)
        assert len(ast.items) == 1
        item = ast.items[0]
        assert isinstance(item, InfruleBlock)
        assert len(item.premises) == 1
        assert isinstance(item.premises[0][0], Identifier)
        assert item.premises[0][0].name == "Premise"
        assert item.premises[0][1] is None  # No label
        assert isinstance(item.conclusion[0], Identifier)
        assert item.conclusion[0].name == "Conclusion"
        assert item.conclusion[1] is None  # No label

    def test_infrule_with_multiple_premises(self) -> None:
        """Test inference rule with multiple premises."""
        text = """INFRULE:
A
A => B
---
B"""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        assert isinstance(ast, Document)
        assert len(ast.items) == 1
        item = ast.items[0]
        assert isinstance(item, InfruleBlock)
        assert len(item.premises) == 2
        # First premise: A
        assert isinstance(item.premises[0][0], Identifier)
        assert item.premises[0][0].name == "A"
        # Second premise: A => B
        assert isinstance(item.premises[1][0], BinaryOp)
        assert item.premises[1][0].operator == "=>"

    def test_infrule_with_labels(self) -> None:
        """Test inference rule with labels."""
        text = """INFRULE:
A [premise]
A => B [implication]
---
B [modus ponens]"""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        assert isinstance(ast, Document)
        assert len(ast.items) == 1
        item = ast.items[0]
        assert isinstance(item, InfruleBlock)
        assert len(item.premises) == 2
        assert item.premises[0][1] == "premise"
        assert item.premises[1][1] == "implication"
        assert item.conclusion[1] == "modus ponens"


class TestInfruleLaTeXGeneration:
    """Test LaTeX generation for INFRULE blocks."""

    def test_generate_simple_infrule(self) -> None:
        """Test LaTeX generation for simple inference rule."""
        gen = LaTeXGenerator()
        infrule = InfruleBlock(
            premises=[
                (Identifier(name="Premise", line=1, column=1), None),
            ],
            conclusion=(Identifier(name="Conclusion", line=3, column=1), None),
            line=1,
            column=1,
        )

        lines = gen._generate_infrule_block(infrule)
        latex = "\n".join(lines)

        assert r"\begin{infrule}" in latex
        assert r"Premise &" in latex
        assert r"\derive" in latex
        assert r"Conclusion &" in latex
        assert r"\end{infrule}" in latex

    def test_generate_infrule_with_labels(self) -> None:
        """Test LaTeX generation with labels."""
        gen = LaTeXGenerator()
        infrule = InfruleBlock(
            premises=[
                (Identifier(name="Premise", line=1, column=1), "premise"),
            ],
            conclusion=(Identifier(name="Conclusion", line=3, column=1), "conclusion"),
            line=1,
            column=1,
        )

        lines = gen._generate_infrule_block(infrule)
        latex = "\n".join(lines)

        assert r"\mbox{premise}" in latex
        assert r"\mbox{conclusion}" in latex


class TestShowsOperator:
    """Test shows operator (sequent judgment)."""

    def test_shows_parsing(self) -> None:
        """Test parsing of shows operator."""
        text = """Gamma shows Delta"""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        # Parse returns BinaryOp directly for single expression
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "shows"
        assert isinstance(ast.left, Identifier)
        assert ast.left.name == "Gamma"
        assert isinstance(ast.right, Identifier)
        assert ast.right.name == "Delta"

    def test_shows_latex_generation(self) -> None:
        """Test LaTeX generation for shows operator."""
        gen = LaTeXGenerator()
        expr = BinaryOp(
            operator="shows",
            left=Identifier(name="Gamma", line=1, column=1),
            right=Identifier(name="Delta", line=1, column=13),
            line=1,
            column=7,
        )

        latex = gen.generate_expr(expr)
        assert r"\shows" in latex
        assert "Gamma" in latex
        assert "Delta" in latex


class TestInfruleIntegration:
    """Integration tests for INFRULE."""

    def test_end_to_end_infrule(self) -> None:
        """Test complete pipeline from text to LaTeX."""
        text = """INFRULE:
A
A => B
---
B [modus ponens]"""

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
        assert r"\begin{infrule}" in latex
        assert r"A &" in latex
        assert r"A \implies B" in latex or r"A \Rightarrow B" in latex
        assert r"\derive" in latex
        assert r"B & \mbox{modus ponens}" in latex
        assert r"\end{infrule}" in latex
