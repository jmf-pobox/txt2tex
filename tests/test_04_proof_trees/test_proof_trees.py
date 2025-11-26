"""Tests for Phase 5: Proof Trees (Path C format)."""

from __future__ import annotations

from txt2tex.ast_nodes import (
    BinaryOp,
    CaseAnalysis,
    Document,
    Identifier,
    ProofNode,
    ProofTree,
)
from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser


class TestLexer:
    """Tests for Phase 5 lexer features."""

    def test_proof_keyword(self) -> None:
        """Test lexing PROOF: keyword."""
        lexer = Lexer("PROOF:")
        tokens = lexer.tokenize()
        assert tokens[0].type.name == "PROOF"
        assert tokens[0].value == "PROOF:"

    def test_double_colon(self) -> None:
        """Test lexing :: sibling marker."""
        lexer = Lexer(":: p")
        tokens = lexer.tokenize()
        assert tokens[0].type.name == "DOUBLE_COLON"
        assert tokens[0].value == "::"


class TestParser:
    """Tests for Phase 5 parser features."""

    def test_simple_proof_tree(self) -> None:
        """Test parsing simple proof tree with conclusion land one premise."""
        text = "PROOF:\np\n  q"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Document)
        assert len(ast.items) == 1
        proof_tree = ast.items[0]
        assert isinstance(proof_tree, ProofTree)
        conclusion = proof_tree.conclusion
        assert isinstance(conclusion, ProofNode)
        assert isinstance(conclusion.expression, Identifier)
        assert conclusion.expression.name == "p"
        assert len(conclusion.children) == 1
        premise = conclusion.children[0]
        assert isinstance(premise, ProofNode)
        assert isinstance(premise.expression, Identifier)
        assert premise.expression.name == "q"

    def test_proof_tree_with_justification(self) -> None:
        """Test parsing proof tree with justifications."""
        text = "PROOF:\np [conclusion]\n  q [premise]"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Document)
        proof_tree = ast.items[0]
        assert isinstance(proof_tree, ProofTree)
        assert proof_tree.conclusion.justification == "conclusion"
        premise = proof_tree.conclusion.children[0]
        assert isinstance(premise, ProofNode)
        assert premise.justification == "premise"

    def test_assumption_label(self) -> None:
        """Test parsing assumption labels [1], [2], etc."""
        text = (
            "PROOF:\np => q [=> intro from 1]\n  [1] p [assumption]\n      q [from p]"
        )
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Document)
        proof_tree = ast.items[0]
        assert isinstance(proof_tree, ProofTree)
        conclusion = proof_tree.conclusion
        assert conclusion.justification == "=> intro from 1"
        assert conclusion.label is None
        assert not conclusion.is_assumption
        assert len(conclusion.children) == 1
        assumption = conclusion.children[0]
        assert isinstance(assumption, ProofNode)
        assert assumption.label == 1
        assert assumption.is_assumption
        assert assumption.justification == "assumption"

    def test_sibling_premises(self) -> None:
        """Test parsing sibling premises with :: marker."""
        text = "PROOF:\np land q [land intro]\n  :: p [premise]\n  :: q [premise]"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Document)
        proof_tree = ast.items[0]
        assert isinstance(proof_tree, ProofTree)
        conclusion = proof_tree.conclusion
        assert len(conclusion.children) == 2
        first = conclusion.children[0]
        assert isinstance(first, ProofNode)
        assert first.is_sibling
        assert isinstance(first.expression, Identifier)
        assert first.expression.name == "p"
        second = conclusion.children[1]
        assert isinstance(second, ProofNode)
        assert second.is_sibling
        assert isinstance(second.expression, Identifier)
        assert second.expression.name == "q"

    def test_case_analysis(self) -> None:
        """Test parsing case analysis."""
        text = (
            "PROOF:\np lor q => r [lor elim]\n  case p:\n    r [from p]\n"
            "  case q:\n    r [from q]"
        )
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Document)
        proof_tree = ast.items[0]
        assert isinstance(proof_tree, ProofTree)
        conclusion = proof_tree.conclusion
        assert len(conclusion.children) == 2
        case1 = conclusion.children[0]
        assert isinstance(case1, CaseAnalysis)
        assert case1.case_name == "p"
        assert len(case1.steps) == 1
        step1 = case1.steps[0]
        assert isinstance(step1.expression, Identifier)
        assert step1.expression.name == "r"
        case2 = conclusion.children[1]
        assert isinstance(case2, CaseAnalysis)
        assert case2.case_name == "q"
        assert len(case2.steps) == 1

    def test_nested_structure(self) -> None:
        """Test parsing nested proof structure."""
        text = "PROOF:\np\n  q\n    r"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Document)
        proof_tree = ast.items[0]
        assert isinstance(proof_tree, ProofTree)
        conclusion = proof_tree.conclusion
        assert len(conclusion.children) == 1
        q_node = conclusion.children[0]
        assert isinstance(q_node, ProofNode)
        assert isinstance(q_node.expression, Identifier)
        assert q_node.expression.name == "q"
        assert len(q_node.children) == 1
        r_node = q_node.children[0]
        assert isinstance(r_node, ProofNode)
        assert isinstance(r_node.expression, Identifier)
        assert r_node.expression.name == "r"

    def test_complex_expression(self) -> None:
        """Test parsing proof tree with complex expressions."""
        text = (
            "PROOF:\np land q => q [=> intro from 1]\n"
            "  [1] p land q [assumption]\n      q [land elim]"
        )
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Document)
        proof_tree = ast.items[0]
        assert isinstance(proof_tree, ProofTree)
        conclusion = proof_tree.conclusion
        assert isinstance(conclusion.expression, BinaryOp)
        assert conclusion.expression.operator == "=>"


