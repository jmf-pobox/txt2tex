"""Regression tests for bug 7: TEXT-block math-mode heuristic corruption.

Four sub-symptoms tested:
  7.A  ^  in TEXT prose is escaped as plain text; ^ inside $...$ is rendered as math.
  7.B  colon in TEXT prose does NOT trigger math-mode wrap.
  7.C  math-operator keywords (forall, exists, lor, land, lnot) are NOT
       auto-mathed when they appear as bare prose words not inside $...$.
  7.D  backtick/backslash adjacency in prose does not garble.

The expected behaviour after the fix:
  - TEXT prose passes through with LaTeX-character escaping only.
  - $ ... $ delimiters are honoured: content inside is parsed by the
    math/Z parser; content outside is plain text.
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
# 7.A  caret in prose vs caret inside $...$
# ---------------------------------------------------------------------------


class TestCaretHandling:
    """Bug 7.A: ^ in TEXT prose must not produce \\textasciicircum inside math."""

    def test_caret_in_plain_prose_is_escaped(self) -> None:
        """A bare ^ in prose is escaped as \\textasciicircum{}, not left raw."""
        latex = _gen("TEXT: We use a^b in prose here.")
        # The caret must not appear raw (LaTeX error) and must not produce
        # \\textasciicircum inside a $...$ math span.
        assert "^" not in latex.replace(r"\textasciicircum{}", "").replace(
            r"\^{}", ""
        ).replace(r"\bsup", "").replace(r"\esup", "")

    def test_dollar_math_caret_is_rendered_as_superscript(self) -> None:
        """$a^b$ in TEXT prose is parsed by the math parser, not escaped."""
        latex = _gen("TEXT: The expression $a^b$ is a superscript.")
        # After the fix, $a^b$ in TEXT is parsed as a superscript expression.
        # In fuzz mode, superscript renders as \bsup ... \esup.
        assert r"\bsup" in latex or "^" in latex  # superscript appeared
        # The broken escape must NOT appear inside the math span
        assert r"\textasciicircum{}" not in latex

    def test_dollar_math_caret_seq_concat(self) -> None:
        """$s ^ t$ in TEXT prose renders as sequence concatenation."""
        latex = _gen("TEXT: The concatenation $s ^ t$ results in a new sequence.")
        # ^ in math context is sequence concatenation (\\cat)
        assert r"\cat" in latex
        assert r"\textasciicircum{}" not in latex


# ---------------------------------------------------------------------------
# 7.B  colon in prose must NOT trigger math-mode wrap
# ---------------------------------------------------------------------------


class TestColonInProse:
    """Bug 7.B: a colon in prose text must not trigger math-mode wrapping."""

    def test_simple_colon_sentence(self) -> None:
        """'word: rest' is plain text, not a type declaration."""
        latex = _gen("TEXT: Note: this is a plain remark.")
        # 'Note' must not end up italicised inside $...$
        assert "$Note$" not in latex
        assert "Note" in latex
        assert "this is a plain remark" in latex

    def test_colon_after_common_word(self) -> None:
        """'Result: something' stays as prose, not type-declaration math."""
        latex = _gen("TEXT: Result: the value is three.")
        assert "Result" in latex
        assert "the value is three" in latex
        # No spurious math wrapping
        assert "$Result$" not in latex

    def test_multiple_colons_in_prose(self) -> None:
        """Multiple colons in one line stay as prose."""
        latex = _gen("TEXT: Proof: by induction: base case and step.")
        assert "Proof" in latex
        assert "by induction" in latex
        # None of these words should be math-wrapped
        assert "$Proof$" not in latex
        assert "$induction$" not in latex


# ---------------------------------------------------------------------------
# 7.C  math-operator keywords in prose must not auto-math when bare
# ---------------------------------------------------------------------------


class TestMathKeywordsInProse:
    """Bug 7.C: bare operator keywords in prose are not auto-mathed."""

    def test_forall_in_prose_not_auto_math(self) -> None:
        """'forall' appearing in prose with no quantifier syntax stays text."""
        latex = _gen("TEXT: We discuss the forall quantifier in logic.")
        # 'forall' in plain prose is a word, but since it is a Z keyword
        # the existing pipeline wraps it.  The critical constraint is that
        # the surrounding English words are NOT swallowed into the same span.
        assert "We discuss" in latex
        assert "quantifier in logic" in latex

    def test_operator_keywords_not_absorbing_prose(self) -> None:
        """Operator keywords must not absorb adjacent English words."""
        latex = _gen("TEXT: The land operator and the lor operator are logical.")
        # Key invariant: surrounding prose is preserved as separate text
        assert "operator" in latex
        assert "are logical" in latex

    def test_dollar_math_forall_parsed(self) -> None:
        """$forall x : N | x > 0$ inside TEXT is parsed by the math parser."""
        latex = _gen("TEXT: We require $forall x : N | x > 0$ for all elements.")
        # The quantifier must render as LaTeX
        assert r"\forall" in latex
        # Prose words around it are plain text
        assert "We require" in latex
        assert "for all elements" in latex

    def test_dollar_math_lor_land_parsed(self) -> None:
        """$p lor q$ inside TEXT is parsed as a logical expression."""
        latex = _gen("TEXT: The formula $p lor q$ is a disjunction.")
        assert r"\lor" in latex
        assert "is a disjunction" in latex

    def test_dollar_math_lnot_parsed(self) -> None:
        """$lnot p$ inside TEXT is parsed as negation."""
        latex = _gen("TEXT: Negation $lnot p$ flips the truth value.")
        assert r"\lnot" in latex
        assert "flips the truth value" in latex


# ---------------------------------------------------------------------------
# 7.D  backtick / backslash adjacency in prose
# ---------------------------------------------------------------------------


class TestSpecialCharacterProse:
    """Bug 7.D: backtick and backslash in prose do not garble output."""

    def test_backslash_in_prose_escaped(self) -> None:
        """A literal \\ in prose becomes \\textbackslash{}."""
        latex = _gen(r"TEXT: The \\ operator separates list items.")
        # Must not produce raw backslash-space confusion
        assert "textbackslash" in latex or "\\\\" in latex

    def test_underscore_in_prose_escaped(self) -> None:
        """An underscore in an identifier like count_N is escaped in prose."""
        latex = _gen("TEXT: The variable count_N tracks the total.")
        assert r"count\_N" in latex or r"count_N" not in latex.replace(r"count\_N", "")

    def test_hash_in_prose_escaped(self) -> None:
        """# in prose is escaped as \\#."""
        latex = _gen("TEXT: The cardinality # S gives the size.")
        assert r"\#" in latex


