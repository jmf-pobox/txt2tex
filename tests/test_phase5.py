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
        """Test parsing simple proof tree with conclusion and one premise."""
        text = """PROOF:
p
  q"""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        # Document with one ProofTree item
        assert isinstance(ast, Document)
        assert len(ast.items) == 1
        proof_tree = ast.items[0]
        assert isinstance(proof_tree, ProofTree)

        # Check conclusion
        conclusion = proof_tree.conclusion
        assert isinstance(conclusion, ProofNode)
        assert isinstance(conclusion.expression, Identifier)
        assert conclusion.expression.name == "p"

        # Check premise
        assert len(conclusion.children) == 1
        premise = conclusion.children[0]
        assert isinstance(premise, ProofNode)
        assert isinstance(premise.expression, Identifier)
        assert premise.expression.name == "q"

    def test_proof_tree_with_justification(self) -> None:
        """Test parsing proof tree with justifications."""
        text = """PROOF:
p [conclusion]
  q [premise]"""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        proof_tree = ast.items[0]
        assert isinstance(proof_tree, ProofTree)
        assert proof_tree.conclusion.justification == "conclusion"
        assert proof_tree.conclusion.children[0].justification == "premise"

    def test_assumption_label(self) -> None:
        """Test parsing assumption labels [1], [2], etc."""
        text = """PROOF:
p => q [=> intro from 1]
  [1] p [assumption]
      q [from p]"""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        proof_tree = ast.items[0]
        assert isinstance(proof_tree, ProofTree)

        # Check conclusion
        conclusion = proof_tree.conclusion
        assert conclusion.justification == "=> intro from 1"
        assert conclusion.label is None
        assert not conclusion.is_assumption

        # Check assumption
        assert len(conclusion.children) == 1
        assumption = conclusion.children[0]
        assert assumption.label == 1
        assert assumption.is_assumption
        assert assumption.justification == "assumption"

    def test_sibling_premises(self) -> None:
        """Test parsing sibling premises with :: marker."""
        text = """PROOF:
p and q [and intro]
  :: p [premise]
  :: q [premise]"""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        proof_tree = ast.items[0]
        conclusion = proof_tree.conclusion

        # Check that we have two children
        assert len(conclusion.children) == 2

        # Check first sibling
        first = conclusion.children[0]
        assert first.is_sibling
        assert isinstance(first.expression, Identifier)
        assert first.expression.name == "p"

        # Check second sibling
        second = conclusion.children[1]
        assert second.is_sibling
        assert isinstance(second.expression, Identifier)
        assert second.expression.name == "q"

    def test_case_analysis(self) -> None:
        """Test parsing case analysis."""
        text = """PROOF:
p or q => r [or elim]
  case p:
    r [from p]
  case q:
    r [from q]"""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        proof_tree = ast.items[0]
        conclusion = proof_tree.conclusion

        # Check that we have two case branches
        assert len(conclusion.children) == 2

        # Check first case
        case1 = conclusion.children[0]
        assert isinstance(case1, CaseAnalysis)
        assert case1.case_name == "p"
        assert len(case1.steps) == 1
        assert isinstance(case1.steps[0].expression, Identifier)
        assert case1.steps[0].expression.name == "r"

        # Check second case
        case2 = conclusion.children[1]
        assert isinstance(case2, CaseAnalysis)
        assert case2.case_name == "q"
        assert len(case2.steps) == 1

    def test_nested_structure(self) -> None:
        """Test parsing nested proof structure."""
        text = """PROOF:
p
  q
    r"""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        proof_tree = ast.items[0]
        conclusion = proof_tree.conclusion

        # p has child q
        assert len(conclusion.children) == 1
        q_node = conclusion.children[0]
        assert isinstance(q_node.expression, Identifier)
        assert q_node.expression.name == "q"

        # q has child r
        assert len(q_node.children) == 1
        r_node = q_node.children[0]
        assert isinstance(r_node.expression, Identifier)
        assert r_node.expression.name == "r"

    def test_complex_expression(self) -> None:
        """Test parsing proof tree with complex expressions."""
        text = """PROOF:
p and q => q [=> intro from 1]
  [1] p and q [assumption]
      q [and elim]"""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        proof_tree = ast.items[0]
        conclusion = proof_tree.conclusion

        # Check conclusion expression is binary op
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

        # Should use \infer macro, not itemize
        assert r"\infer" in latex
        assert r"\begin{itemize}" not in latex
        assert r"\noindent" in latex  # Left-aligned, not centered
        # Expressions are in math mode within the \infer macro
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

        # Should include justification in \infer label
        assert r"\infer[" in latex
        assert "elim" in latex

    def test_sibling_premises(self) -> None:
        """Test generating siblings with & separator."""
        gen = LaTeXGenerator()
        ast = ProofTree(
            conclusion=ProofNode(
                expression=BinaryOp(
                    operator="and",
                    left=Identifier(name="p", line=2, column=1),
                    right=Identifier(name="q", line=2, column=7),
                    line=2,
                    column=3,
                ),
                justification="and intro",
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

        # Should use & to separate sibling premises
        assert " & " in latex
        assert r"\infer" in latex


class TestIntegration:
    """End-to-end integration tests for Phase 5."""

    def test_simple_implication(self) -> None:
        """Test complete pipeline for simple implication proof."""
        text = """PROOF:
p and q => q [=> intro from 1]
  [1] p and q [assumption]
      q [and elim]"""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        doc = gen.generate_document(ast)

        # Should use \infer macros
        assert r"\infer" in doc
        assert r"\begin{itemize}" not in doc
        assert r"p \land q \Rightarrow q" in doc
        assert r"\noindent" in doc  # Left-aligned, not centered

    def test_sibling_premises_integration(self) -> None:
        """Test complete pipeline with sibling premises."""
        text = """PROOF:
p and (p => q) => (p and q) [=> intro from 1]
  [1] p and (p => q) [assumption]
      :: p [and elim]
      :: p => q [and elim]
      q [=> elim]
      p and q [and intro]"""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        doc = gen.generate_document(ast)

        # Should use & for sibling premises
        assert " & " in doc
        assert r"\infer" in doc

    def test_case_analysis_integration(self) -> None:
        """Test complete pipeline with case analysis."""
        text = """PROOF:
p or q => r [or elim]
  case p:
    r [from p]
  case q:
    r [from q]"""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        doc = gen.generate_document(ast)

        # Should generate inference tree with r in display math
        assert r"\infer" in doc
        assert "r" in doc  # r appears directly in display math mode
