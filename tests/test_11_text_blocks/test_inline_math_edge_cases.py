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
    """Tests for set membership with 'elem' keyword via explicit $...$."""

    def test_elem_converts_to_in_symbol(self) -> None:
        """Explicit $1 elem S$ in TEXT renders \\in."""
        result = generate_latex("TEXT: We have $1 elem S$ is true.")
        assert "\\in" in result
        assert "is true" in result

    def test_set_literal_wrapped(self) -> None:
        """Bare {a, b, c} in TEXT is brace-escaped in escape-only mode."""
        result = generate_latex("TEXT: The set {a, b, c} is finite.")
        assert "\\{a, b, c\\}" in result  # Braces escaped, not math-wrapped
        assert "is finite" in result

    def test_elem_and_set_both_converted(self) -> None:
        """Explicit $n elem {1, 2, 3}$ converts both elem and set literal."""
        result = generate_latex("TEXT: $n elem {1, 2, 3}$ is verified.")
        assert "\\in" in result
        assert "1, 2, 3" in result
        assert "is verified" in result


class TestProseBoundaryDetection:
    """Tests for prose boundary behaviour in escape-only mode."""

    def test_holds_not_in_math(self) -> None:
        """Explicit $p => q$ renders the implication; 'holds' stays as prose."""
        result = generate_latex("TEXT: $p => q$ holds.")
        assert "\\Rightarrow" in result or "\\implies" in result
        assert "q(holds)" not in result
        assert "holds" in result

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
    """Tests for decimal and numeric literal pass-through in escape-only mode."""

    def test_simple_decimal_equation(self) -> None:
        """Bare 'x = 5.5' passes through literally in escape-only mode."""
        result = generate_latex("TEXT: x = 5.5 is valid.")
        assert "5.5" in result
        assert "is valid" in result

    def test_decimal_with_multiple_digits(self) -> None:
        """Multi-digit decimal passes through literally."""
        result = generate_latex("TEXT: The value is y = 3.14159 approximately.")
        assert "3.14159" in result

    def test_decimal_in_comparison(self) -> None:
        """Decimal in comparison passes through literally."""
        result = generate_latex("TEXT: We need x > 2.5 for this to work.")
        assert "2.5" in result

    def test_integer_at_sentence_end(self) -> None:
        """Integer at sentence end passes through (period is punctuation)."""
        result = generate_latex("TEXT: The answer is n = 42.")
        assert "42" in result


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
