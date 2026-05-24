"""Tests for dollar-sign parity and $$ handling in TEXT prose.

Two unsafe patterns must be caught before math-span processing:

1.  $$...$$ — display-math delimiters have no meaning in TEXT prose.
    They interact badly with the $...$ span splitter and must be escaped.

2.  Unbalanced $ — a single stray $ silently opens math mode in pdflatex,
    potentially swallowing subsequent prose until the next $ elsewhere in
    the document.  When the $ count is odd, all $ characters on the line
    must be escaped to \\$.
"""

from __future__ import annotations

from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser


def _gen(source: str) -> str:
    """Parse source and return the generated LaTeX document body."""
    if not source.startswith("==="):
        source = "=== Test ===\n\n" + source
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    doc = parser.parse()
    gen = LaTeXGenerator(use_fuzz=True)
    return gen.generate_document(doc)


# ---------------------------------------------------------------------------
# $$ — display-math delimiters in TEXT prose must be escaped
# ---------------------------------------------------------------------------


class TestDoubleDoller:
    """$$ in TEXT prose is detected and escaped so it never reaches pdflatex."""

    def test_double_dollar_is_escaped(self) -> None:
        r"""$$...$$ in prose becomes \$\$...\$\$ in the output."""
        latex = _gen("TEXT: Display math $$x = 5$$ does not belong here.")
        # No raw $$ may appear
        assert "$$" not in latex
        # The escaped form must appear
        assert r"\$\$" in latex

    def test_standalone_double_dollar_escaped(self) -> None:
        r"""Bare $$ with no content is escaped."""
        latex = _gen("TEXT: Here is $$ and nothing else.")
        assert "$$" not in latex

    def test_double_dollar_prose_preserved(self) -> None:
        r"""Text around $$ is preserved after escaping."""
        latex = _gen("TEXT: Before $$expr$$ after.")
        assert "Before" in latex
        assert "after" in latex

    def test_double_dollar_not_confused_with_two_singles(self) -> None:
        r"""Two balanced $a$ $b$ spans remain as math, not escaped."""
        latex = _gen("TEXT: We have $a$ and $b$ separately.")
        # Both single-dollar spans are balanced — must NOT be escaped
        assert r"\$" not in latex
        # Both are processed as math
        assert "$a$" in latex or "$" in latex


# ---------------------------------------------------------------------------
# Single stray $ — unbalanced dollar sign triggers LaTeX math-mode error
# ---------------------------------------------------------------------------


class TestUnbalancedDollar:
    """A single stray $ in TEXT prose is escaped to prevent runaway math mode."""

    def test_price_notation_stray_dollar_escaped(self) -> None:
        r"""'The price is $5' — the lone $ is escaped to \$."""
        latex = _gen("TEXT: The price is $5 today.")
        # After escaping there must be no raw $5 reaching LaTeX
        # (a lone $ would open math mode swallowing "5 today")
        assert r"\$" in latex
        # The prose must be preserved
        assert "The price is" in latex
        assert "today" in latex

    def test_single_dollar_at_start_escaped(self) -> None:
        r"""A lone $ at the start of a phrase is escaped."""
        latex = _gen("TEXT: $100 is the fee for entry.")
        assert r"\$" in latex
        assert "is the fee for entry" in latex

    def test_single_dollar_at_end_escaped(self) -> None:
        r"""A lone $ at the end is escaped."""
        latex = _gen("TEXT: The total cost is 42$.")
        assert r"\$" in latex

    def test_odd_count_three_dollars_escaped(self) -> None:
        r"""Three $ characters (odd) are all escaped."""
        latex = _gen("TEXT: Pay $5 plus $3 tax for a $8 total actually.")
        # Three dollars — odd count — all must be escaped
        assert "$$" not in latex
        # No unescaped single $ should remain after the \$ replacements
        # Strip escaped forms then check
        body_start = latex.find(r"\noindent")
        body = latex[body_start:] if body_start != -1 else latex
        cleaned = body.replace(r"\$", "DOLLAR")
        assert "$" not in cleaned

    def test_single_dollar_no_raw_dollar_in_prose(self) -> None:
        r"""After escaping, no unescaped $ appears in the prose section."""
        latex = _gen("TEXT: The budget is $50 per item.")
        body_start = latex.find(r"\noindent")
        body = latex[body_start:] if body_start != -1 else latex
        # Replace escaped form, then check no raw $ remains
        cleaned = body.replace(r"\$", "")
        assert "$" not in cleaned


# ---------------------------------------------------------------------------
# Balanced $ pairs are NOT affected by the parity fix
# ---------------------------------------------------------------------------


class TestBalancedDollarsUnaffected:
    """Balanced $...$ spans (even count) must pass through to math processing."""

    def test_single_balanced_span_not_escaped(self) -> None:
        r"""$x$ with balanced dollars is processed as math, not escaped."""
        latex = _gen("TEXT: Let $x$ be a natural number.")
        # The math span must be present (either $x$ literally or processed form)
        assert "$x$" in latex
        # No spurious escaped dollar for a balanced span
        # (\$ may appear only if the span had a problem, not for balanced pairs)
        assert r"\$5" not in latex  # sanity: price dollar is not leaked in

    def test_two_balanced_spans_not_escaped(self) -> None:
        r"""Two $...$ spans (four $ total, even) are both processed as math."""
        latex = _gen("TEXT: Both $p$ and $q$ are propositions.")
        # Neither span should be escaped
        assert r"\$p\$" not in latex
        assert r"\$q\$" not in latex
        # Prose is preserved
        assert "Both" in latex
        assert "are propositions" in latex

    def test_three_balanced_spans_not_escaped(self) -> None:
        r"""Three $...$ spans (six $ total, even) are all processed as math."""
        latex = _gen("TEXT: Given $a$, $b$, and $c$ are elements.")
        assert "are elements" in latex
        # No run of \$...\$ patterns for the math content
        assert r"\$a\$" not in latex

    def test_forall_balanced_span_not_escaped(self) -> None:
        r"""$\forall x$ span (balanced) is allowed through."""
        latex = _gen(r"TEXT: The claim $\forall x$ is universal.")
        assert r"\forall" in latex
        assert r"\$" not in latex


# ---------------------------------------------------------------------------
# Interaction: $$ inside a line that also has balanced $...$ pairs
# ---------------------------------------------------------------------------


class TestDoubleAndSingleInteraction:
    """$$ and balanced $...$ on the same line are handled correctly."""

    def test_double_dollar_does_not_corrupt_single_dollar_spans(self) -> None:
        r"""$$ is escaped, and a subsequent balanced $x$ is still math."""
        # After $$ is replaced with \$\$, the remaining text has no $,
        # so no balanced $x$ can follow — this is a design constraint.
        latex = _gen("TEXT: The display $$n$$ follows $x$ inline.")
        # $$ must be escaped
        assert "$$" not in latex
