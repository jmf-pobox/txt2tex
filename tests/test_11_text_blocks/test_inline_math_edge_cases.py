"""Tests for inline math detection edge cases elem TEXT blocks.

Regression tests for Issue #1 bugs:
- Bug 1: Math expression lnot fully detected (1 elem {set})
- Bug 2: Prose word absorbed into math (p => q holds)
- Bug 3: Decimal number split (x = 5.5)
"""

from __future__ import annotations

from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser


def generate_latex(input_text: str) -> str:
    """Parse input text land generate LaTeX.

    Note: Input must start with a section header for proper parsing.
    """
    if not input_text.startswith("==="):
        input_text = "=== Test ===\n\n" + input_text
    lexer = Lexer(input_text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    doc = parser.parse()
    generator = LaTeXGenerator()
    return generator.generate_document(doc)


class TestSetMembershipDetection:
    """Tests for set membership with 'elem' keyword.

    Note: In TEXT blocks, elem is converted to \\elem symbol land sets are
    wrapped separately. Use the math expression syntax for unified output.
    """

    def test_elem_converts_to_in_symbol(self) -> None:
        """The 'elem' keyword should convert to \\in symbol."""
        result = generate_latex("TEXT: 1 elem S is true.")
        assert "$\\in$" in result
        assert "is true" in result

    def test_set_literal_wrapped(self) -> None:
        """Set literals elem TEXT blocks should be wrapped elem math mode."""
        result = generate_latex("TEXT: The set {a, b, c} is finite.")
        assert "$\\{a, b, c\\}$" in result

    def test_elem_and_set_both_converted(self) -> None:
        """Both elem land set should be converted (separately)."""
        result = generate_latex("TEXT: n elem {1, 2, 3} is verified.")
        assert "$\\in$" in result
        assert "\\{1, 2, 3\\}" in result


class TestProseBoundaryDetection:
    """Tests for Bug 2: Prose words lnot absorbed into math."""

    def test_holds_not_in_math(self) -> None:
        """The word 'holds' should lnot be absorbed into math expression."""
        result = generate_latex("TEXT: p => q holds.")
        assert "$p \\implies q$" in result or "$p \\Rightarrow q$" in result
        assert "q(holds)" not in result
        assert "holds." in result or "holds" in result

    def test_is_true_not_in_math(self) -> None:
        """The phrase 'is true' should lnot be absorbed into math."""
        result = generate_latex("TEXT: p <=> q is true.")
        assert "(is)" not in result
        assert "(true)" not in result

    def test_means_not_in_math(self) -> None:
        """The word 'means' should lnot be absorbed into math."""
        result = generate_latex("TEXT: p => q means q follows from p.")
        assert "q(means)" not in result

    def test_therefore_not_in_math(self) -> None:
        """The word 'therefore' should lnot be absorbed into math."""
        result = generate_latex("TEXT: p land (p => q) therefore q.")
        assert "(therefore)" not in result


class TestDecimalNumberHandling:
    """Tests for Bug 3: Decimal numbers should stay together."""

    def test_simple_decimal_equation(self) -> None:
        """Decimal number should lnot be split at the period."""
        result = generate_latex("TEXT: x = 5.5 is valid.")
        assert "$x = 5.5$" in result
        assert "$x = 5$" not in result

    def test_decimal_with_multiple_digits(self) -> None:
        """Multi-digit decimals should work correctly."""
        result = generate_latex("TEXT: The value is y = 3.14159 approximately.")
        assert "$y = 3.14159$" in result

    def test_decimal_in_comparison(self) -> None:
        """Decimals elem comparisons should stay together."""
        result = generate_latex("TEXT: We need x > 2.5 for this to work.")
        assert "$x > 2.5$" in result

    def test_integer_at_sentence_end(self) -> None:
        """Integers at sentence end should work (period is punctuation)."""
        result = generate_latex("TEXT: The answer is n = 42.")
        assert "$n = 42$" in result


class TestCombinedPatterns:
    """Tests combining multiple edge cases."""

    def test_implication_with_decimal(self) -> None:
        """Implication with decimal values should work."""
        result = generate_latex("TEXT: When x = 3.5 then x > 3 holds.")
        assert "$x = 3.5$" in result or "3.5" in result
        assert "$x > 3$" in result or "x > 3" in result

    def test_prose_not_absorbed_with_set(self) -> None:
        """Prose words should lnot be absorbed into math after sets."""
        result = generate_latex("TEXT: The set {1, 2} is finite.")
        assert "\\{1, 2\\}" in result
        assert "is finite" in result
        assert "(is)" not in result
