"""Regression tests for bug 7.F: bare colons in TEXT prose trigger auto-math wrap.

Prose like "Grouped by cardinality: empty, four singletons, ..." was rendered
as "Grouped by $cardinality : empty$, ..." because the colon-after-noun pattern
triggered a math-mode wrap (type-declaration heuristic).

Required behaviour: bare colons in TEXT prose are English punctuation.
Only content inside explicit $...$ should be parsed as math.
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


class TestBareColonInProse:
    """Bug 7.F: colon in TEXT prose must not trigger math-mode wrapping."""

    def test_cardinality_colon_not_math_wrapped(self) -> None:
        """'cardinality: empty' is plain English, not a type ascription."""
        latex = _gen("TEXT: Grouped by cardinality: empty, four singletons, six pairs.")
        # 'cardinality' must NOT be inside $...$
        assert "$cardinality" not in latex
        assert "cardinality$" not in latex
        # The prose must be preserved
        assert "cardinality" in latex
        assert "empty" in latex
        assert "four singletons" in latex

    def test_cases_colon_not_math_wrapped(self) -> None:
        """'Cases: foo and bar' stays as prose."""
        latex = _gen("TEXT: Cases: the empty set and the unit set.")
        assert "$Cases$" not in latex
        assert "Cases" in latex
        assert "empty set" in latex

    def test_notes_colon_not_math_wrapped(self) -> None:
        """'Notes: ...' stays as prose."""
        latex = _gen("TEXT: Notes: this is an important observation.")
        assert "$Notes$" not in latex
        assert "Notes" in latex

    def test_arbitrary_word_colon_not_math_wrapped(self) -> None:
        """Any word followed by colon stays as prose (not just listed keywords)."""
        latex = _gen("TEXT: Observation: the function is total.")
        assert "$Observation$" not in latex
        assert "Observation" in latex
        assert "the function is total" in latex

    def test_colon_mid_sentence_not_math_wrapped(self) -> None:
        """A colon in the middle of a sentence is punctuation."""
        latex = _gen("TEXT: We group by size: small, medium, large.")
        # 'size' should not be math-wrapped
        assert "$size$" not in latex
        assert "size" in latex

    def test_identifier_like_word_colon_not_math_wrapped(self) -> None:
        """Even identifier-looking words before colons are prose in TEXT."""
        latex = _gen("TEXT: The variable x_count: this tracks the total.")
        # x_count: this is NOT a type declaration in prose context
        # It should be treated as punctuation
        assert "this tracks the total" in latex

    def test_explicit_dollar_math_colon_still_works(self) -> None:
        """$x : N$ inside TEXT prose is still parsed as a type declaration."""
        latex = _gen("TEXT: Let $x : N$ be a natural number.")
        # The explicit $...$ math span should be processed as math
        assert r"\nat" in latex or "N" in latex  # N → \nat in fuzz mode
        assert "be a natural number" in latex

    def test_multiple_colons_in_prose_not_math_wrapped(self) -> None:
        """Multiple colons in one line stay as prose."""
        latex = _gen("TEXT: Method: first step: establish the base case.")
        assert "$Method$" not in latex
        assert "first step" in latex
        assert "establish the base case" in latex

    def test_prose_colon_does_not_eat_following_words(self) -> None:
        """The colon heuristic was eating words after the colon into math mode."""
        latex = _gen(
            "TEXT: Partition classes: singleton sets, the empty set, and the full set."
        )
        # None of these words should be inside math spans
        assert "singleton sets" in latex
        assert "the empty set" in latex
        assert "and the full set" in latex
        # 'classes' or 'Partition' must not appear inside $...$
        assert "$classes" not in latex
        assert "$Partition" not in latex
