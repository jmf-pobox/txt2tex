"""Tests for equivalence chains with justifications."""

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


class TestEquivalenceParsing:
    """Test parsing of equivalence chains."""

    def test_simple_equiv_chain_no_justifications(self) -> None:
        """Test parsing simple equivalence chain without justifications."""
        text = "EQUIV:\np land q\nq land p"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Document)
        assert len(ast.items) == 1
        equiv = ast.items[0]
        assert isinstance(equiv, EquivChain)
        assert len(equiv.steps) == 2
        step1 = equiv.steps[0]
        assert isinstance(step1, EquivStep)
        assert isinstance(step1.expression, BinaryOp)
        assert step1.expression.operator == "land"
        assert step1.justification is None
        step2 = equiv.steps[1]
        assert isinstance(step2, EquivStep)
        assert isinstance(step2.expression, BinaryOp)
        assert step2.expression.operator == "land"
        assert step2.justification is None

    def test_equiv_chain_with_justifications(self) -> None:
        """Test parsing equivalence chain with justifications."""
        text = "EQUIV:\np land q\nq land p [commutative]\np land q [idempotent]"
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
        assert equiv.steps[2].justification == "idempotent"

    def test_equiv_chain_mixed_justifications(self) -> None:
        """Test equivalence chain with some steps having justifications."""
        text = "EQUIV:\np land q\nq land p [commutative]\nq land p"
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
        text = (
            "EQUIV:\nlnot (p land q)\n"
            "(lnot p) lor (lnot q) [De Morgan]\n"
            "lnot p lor lnot q [parentheses]"
        )
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Document)
        equiv = ast.items[0]
        assert isinstance(equiv, EquivChain)
        assert len(equiv.steps) == 3
        assert equiv.steps[0].justification is None
        assert equiv.steps[1].justification == "De Morgan"
        assert equiv.steps[2].justification == "parentheses"

    def test_equiv_chain_with_implies(self) -> None:
        """Test equivalence chain with implication operators."""
        text = "EQUIV:\np => q\nlnot p lor q [definition]"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Document)
        equiv = ast.items[0]
        assert isinstance(equiv, EquivChain)
        assert len(equiv.steps) == 2
        assert isinstance(equiv.steps[0].expression, BinaryOp)
        assert equiv.steps[0].expression.operator == "=>"
        assert isinstance(equiv.steps[1].expression, BinaryOp)
        assert equiv.steps[1].expression.operator == "lor"
        assert equiv.steps[1].justification == "definition"

    def test_multiple_equiv_chains(self) -> None:
        """Test document with multiple equivalence chains."""
        text = "EQUIV:\np land q\nq land p\n\nEQUIV:\np lor q\nq lor p"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Document)
        assert len(ast.items) == 2
        assert isinstance(ast.items[0], EquivChain)
        assert isinstance(ast.items[1], EquivChain)
        assert len(ast.items[0].steps) == 2
        assert len(ast.items[1].steps) == 2


class TestEquivalenceLaTeX:
    """Test LaTeX generation for equivalence chains."""

    def test_generate_equiv_chain_no_justifications(self) -> None:
        """Test LaTeX generation for equivalence chain without justifications."""
        gen = LaTeXGenerator()
        equiv = EquivChain(
            steps=[
                EquivStep(
                    expression=BinaryOp(
                        operator="land",
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
                        operator="land",
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
        lines = gen._generate_argue_chain(equiv)
        latex = "\n".join(lines)
        assert "\\begin{array}" in latex
        assert "\\end{array}" in latex
        assert "p \\land q" in latex
        assert "\\Leftrightarrow q \\land p" in latex
        assert "p \\land q \\\\" in latex
        assert not latex.strip().endswith("\\\\")

    def test_generate_equiv_chain_with_justifications(self) -> None:
        """Test LaTeX generation for equivalence chain with justifications."""
        gen = LaTeXGenerator()
        equiv = EquivChain(
            steps=[
                EquivStep(
                    expression=BinaryOp(
                        operator="land",
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
                        operator="land",
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
        lines = gen._generate_argue_chain(equiv)
        latex = "\n".join(lines)
        assert "\\begin{array}" in latex
        assert "\\end{array}" in latex
        assert "p \\land q" in latex
        assert "\\Leftrightarrow q \\land p & [\\mbox{commutative}]" in latex

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
        assert "\\documentclass[a4paper,10pt,fleqn]{article}" in latex
        assert "\\usepackage{zed-cm}" in latex
        assert "\\usepackage{amssymb}" in latex
        assert "\\begin{array}" in latex
        assert "p \\\\" in latex
        assert "\\Leftrightarrow q & [\\mbox{assumption}]" in latex
        assert "\\end{array}" in latex
        assert "\\end{document}" in latex


class TestEquivalenceIntegration:
    """Integration tests for equivalence chains."""

    def test_end_to_end_equiv_chain(self) -> None:
        """Test complete pipeline from text to LaTeX for equivalence chain."""
        text = "EQUIV:\np land q\nq land p [commutative]"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert isinstance(ast, Document)
        assert len(ast.items) == 1
        assert isinstance(ast.items[0], EquivChain)
        assert "\\begin{array}" in latex
        assert "p \\land q" in latex
        assert "\\Leftrightarrow q \\land p & [\\mbox{commutative}]" in latex
        assert "\\end{array}" in latex

    def test_end_to_end_complex_equiv(self) -> None:
        """Test complete pipeline with complex equivalence chain."""
        text = (
            "EQUIV:\nlnot (p land q)\n"
            "(lnot p) lor (lnot q) [De Morgan]\n"
            "lnot p lor lnot q [parentheses]"
        )
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
        assert "\\begin{array}" in latex
        assert "\\lnot" in latex
        assert "\\land" in latex
        assert "\\lor" in latex
        assert "\\mbox{De Morgan}" in latex
        assert "\\mbox{parentheses}" in latex
        assert "\\end{array}" in latex

    def test_equiv_chain_mixed_with_expressions(self) -> None:
        """Test equivalence chain mixed with regular expressions."""
        text = "p land q\n\nEQUIV:\np lor q\nq lor p [commutative]\n\n(a) lnot p"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Document)
        assert len(ast.items) == 3
        assert isinstance(ast.items[0], BinaryOp)
        assert isinstance(ast.items[1], EquivChain)
        assert len(ast.items[1].steps) == 2
        assert isinstance(ast.items[2], Part)
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "p \\land q" in latex
        assert "\\begin{array}" in latex
        assert "\\lnot p" in latex
        assert "\\end{array}" in latex