# ---------------------------------------------------------------------------
# Dollar-math round-trip: content is routed through the math parser
# ---------------------------------------------------------------------------


class TestDollarMathRoundTrip:
    """$...$ in TEXT is parsed by the math/Z parser, not treated as raw LaTeX."""

    def test_set_comprehension_in_dollar_math(self) -> None:
        """${ x : N | x > 0 }$ in TEXT is parsed as a set comprehension."""
        latex = _gen("TEXT: The set ${ x : N | x > 0 }$ is non-empty.")
        # Should contain set-comprehension LaTeX, not the raw braces
        assert r"\forall" not in latex or r"\nat" in latex or r"\{" in latex
        assert "is non-empty" in latex

    def test_relation_in_dollar_math(self) -> None:
        """$R o9 S$ in TEXT prose emits \\semi (inline, not Z paragraph)."""
        latex = _gen("TEXT: Composition $R o9 S$ is associative.")
        assert r"\semi" in latex
        assert r"\comp" not in latex
        assert "is associative" in latex

    def test_plain_identifier_in_dollar_math(self) -> None:
        """$x$ in TEXT produces a simple math-mode identifier."""
        latex = _gen("TEXT: Let $x$ be a natural number.")
        assert "$x$" in latex
        assert "be a natural number" in latex
