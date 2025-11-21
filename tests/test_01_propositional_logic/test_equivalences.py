"""Tests for Phase 2: Equivalence chains with justifications."""

from txt2tex.ast_nodes import (
    BinaryOp,
    Document,
    EquivChain,
    EquivStep,
    Identifier,
    Part,
)
from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser


class TestPhase2Parsing:
    """Test parsing of equivalence chains."""

    def test_simple_equiv_chain_no_justifications(self) -> None:
        """Test parsing simple equivalence chain without justifications."""
        text = """EQUIV:
p and q
q and p"""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        assert isinstance(ast, Document)
        assert len(ast.items) == 1

        equiv = ast.items[0]
        assert isinstance(equiv, EquivChain)
        assert len(equiv.steps) == 2

        # First step
        step1 = equiv.steps[0]
        assert isinstance(step1, EquivStep)
        assert isinstance(step1.expression, BinaryOp)
        assert step1.expression.operator == "and"
        assert step1.justification is None

        # Second step
        step2 = equiv.steps[1]
        assert isinstance(step2, EquivStep)
        assert isinstance(step2.expression, BinaryOp)
        assert step2.expression.operator == "and"
        assert step2.justification is None

    def test_equiv_chain_with_justifications(self) -> None:
        """Test parsing equivalence chain with justifications."""
        text = """EQUIV:
p and q
q and p [commutative]
p and q [idempotent]"""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        assert isinstance(ast, Document)
        equiv = ast.items[0]
        assert isinstance(equiv, EquivChain)
        assert len(equiv.steps) == 3

        # First step - no justification
        assert equiv.steps[0].justification is None

        # Second step - has justification
        assert equiv.steps[1].justification == "commutative"

        # Third step - has justification
        assert equiv.steps[2].justification == "idempotent"

    def test_equiv_chain_mixed_justifications(self) -> None:
        """Test equivalence chain with some steps having justifications."""
        text = """EQUIV:
p and q
q and p [commutative]
q and p"""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        assert isinstance(ast, Document)
        equiv = ast.items[0]
        assert isinstance(equiv, EquivChain)
        assert len(equiv.steps) == 3

        assert equiv.steps[0].justification is None
        assert equiv.steps[1].justification == "commutative"
        assert equiv.steps[2].justification is None

    def test_equiv_chain_complex_expressions(self) -> None:
        """Test equivalence chain with complex expressions."""
        text = """EQUIV:
not (p and q)
(not p) or (not q) [De Morgan]
not p or not q [parentheses]"""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        assert isinstance(ast, Document)
        equiv = ast.items[0]
        assert isinstance(equiv, EquivChain)
        assert len(equiv.steps) == 3

        # Verify justifications
        assert equiv.steps[0].justification is None
        assert equiv.steps[1].justification == "De Morgan"
        assert equiv.steps[2].justification == "parentheses"

    def test_equiv_chain_with_implies(self) -> None:
        """Test equivalence chain with implication operators."""
        text = """EQUIV:
p => q
not p or q [definition]"""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        assert isinstance(ast, Document)
        equiv = ast.items[0]
        assert isinstance(equiv, EquivChain)
        assert len(equiv.steps) == 2

        # First step
        assert isinstance(equiv.steps[0].expression, BinaryOp)
        assert equiv.steps[0].expression.operator == "=>"

        # Second step
        assert isinstance(equiv.steps[1].expression, BinaryOp)
        assert equiv.steps[1].expression.operator == "or"
        assert equiv.steps[1].justification == "definition"

    def test_multiple_equiv_chains(self) -> None:
        """Test document with multiple equivalence chains."""
        text = """EQUIV:
p and q
q and p

EQUIV:
p or q
q or p"""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        assert isinstance(ast, Document)
        assert len(ast.items) == 2

        # Both items should be equivalence chains
        assert isinstance(ast.items[0], EquivChain)
        assert isinstance(ast.items[1], EquivChain)

        # First chain
        assert len(ast.items[0].steps) == 2

        # Second chain
        assert len(ast.items[1].steps) == 2


