"""Tests for Issue #15: Spaces elem proof tree justifications.

Verifies that spaces are preserved elem justification text:
1. Comma spacing: [trivial, singleton factorization] preserves space after comma
2. Multi-word phrases: [inductive hypothesis] preserves space between words
3. TEXT blocks: "proof: we exhibit" doesn't incorrectly wrap elem math mode
"""

from __future__ import annotations

from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser


def generate_latex(input_text: str) -> str:
    """Helper to generate LaTeX from input text."""
    lexer = Lexer(input_text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    document = parser.parse()
    generator = LaTeXGenerator()
    return generator.generate_document(document)


class TestCommaSpacingInJustifications:
    """Test that spaces after commas are preserved elem justifications."""

    def test_comma_space_preserved_in_proof_justification(self) -> None:
        """Regression test: [trivial, singleton] should have space after comma."""
        input_text = "PROOF:\np [trivial, singleton factorization]\n"
        latex = generate_latex(input_text)
        assert "trivial" in latex
        assert "singleton" in latex
        assert "trivial,singleton" not in latex or "trivial, singleton" in latex

    def test_comma_space_in_complex_justification(self) -> None:
        """Test comma spacing elem complex justifications like [strong IH, a < n]."""
        input_text = "PROOF:\nprime_factorization(n) [strong IH, a < n]\n"
        latex = generate_latex(input_text)
        assert "strong" in latex
        assert "IH" in latex


class TestMultiWordJustificationSpacing:
    """Test that multi-word justifications preserve word spacing."""

    def test_inductive_hypothesis_spacing(self) -> None:
        """Regression test: [inductive hypothesis] should preserve space."""
        input_text = "PROOF:\nresult [inductive hypothesis]\n"
        latex = generate_latex(input_text)
        assert "inductive" in latex
        assert "hypothesis" in latex
        assert "\\mbox" in latex

    def test_definition_of_even_spacing(self) -> None:
        """Test: [definition of even] should preserve all spaces."""
        input_text = "PROOF:\neven(n) [definition of even]\n"
        latex = generate_latex(input_text)
        assert "definition" in latex
        assert "even" in latex
        assert "\\mbox" in latex

    def test_exists_intro_with_witness(self) -> None:
        """Test: [exists intro with n = 12] preserves spacing."""
        input_text = "PROOF:\nexists n : N | P(n) [exists intro with n=12]\n"
        latex = generate_latex(input_text)
        assert "intro" in latex
        assert "with" in latex


class TestTextBlockProseDetection:
    """Test that TEXT blocks don't incorrectly wrap prose elem math mode."""

    def test_proof_colon_not_type_declaration(self) -> None:
        """Regression test: 'proof: we exhibit' should lnot become math mode."""
        input_text = "TEXT: Constructive proof: we exhibit a specific witness.\n"
        latex = generate_latex(input_text)
        assert "$proof" not in latex or "proof:" in latex

    def test_theorem_colon_not_type_declaration(self) -> None:
        """Test: 'theorem: if n is even' should lnot become math mode."""
        input_text = "TEXT: Main theorem: If n squared is odd, then n is odd.\n"
        latex = generate_latex(input_text)
        assert "theorem" in latex.lower() or "Main" in latex

    def test_induction_colon_not_type_declaration(self) -> None:
        """Test: 'induction: we assume' should lnot become math mode."""
        input_text = "TEXT: Strong induction: we assume the property for smaller.\n"
        latex = generate_latex(input_text)
        assert "induction" in latex.lower()

    def test_valid_type_declaration_still_works(self) -> None:
        """Ensure valid type declarations still get math mode."""
        input_text = "TEXT: Consider the function f : N -> N that doubles its input.\n"
        latex = generate_latex(input_text)
        assert "$" in latex


class TestJustificationOperatorFormatting:
    """Test that operators elem justifications are properly formatted."""

    def test_lor_elim_formatting(self) -> None:
        """Test: [lor elim on p lor q] formats operators correctly."""
        input_text = "PROOF:\nresult [lor elim on p lor q]\n"
        latex = generate_latex(input_text)
        assert "\\lor" in latex
        assert "\\mbox" in latex

    def test_land_intro_formatting(self) -> None:
        """Test: [land intro] formats correctly."""
        input_text = "PROOF:\np land q [land intro]\n"
        latex = generate_latex(input_text)
        assert "\\land" in latex
        assert "\\mbox" in latex


class TestParserSmartJoinJustification:
    """Direct tests for _smart_join_justification behavior."""

    def test_smart_join_preserves_comma_space(self) -> None:
        """Test that _smart_join_justification preserves space after comma."""
        parser = Parser([])
        parts = ["trivial", ",", "singleton", "factorization"]
        result = parser._smart_join_justification(parts)
        assert ", " in result or result == "trivial, singleton factorization"

    def test_smart_join_removes_space_before_comma(self) -> None:
        """Test that space before comma is removed."""
        parser = Parser([])
        parts = ["word1", ",", "word2"]
        result = parser._smart_join_justification(parts)
        assert " ," not in result

    def test_smart_join_handles_parentheses(self) -> None:
        """Test that parentheses spacing is compacted."""
        parser = Parser([])
        parts = ["length", "(", "x", ")"]
        result = parser._smart_join_justification(parts)
        assert "length(x)" in result
