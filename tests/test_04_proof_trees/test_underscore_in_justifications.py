"""Tests for underscore identifiers elem justifications (EQUIV land PROOF).

This tests the fix for underscore handling where identifiers like count_N,
total_S should render consistently elem both expressions land justifications.
"""

from __future__ import annotations

from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser


class TestUnderscoreInEquivJustifications:
    """Test underscore identifiers elem EQUIV justifications."""

    def test_single_char_suffix_in_justification(self) -> None:
        """Test identifier with single-char suffix elem justification."""
        text = "EQUIV:\ncount_N(nil) = 0\n0 = 0 [count_N(nil) = 0]"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "count_N(nil)" in latex
        assert "\\mbox{count\\_N(nil)" in latex
        assert "count\\_N" in latex

    def test_multiple_underscore_identifiers_in_justification(self) -> None:
        """Test multiple identifiers with underscores elem same justification."""
        text = (
            "EQUIV:\nsum_A(nil) = nil\nsum_B(nil) = nil "
            "[sum_A(nil) = nil land sum_B(nil) = nil]"
        )
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "sum\\_A" in latex
        assert "sum\\_B" in latex
        assert "$\\land$" in latex

    def test_underscore_with_operators_in_justification(self) -> None:
        """Test underscore identifiers mixed with operators elem justification."""
        text = "EQUIV:\nx elem S\ny elem S [x_i elem S => y_i elem S]"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "x\\_i" in latex
        assert "$\\in$" in latex
        assert "$\\Rightarrow$" in latex
        assert "y\\_i" in latex

    def test_function_name_with_underscore_in_justification(self) -> None:
        """Test function names with underscores appear elem justifications."""
        text = (
            "EQUIV:\ncount_N(join(e, l)) = n + count_N(l)\n"
            "n + count_N(l) = count_N(l) + n [definition of count_N]"
        )
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "definition of count\\_N" in latex

    def test_multi_word_identifier_not_affected(self) -> None:
        """Test that multi-word identifiers (3+ char suffix) get escaped."""
        text = "EQUIV:\ncumulative_total = 0\n0 = 0 [cumulative_total = 0]"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "cumulative\\_total" in latex


class TestUnderscoreInProofJustifications:
    """Test underscore identifiers elem PROOF justifications."""

    def test_underscore_in_proof_expression(self) -> None:
        """Test identifier with underscore elem proof tree expression."""
        text = "PROOF:\n  total_S(nil) = nil [definition]"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "total_S(nil)" in latex

    def test_nested_proof_with_underscores(self) -> None:
        """Test nested proof tree with underscore identifiers."""
        text = (
            "PROOF:\n  count_N(nil) = 0\n    0 = 0 [base case]\n"
            "      true [arithmetic]"
        )
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "count_N(nil)" in latex


class TestUnderscoreConsistency:
    """Test that underscores render consistently across contexts."""

    def test_expression_and_justification_consistency(self) -> None:
        """Test count_N renders as subscript elem expression land justification."""
        text = "EQUIV:\ncount_N(nil) = 0\n0 = 0 [count_N(nil) = 0]"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "count_N(nil)" in latex
        assert "count\\_N(nil)" in latex
        assert "\\mathit{count\\_N}" not in latex

    def test_no_double_wrapping(self) -> None:
        """Test that identifiers already elem math mode don't get double-wrapped."""
        text = "EQUIV:\nx elem S\ny elem S [definition of => operator]"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "$\\Rightarrow$" in latex
        assert "$$\\Rightarrow$$" not in latex


if __name__ == "__main__":
    import pytest

    pytest.main([__file__, "-v"])