class TestLaTeXGenerator:
    """Tests for Phase 5 LaTeX generator."""

    def test_simple_proof_tree(self) -> None:
        """Test generating simple proof tree with \\infer macro."""
        gen = LaTeXGenerator()
        ast = ProofTree(
            conclusion=ProofNode(
                expression=Identifier(name="p", line=2, column=1),
                justification="rule",
                label=None,
                is_assumption=False,
                is_sibling=False,
                children=[
                    ProofNode(
                        expression=Identifier(name="q", line=3, column=3),
                        justification=None,
                        label=None,
                        is_assumption=False,
                        is_sibling=False,
                        children=[],
                        indent_level=2,
                        line=3,
                        column=3,
                    )
                ],
                indent_level=0,
                line=2,
                column=1,
            ),
            line=1,
            column=1,
        )
        latex_lines = gen.generate_document_item(ast)
        latex = "\n".join(latex_lines)
        assert "\\infer" in latex
        assert "\\begin{itemize}" not in latex
        assert "\\begin{center}" in latex
        assert "\\end{center}" in latex
        assert "p" in latex
        assert "q" in latex

    def test_proof_tree_with_justification(self) -> None:
        """Test generating proof tree with justification label."""
        gen = LaTeXGenerator()
        ast = ProofTree(
            conclusion=ProofNode(
                expression=Identifier(name="p", line=2, column=1),
                justification="and elim",
                label=None,
                is_assumption=False,
                is_sibling=False,
                children=[],
                indent_level=0,
                line=2,
                column=1,
            ),
            line=1,
            column=1,
        )
        latex_lines = gen.generate_document_item(ast)
        latex = "\n".join(latex_lines)
        assert "\\infer[" in latex
        assert "elim" in latex

    def test_sibling_premises(self) -> None:
        """Test generating siblings with & separator."""
        gen = LaTeXGenerator()
        ast = ProofTree(
            conclusion=ProofNode(
                expression=BinaryOp(
                    operator="land",
                    left=Identifier(name="p", line=2, column=1),
                    right=Identifier(name="q", line=2, column=7),
                    line=2,
                    column=3,
                ),
                justification="land intro",
                label=None,
                is_assumption=False,
                is_sibling=False,
                children=[
                    ProofNode(
                        expression=Identifier(name="p", line=3, column=5),
                        justification=None,
                        label=None,
                        is_assumption=False,
                        is_sibling=True,
                        children=[],
                        indent_level=2,
                        line=3,
                        column=5,
                    ),
                    ProofNode(
                        expression=Identifier(name="q", line=4, column=5),
                        justification=None,
                        label=None,
                        is_assumption=False,
                        is_sibling=True,
                        children=[],
                        indent_level=2,
                        line=4,
                        column=5,
                    ),
                ],
                indent_level=0,
                line=2,
                column=1,
            ),
            line=1,
            column=1,
        )
        latex_lines = gen.generate_document_item(ast)
        latex = "\n".join(latex_lines)
        assert "\n&\n" in latex
        assert "\\infer" in latex


class TestIntegration:
    """End-to-end integration tests for Phase 5."""

    def test_simple_implication(self) -> None:
        """Test complete pipeline for simple implication proof."""
        text = (
            "PROOF:\np land q => q [=> intro from 1]\n"
            "  [1] p land q [assumption]\n      q [land elim]"
        )
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        doc = gen.generate_document(ast)
        assert "\\infer" in doc
        assert "\\begin{itemize}" not in doc
        assert "p \\land q \\Rightarrow q" in doc
        assert "\\begin{center}" in doc
        assert "\\end{center}" in doc

    def test_sibling_premises_integration(self) -> None:
        """Test complete pipeline with sibling premises."""
        text = (
            "PROOF:\np land (p => q) => (p land q) [=> intro from 1]\n"
            "  [1] p land (p => q) [assumption]\n      :: p [land elim]\n"
            "      :: p => q [land elim]\n      q [=> elim]\n"
            "      p land q [land intro]"
        )
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        doc = gen.generate_document(ast)
        assert " & " in doc
        assert "\\infer" in doc

    def test_case_analysis_integration(self) -> None:
        """Test complete pipeline with case analysis."""
        text = (
            "PROOF:\np lor q => r [lor elim]\n  case p:\n    r [from p]\n"
            "  case q:\n    r [from q]"
        )
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        doc = gen.generate_document(ast)
        assert "\\infer" in doc
        assert "r" in doc
