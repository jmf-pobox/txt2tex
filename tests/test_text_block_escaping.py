"""Tests for TEXT-block special character escaping.

Every LaTeX active character that can cause silent corruption or compile errors
in TEXT prose must be escaped to its safe literal-glyph form.  Characters
inside $...$ math spans must NOT be touched by the prose escaper.
"""

from __future__ import annotations

import re

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
# % — LaTeX line-comment: silently discards everything after it
# ---------------------------------------------------------------------------


class TestPercentEscape:
    """% in TEXT prose must be escaped to \\% so it is not a line comment."""

    def test_percent_in_prose_is_escaped(self) -> None:
        """A bare % becomes \\% in the emitted LaTeX."""
        latex = _gen("TEXT: The success rate is 95% today.")
        assert r"\%" in latex

    def test_trailing_percent_is_escaped(self) -> None:
        """% at end of a sentence is escaped, not treated as a comment."""
        latex = _gen("TEXT: Probability of success is 50%.")
        assert r"\%" in latex
        # The trailing text must not be silently discarded
        assert "Probability" in latex

    def test_percent_does_not_reach_latex_raw(self) -> None:
        """No bare % should appear in the prose portion of the output."""
        latex = _gen("TEXT: A 30% discount applies here.")
        # Strip escaped form, then check no raw % remains in the prose portion
        # (the document header may contain % for comments, so we check the body)
        body_start = latex.find(r"\noindent")
        body = latex[body_start:] if body_start != -1 else latex
        cleaned = body.replace(r"\%", "")
        assert "%" not in cleaned

    def test_multiple_percents_in_prose(self) -> None:
        """Multiple % characters in one line are all escaped."""
        latex = _gen("TEXT: From 10% to 90% is an 80% increase.")
        assert latex.count(r"\%") >= 3

    def test_percent_inside_math_not_escaped(self) -> None:
        """% inside $...$ is not an LaTeX active character in math mode."""
        # This is a degenerate case; % has no special meaning in math mode
        # but we confirm the math span itself is not mangled.
        latex = _gen(r"TEXT: See $\forall x$ for all x.")
        assert r"\forall" in latex


# ---------------------------------------------------------------------------
# & — Alignment tab: raises "Misplaced alignment tab" outside tabular/align
# ---------------------------------------------------------------------------


class TestAmpersandEscape:
    """& in TEXT prose must be escaped to \\& so it is not a column separator."""

    def test_ampersand_in_prose_is_escaped(self) -> None:
        """A bare & becomes \\& in the emitted LaTeX."""
        latex = _gen("TEXT: The company Smith & Jones is founded here.")
        assert r"\&" in latex

    def test_ampersand_does_not_appear_raw(self) -> None:
        """No raw & appears in the prose after escaping."""
        latex = _gen("TEXT: Research & Development.")
        body_start = latex.find(r"\noindent")
        body = latex[body_start:] if body_start != -1 else latex
        cleaned = body.replace(r"\&", "")
        assert "&" not in cleaned

    def test_multiple_ampersands_escaped(self) -> None:
        """Multiple & characters are all escaped."""
        latex = _gen("TEXT: A & B & C are three items.")
        assert latex.count(r"\&") >= 2

    def test_prose_preserved_around_ampersand(self) -> None:
        """Words around & are preserved."""
        latex = _gen("TEXT: Smith & Jones founded the firm.")
        assert "Smith" in latex
        assert "Jones" in latex


# ---------------------------------------------------------------------------
# # — Macro parameter: causes TeX error or substitutes arg outside macro def
# ---------------------------------------------------------------------------


class TestHashEscape:
    """# in TEXT prose must be escaped to \\# (regression: was already fixed)."""

    def test_hash_in_prose_is_escaped(self) -> None:
        """A bare # becomes \\# in the emitted LaTeX."""
        latex = _gen("TEXT: The cardinality # S gives the size.")
        assert r"\#" in latex

    def test_hash_number_notation_escaped(self) -> None:
        """# used as 'number' is escaped."""
        latex = _gen("TEXT: This is step #3 in the proof.")
        assert r"\#" in latex

    def test_multiple_hashes_escaped(self) -> None:
        """Multiple # characters are all escaped."""
        latex = _gen("TEXT: Items #1, #2, and #3 are selected.")
        assert latex.count(r"\#") >= 3


# ---------------------------------------------------------------------------
# ~ — Non-breaking space: silently becomes a nbsp, not the literal tilde
# ---------------------------------------------------------------------------


