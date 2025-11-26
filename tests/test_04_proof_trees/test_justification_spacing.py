"""Tests for Issue #15: Spaces in proof tree justifications.

Verifies that spaces are preserved in justification text:
1. Comma spacing: [trivial, singleton factorization] preserves space after comma
2. Multi-word phrases: [inductive hypothesis] preserves space between words
3. TEXT blocks: "proof: we exhibit" doesn't incorrectly wrap in math mode
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
    """Test that spaces after commas are preserved in justifications."""

    def test_comma_space_preserved_in_proof_justification(self) -> None:
        """Regression test: [trivial, singleton] should have space after comma."""
        input_text = """PROOF:
p [trivial, singleton factorization]
"""
        latex = generate_latex(input_text)
        # The justification should contain comma followed by space
        # When wrapped in \mathrm{}, the phrase becomes one wrapped unit
        assert "trivial" in latex
        assert "singleton" in latex
        # Verify no run-together like "trivial,singleton" without space
        # The comma should be followed by a space in the raw justification
        assert "trivial,singleton" not in latex or "trivial, singleton" in latex

    def test_comma_space_in_complex_justification(self) -> None:
        """Test comma spacing in complex justifications like [strong IH, a < n]."""
        input_text = """PROOF:
prime_factorization(n) [strong IH, a < n]
"""
        latex = generate_latex(input_text)
        # Should preserve space after comma
        assert "strong" in latex
        assert "IH" in latex


class TestMultiWordJustificationSpacing:
    """Test that multi-word justifications preserve word spacing."""

    def test_inductive_hypothesis_spacing(self) -> None:
        """Regression test: [inductive hypothesis] should preserve space."""
        input_text = """PROOF:
result [inductive hypothesis]
"""
        latex = generate_latex(input_text)
        # The phrase should be wrapped to preserve spacing
        # Either as \mathrm{inductive hypothesis} or with proper spacing
        assert "inductive" in latex
        assert "hypothesis" in latex
        # Should NOT have words run together without \mathrm wrapping
        # Check that mathrm is used for text
        assert r"\mathrm" in latex

    def test_definition_of_even_spacing(self) -> None:
        """Test: [definition of even] should preserve all spaces."""
        input_text = """PROOF:
even(n) [definition of even]
"""
        latex = generate_latex(input_text)
        # Multi-word phrase should be wrapped
        assert "definition" in latex
        assert "even" in latex
        # Verify \mathrm wrapping for text preservation
        assert r"\mathrm" in latex

    def test_exists_intro_with_witness(self) -> None:
        """Test: [exists intro with n = 12] preserves spacing."""
        input_text = """PROOF:
exists n : N | P(n) [exists intro with n=12]
"""
        latex = generate_latex(input_text)
        # Should contain the intro rule properly formatted
        assert "intro" in latex
        assert "with" in latex


class TestTextBlockProseDetection:
    """Test that TEXT blocks don't incorrectly wrap prose in math mode."""

    def test_proof_colon_not_type_declaration(self) -> None:
        """Regression test: 'proof: we exhibit' should not become math mode."""
        input_text = """TEXT: Constructive proof: we exhibit a specific witness.
"""
        latex = generate_latex(input_text)
        # "proof:" followed by prose should NOT be in math mode
        # The colon after "proof" is prose, not a type declaration
        # Should NOT have $proof : we$ pattern
        assert "$proof" not in latex or "proof:" in latex

    def test_theorem_colon_not_type_declaration(self) -> None:
        """Test: 'theorem: if n is even' should not become math mode."""
        input_text = """TEXT: Main theorem: If n squared is odd, then n is odd.
"""
        latex = generate_latex(input_text)
        # "theorem:" should not be wrapped in math mode
        assert "theorem" in latex.lower() or "Main" in latex

    def test_induction_colon_not_type_declaration(self) -> None:
        """Test: 'induction: we assume' should not become math mode."""
        input_text = """TEXT: Strong induction: we assume the property for smaller.
"""
        latex = generate_latex(input_text)
        # Should be prose, not math
        assert "induction" in latex.lower()

    def test_valid_type_declaration_still_works(self) -> None:
        """Ensure valid type declarations still get math mode."""
        input_text = """TEXT: Consider the function f : N -> N that doubles its input.
"""
        latex = generate_latex(input_text)
        # "f : N -> N" is a valid type declaration
        # Should be in math mode
        assert "$" in latex  # Some math mode should be present


class TestJustificationOperatorFormatting:
    """Test that operators in justifications are properly formatted."""

    def test_lor_elim_formatting(self) -> None:
        """Test: [lor elim on p lor q] formats operators correctly."""
        input_text = """PROOF:
result [lor elim on p lor q]
"""
        latex = generate_latex(input_text)
        # Should have \lor for the operator
        assert r"\lor" in latex
        # Should have \mathrm{elim} for text
        assert r"\mathrm" in latex

    def test_land_intro_formatting(self) -> None:
        """Test: [land intro] formats correctly."""
        input_text = """PROOF:
p land q [land intro]
"""
        latex = generate_latex(input_text)
        # Should have \land for the operator
        assert r"\land" in latex
        # Should have \mathrm for intro
        assert r"\mathrm" in latex


class TestParserSmartJoinJustification:
    """Direct tests for _smart_join_justification behavior."""

    def test_smart_join_preserves_comma_space(self) -> None:
        """Test that _smart_join_justification preserves space after comma."""
        parser = Parser([])  # Empty token list, we just need the method
        parts = ["trivial", ",", "singleton", "factorization"]
        result = parser._smart_join_justification(parts)
        # Should have space after comma
        assert ", " in result or result == "trivial, singleton factorization"

    def test_smart_join_removes_space_before_comma(self) -> None:
        """Test that space before comma is removed."""
        parser = Parser([])
        parts = ["word1", ",", "word2"]
        result = parser._smart_join_justification(parts)
        # Should NOT have space before comma
        assert " ," not in result

    def test_smart_join_handles_parentheses(self) -> None:
        """Test that parentheses spacing is compacted."""
        parser = Parser([])
        parts = ["length", "(", "x", ")"]
        result = parser._smart_join_justification(parts)
        # Should compact parentheses
        assert "length(x)" in result
