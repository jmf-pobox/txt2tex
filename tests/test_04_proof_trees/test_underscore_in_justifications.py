"""Tests for underscore identifiers in justifications (EQUIV and PROOF).

This tests the fix for underscore handling where identifiers like length_L,
played_L should render consistently in both expressions and justifications.
"""

from __future__ import annotations

from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser


class TestUnderscoreInEquivJustifications:
    """Test underscore identifiers in EQUIV justifications."""

    def test_single_char_suffix_in_justification(self) -> None:
        """Test identifier with single-char suffix in justification."""
        text = """EQUIV:
length_L(nil) = 0
0 = 0 [length_L(nil) = 0]"""

        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # Expression should use subscript: length_L
        assert "length_L(nil)" in latex

        # Justification should escape underscore for prose rendering
        # Note: Spacing may be compressed in justification text
        assert r"\mbox{length\_L(nil)" in latex
        assert r"length\_L" in latex  # Identifier with escaped underscore

    def test_multiple_underscore_identifiers_in_justification(self) -> None:
        """Test multiple identifiers with underscores in same justification."""
        text = """EQUIV:
played_L(nil) = nil
unplayed_L(nil) = nil [played_L(nil) = nil land unplayed_L(nil) = nil]"""

        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # Both identifiers should have escaped underscores
        assert r"played\_L" in latex
        assert r"unplayed\_L" in latex

        # The 'land' operator should also be converted
        assert r"$\land$" in latex

    def test_underscore_with_operators_in_justification(self) -> None:
        """Test underscore identifiers mixed with operators in justification."""
        text = """EQUIV:
x elem S
y elem S [x_i elem S => y_i elem S]"""

        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # Underscore identifiers have escaped underscores in justification
        assert r"x\_i" in latex  # Justification uses escaped underscore

        # Operators converted
        assert r"$\in$" in latex
        assert r"$\Rightarrow$" in latex

        # Both identifiers should appear with escaped underscores
        assert r"y\_i" in latex

    def test_function_name_with_underscore_in_justification(self) -> None:
        """Test function names with underscores appear in justifications."""
        text = """EQUIV:
length_L(join(e, l)) = n + length_L(l)
n + length_L(l) = length_L(l) + n [definition of length_L]"""

        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # Function name in justification has escaped underscore
        assert r"definition of length\_L" in latex

    def test_multi_word_identifier_not_affected(self) -> None:
        """Test that multi-word identifiers (3+ char suffix) get escaped."""
        text = """EQUIV:
cumulative_total = 0
0 = 0 [cumulative_total = 0]"""

        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # Multi-word identifiers should have escaped underscores in justification
        assert r"cumulative\_total" in latex


class TestUnderscoreInProofJustifications:
    """Test underscore identifiers in PROOF justifications."""

    def test_underscore_in_proof_expression(self) -> None:
        """Test identifier with underscore in proof tree expression."""
        text = """PROOF:
  played_L(nil) = nil [definition]"""

        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # Expression should use subscript notation
        assert "played_L(nil)" in latex

        # Note: Proof tree justifications use \infer[label] syntax
        # where label is raw text, not escaped like EQUIV justifications

    def test_nested_proof_with_underscores(self) -> None:
        """Test nested proof tree with underscore identifiers."""
        text = """PROOF:
  length_L(nil) = 0
    0 = 0 [base case]
      true [arithmetic]"""

        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # Expression should use subscript notation
        assert "length_L(nil)" in latex


class TestUnderscoreConsistency:
    """Test that underscores render consistently across contexts."""

    def test_expression_and_justification_consistency(self) -> None:
        """Test length_L renders as subscript in expression and justification."""
        text = """EQUIV:
length_L(nil) = 0
0 = 0 [length_L(nil) = 0]"""

        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # Both should use subscript notation (not \mathit{length\_L})
        # Expression: length_L(nil) in math mode
        assert "length_L(nil)" in latex

        # Justification: length\_L(nil) with escaped underscore for prose
        assert r"length\_L(nil)" in latex

        # Should NOT have escaped underscore in mathit
        assert r"\mathit{length\_L}" not in latex

    def test_no_double_wrapping(self) -> None:
        """Test that identifiers already in math mode don't get double-wrapped."""
        text = """EQUIV:
x in S
y in S [definition of => operator]"""

        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # => should be converted to $\Rightarrow$, not $$\Rightarrow$$
        assert r"$\Rightarrow$" in latex
        assert r"$$\Rightarrow$$" not in latex


if __name__ == "__main__":
    import pytest

    pytest.main([__file__, "-v"])