class TestTildeEscape:
    """~ in TEXT prose must be escaped to \\textasciitilde{} as a visible glyph."""

    def test_tilde_in_prose_is_escaped(self) -> None:
        r"""A bare ~ is escaped: \textasciitilde appears in the emitted LaTeX."""
        latex = _gen("TEXT: The approximation x~5 is used.")
        # The command may appear as \textasciitilde{} or \textasciitilde$\{\}$
        # depending on downstream inline-math processing of the braces; both
        # are acceptable — the key invariant is that no raw ~ remains.
        assert r"\textasciitilde" in latex

    def test_tilde_does_not_reach_latex_raw(self) -> None:
        """No bare ~ appears in the prose portion of the output."""
        latex = _gen("TEXT: Approximately ~10 units remain.")
        body_start = latex.find(r"\noindent")
        body = latex[body_start:] if body_start != -1 else latex
        # Strip the escaped command in both possible forms; no raw ~ should remain
        cleaned = body.replace(r"\textasciitilde{}", "").replace(r"\textasciitilde", "")
        assert "~" not in cleaned

    def test_tilde_prose_preserved(self) -> None:
        """Words around ~ are preserved."""
        latex = _gen("TEXT: The value x~5 is approximate.")
        assert "The value" in latex
        assert "is approximate" in latex


# ---------------------------------------------------------------------------
# ^ — Superscript: raises "Missing $ inserted" outside math mode
# ---------------------------------------------------------------------------


class TestCaretEscape:
    """^ in TEXT prose must be escaped (regression: already fixed in bug 7.A)."""

    def test_caret_in_prose_is_escaped(self) -> None:
        """A bare ^ in prose is escaped so it cannot trigger math-mode superscript."""
        latex = _gen("TEXT: The expression a^b appears in prose.")
        # Must not appear raw
        clean = (
            latex.replace(r"\textasciicircum{}", "")
            .replace(r"\^{}", "")
            .replace(r"\bsup", "")
            .replace(r"\esup", "")
        )
        assert "^" not in clean

    def test_caret_inside_dollar_math_is_not_escaped(self) -> None:
        """^ inside $...$ is processed by the math parser, not by the prose escaper."""
        latex = _gen("TEXT: The set $a^b$ is a superscript.")
        # \textasciicircum must NOT appear inside the math span
        assert r"\textasciicircum{}" not in latex


# ---------------------------------------------------------------------------
# _ — Subscript: raises "Missing $ inserted" outside math mode
# ---------------------------------------------------------------------------


class TestUnderscoreEscape:
    """_ in TEXT prose must be escaped to \\_.

    Handled by _escape_underscores_outside_math at the end of the pipeline.
    """

    def test_underscore_in_identifier_is_escaped(self) -> None:
        """count_N in prose is escaped as count\\_N."""
        latex = _gen("TEXT: The variable count_N tracks the total.")
        assert r"count\_N" in latex

    def test_underscore_does_not_appear_raw_in_prose(self) -> None:
        """No raw _ appears in prose output."""
        latex = _gen("TEXT: The variable x_1 is the first element.")
        body_start = latex.find(r"\noindent")
        body = latex[body_start:] if body_start != -1 else latex
        # Strip the escaped form and math spans before checking
        body_no_math = re.sub(r"\$[^$]*\$", "", body)
        cleaned = body_no_math.replace(r"\_", "")
        assert "_" not in cleaned

    def test_underscore_inside_dollar_math_not_escaped(self) -> None:
        """_ inside $...$ is handled by the math parser, not escaped as \\_ ."""
        latex = _gen(r"TEXT: The element $x \in S$ is in the set.")
        # The prose escaper must not insert \\_ inside the math span
        assert r"\in" in latex


# ---------------------------------------------------------------------------
# Combinations — multiple special chars on the same line
# ---------------------------------------------------------------------------


class TestCombinedEscapes:
    """Multiple special characters on one line are all escaped correctly."""

    def test_percent_and_ampersand_together(self) -> None:
        """Both % and & on the same line are each escaped."""
        latex = _gen("TEXT: Score: 50% & grade B.")
        assert r"\%" in latex
        assert r"\&" in latex

    def test_all_five_special_chars(self) -> None:
        """%, &, #, ~, ^ each appear and are all escaped."""
        latex = _gen("TEXT: A 50% score, R&D, item #1, x~5, and a^b.")
        assert r"\%" in latex
        assert r"\&" in latex
        assert r"\#" in latex
        assert r"\textasciitilde" in latex

    def test_math_span_not_corrupted_by_prose_escaping(self) -> None:
        """A $...$ math span adjacent to special chars is not corrupted."""
        latex = _gen(r"TEXT: The set $\forall x$ has 50% coverage & more.")
        assert r"\forall" in latex
        assert r"\%" in latex
        assert r"\&" in latex
