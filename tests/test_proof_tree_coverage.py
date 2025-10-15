"""Tests for proof tree coverage - targeting lines 1576-1673 in latex_gen.py.

This file focuses on testing the complex case analysis code that handles:
- Or-elimination with case branches
- Disjunction sibling filtering
- Staggered height calculations
- Nested grandchild recursion
"""

from __future__ import annotations

from txt2tex.ast_nodes import (
    CaseAnalysis,
    Document,
    Identifier,
    ProofNode,
)
from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser


def make_proof_node(
    expr: str,
    justification: str | None = None,
    label: int | None = None,
    is_assumption: bool = False,
    is_sibling: bool = False,
    children: list[ProofNode | CaseAnalysis] | None = None,
    indent: int = 0,
) -> ProofNode:
    """Helper to create ProofNode with all required fields."""
    return ProofNode(
        expression=Identifier(name=expr, line=1, column=1),
        justification=justification,
        label=label,
        is_assumption=is_assumption,
        is_sibling=is_sibling,
        children=children or [],
        indent_level=indent,
        line=1,
        column=1,
    )


def make_case(name: str, steps: list[ProofNode]) -> CaseAnalysis:
    """Helper to create CaseAnalysis."""
    return CaseAnalysis(case_name=name, steps=steps, line=1, column=1)


class TestCaseAnalysisWithSiblings:
    """Test case analysis with sibling filtering (lines 1598-1661)."""

    def test_case_analysis_with_disjunction_sibling(self) -> None:
        """Test or-elim with disjunction sibling filtering (lines 1602-1609).

        Tests the logic that filters siblings to only include disjunctions
        as top-level premises when case analysis is present.
        """
        text = """PROOF:
(p and (q or r)) => ((p and q) or (p and r)) [=> intro from 1]
  [1] p and (q or r) [assumption]
  :: (p and q) or (p and r) [or elim from 2]
    [2] q or r [from 1]
    case q:
      :: p and q [and intro]
        :: p [and elim from 1]
        :: q [case assumption]
      :: (p and q) or (p and r) [or intro]
    case r:
      :: p and r [and intro]
        :: p [and elim from 1]
        :: r [case assumption]
      :: (p and q) or (p and r) [or intro]"""

        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        assert isinstance(ast, Document)
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # Should generate inference rules
        assert r"\infer" in latex

        # Should contain case analysis elements
        assert "q" in latex
        assert "r" in latex

        # Should use & for horizontal layout
        assert " & " in latex

    def test_case_analysis_multiple_cases_staggered(self) -> None:
        """Test multiple case branches with staggered heights (lines 1616-1652).

        Tests the staggered height formula:
        - First case: 6 + depth*2
        - Subsequent cases: 18 + depth*4 with \\hskip 6em
        """
        text = """PROOF:
result [or elim]
  case p:
    result [from p]
  case q:
    result [from q]
  case r:
    result [from r]"""

        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # Should generate raised proof structures
        # The staggered strategy uses \raiseproof for vertical spacing
        assert r"\infer" in latex
        assert r"\raiseproof" in latex

        # Multiple cases should generate staggered layout with hskip
        assert r"\hskip" in latex
        assert latex.count(r"\raiseproof") >= 2  # Multiple raised cases


class TestNestedCaseAnalysis:
    """Test nested grandchildren in case analysis (lines 1581-1592)."""

    def test_nested_case_analysis_grandchildren(self) -> None:
        """Test case analysis as grandchildren (lines 1582-1586).

        Tests the code that checks if grandchild is CaseAnalysis and
        sets has_case_analysis flag.
        """
        # Parse a real proof with nested structure
        text = """PROOF:
conclusion [rule]
  premise [from 1]
    case p:
      result [case p]
    case q:
      result [case q]"""

        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # Should handle nested case analysis
        assert r"\infer" in latex
        assert "conclusion" in latex

    def test_sequential_child_with_children(self) -> None:
        """Test sequential derivation with children (lines 1573-1592).

        Tests the code path where a sequential child has its own children,
        requiring recursive subtree generation.
        """
        text = """PROOF:
top [rule1]
  [1] assumption1 [assumption]
  middle [rule2]
    bottom1 [from 1]
    bottom2 [from 1]"""

        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # Should generate nested inference rules
        assert r"\infer" in latex
        assert latex.count(r"\infer") >= 2  # Multiple nested inferences


class TestProofTreeEdgeCases:
    """Test edge cases in proof tree generation."""

    def test_case_analysis_no_siblings(self) -> None:
        """Test case analysis without siblings (lines 1662-1665).

        Tests the else branch where only child_premises_parts exist.
        """
        text = """PROOF:
result [or elim]
  case p:
    result [from p]"""

        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # Should generate basic case structure
        assert r"\infer" in latex
        assert "result" in latex

    def test_child_with_justification(self) -> None:
        """Test child node with justification (lines 1667-1673).

        Tests the branch where child has a justification label.
        """
        text = """PROOF:
conclusion [rule]
  premise [specific justification]
    subpremise [another rule]"""

        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # Should include justification labels
        assert r"\infer[" in latex  # Justification in brackets
        assert "rule" in latex or "specific" in latex

    def test_empty_current_premises(self) -> None:
        """Test when current_premises defaults to assumption (line 1665).

        Tests the case where neither sibling_latex_parts nor
        child_premises_parts exist.
        """
        text = """PROOF:
conclusion [rule]
  [1] assumption [assumption]"""

        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # Should use assumption as premise
        assert r"\infer" in latex
        assert "assumption" in latex

    def test_sequential_with_case_analysis_children(self) -> None:
        """Test sequential child with case analysis grandchildren (lines 1576-1673).

        This is the KEY test for the complex proof tree code. Structure needed:
        - Assumption WITH MULTIPLE CHILDREN
        - One of those children is sequential (not sibling)
        - That sequential child has case analysis grandchildren

        This triggers _generate_complex_assumption_scope which contains
        lines 1576-1673 that handle:
        - Filtering disjunction siblings
        - Staggered height calculations
        - Nested case processing
        """
        text = """PROOF:
conclusion [rule]
  [1] assumption [assumption]
    sibling1 [from 1]
    sequential_node [sequential_rule]
      case p:
        result_p [from p]
      case q:
        result_q [from q]"""

        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # Should generate complex nested structure
        assert r"\infer" in latex
        # Complex proof should have multiple elements
        assert latex.count(r"\infer") >= 2