class TestPhase2LaTeXGeneration:
    """Test LaTeX generation for equivalence chains."""

    def test_generate_equiv_chain_no_justifications(self) -> None:
        """Test LaTeX generation for equivalence chain without justifications."""
        gen = LaTeXGenerator()
        equiv = EquivChain(
            steps=[
                EquivStep(
                    expression=BinaryOp(
                        operator="and",
                        left=Identifier(name="p", line=2, column=1),
                        right=Identifier(name="q", line=2, column=5),
                        line=2,
                        column=3,
                    ),
                    justification=None,
                    line=2,
                    column=1,
                ),
                EquivStep(
                    expression=BinaryOp(
                        operator="and",
                        left=Identifier(name="q", line=3, column=1),
                        right=Identifier(name="p", line=3, column=5),
                        line=3,
                        column=3,
                    ),
                    justification=None,
                    line=3,
                    column=1,
                ),
            ],
            line=1,
            column=1,
        )

        lines = gen._generate_equiv_chain(equiv)
        latex = "\n".join(lines)

        assert r"\begin{center}" in latex
        assert r"$\displaystyle" in latex
        assert r"\begin{array}{l@{\hspace{2em}}r}" in latex
        assert r"\end{array}$" in latex
        assert r"\end{center}" in latex
        assert r"p \land q" in latex
        assert r"\Leftrightarrow q \land p" in latex
        # Check that first line has \\ but last doesn't (before \end{array})
        assert r"p \land q \\" in latex
        assert not latex.strip().endswith(r"\\")

    def test_generate_equiv_chain_with_justifications(self) -> None:
        """Test LaTeX generation for equivalence chain with justifications."""
        gen = LaTeXGenerator()
        equiv = EquivChain(
            steps=[
                EquivStep(
                    expression=BinaryOp(
                        operator="and",
                        left=Identifier(name="p", line=2, column=1),
                        right=Identifier(name="q", line=2, column=5),
                        line=2,
                        column=3,
                    ),
                    justification=None,
                    line=2,
                    column=1,
                ),
                EquivStep(
                    expression=BinaryOp(
                        operator="and",
                        left=Identifier(name="q", line=3, column=1),
                        right=Identifier(name="p", line=3, column=5),
                        line=3,
                        column=3,
                    ),
                    justification="commutative",
                    line=3,
                    column=1,
                ),
            ],
            line=1,
            column=1,
        )

        lines = gen._generate_equiv_chain(equiv)
        latex = "\n".join(lines)

        assert r"\begin{center}" in latex
        assert r"$\displaystyle" in latex
        assert r"\begin{array}{l@{\hspace{2em}}r}" in latex
        assert r"\end{array}$" in latex
        assert r"\end{center}" in latex
        assert r"p \land q" in latex
        assert r"\Leftrightarrow q \land p & [\mbox{commutative}]" in latex

    def test_generate_document_with_equiv_chain(self) -> None:
        """Test complete document generation with equivalence chain."""
        gen = LaTeXGenerator()
        equiv = EquivChain(
            steps=[
                EquivStep(
                    expression=Identifier(name="p", line=2, column=1),
                    justification=None,
                    line=2,
                    column=1,
                ),
                EquivStep(
                    expression=Identifier(name="q", line=3, column=1),
                    justification="assumption",
                    line=3,
                    column=1,
                ),
            ],
            line=1,
            column=1,
        )
        doc = Document(items=[equiv], line=1, column=1)

        latex = gen.generate_document(doc)

        assert r"\documentclass[a4paper,10pt,fleqn]{article}" in latex
        assert r"\usepackage{zed-cm}" in latex
        assert r"\usepackage{amssymb}" in latex  # amsmath removed - using array
        assert r"\begin{center}" in latex
        assert r"$\displaystyle" in latex
        assert r"\begin{array}{l@{\hspace{2em}}r}" in latex
        assert r"p \\" in latex
        assert r"\Leftrightarrow q & [\mbox{assumption}]" in latex
        assert r"\end{array}$" in latex
        assert r"\end{center}" in latex
        assert r"\end{document}" in latex


class TestPhase2Integration:
    """Integration tests for Phase 2."""

    def test_end_to_end_equiv_chain(self) -> None:
        """Test complete pipeline from text to LaTeX for equivalence chain."""
        text = """EQUIV:
p and q
q and p [commutative]"""

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
        assert len(ast.items) == 1
        assert isinstance(ast.items[0], EquivChain)
        assert r"\begin{center}" in latex
        assert r"$\displaystyle" in latex
        assert r"\begin{array}{l@{\hspace{2em}}r}" in latex
        assert r"p \land q" in latex
        assert r"\Leftrightarrow q \land p & [\mbox{commutative}]" in latex
        assert r"\end{array}$" in latex
        assert r"\end{center}" in latex

    def test_end_to_end_complex_equiv(self) -> None:
        """Test complete pipeline with complex equivalence chain."""
        text = """EQUIV:
not (p and q)
(not p) or (not q) [De Morgan]
not p or not q [parentheses]"""

        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        assert isinstance(ast, Document)
        assert len(ast.items) == 1
        equiv = ast.items[0]
        assert isinstance(equiv, EquivChain)
        assert len(equiv.steps) == 3

        # Check LaTeX output
        assert r"\begin{center}" in latex
        assert r"$\displaystyle" in latex
        assert r"\begin{array}{l@{\hspace{2em}}r}" in latex
        assert r"\lnot" in latex
        assert r"\land" in latex
        assert r"\lor" in latex
        assert r"[\mbox{De Morgan}]" in latex
        assert r"[\mbox{parentheses}]" in latex
        assert r"\end{array}$" in latex
        assert r"\end{center}" in latex

    def test_equiv_chain_mixed_with_expressions(self) -> None:
        """Test equivalence chain mixed with regular expressions."""
        text = """p and q

EQUIV:
p or q
q or p [commutative]

(a) not p"""

        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        assert isinstance(ast, Document)
        assert len(ast.items) == 3

        # First item: expression
        assert isinstance(ast.items[0], BinaryOp)

        # Second item: equiv chain
        assert isinstance(ast.items[1], EquivChain)
        assert len(ast.items[1].steps) == 2

        # Third item: part (structural element stops the equiv chain)
        assert isinstance(ast.items[2], Part)

        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # Should have both left-aligned expressions and centered array in display math
        assert r"p \land q" in latex
        assert r"\begin{center}" in latex
        assert r"$\displaystyle" in latex
        assert r"\begin{array}{l@{\hspace{2em}}r}" in latex
        assert r"\lnot p" in latex
        assert r"\end{array}$" in latex
        assert r"\end{center}" in latex
