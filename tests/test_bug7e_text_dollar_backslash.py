"""Tests for the strict $...$ inline-math model superseding bug 7.E.

Bug 7.E (2026-05-21): backslash-prefixed LaTeX commands inside $...$ were
re-lexed by the whiteboard engine, producing garbled output — a backslash parsed as
SETMINUS, ``Leftrightarrow`` as an applied identifier.

The original fix (allow-list pass-through) is superseded by the Phase 1 strict
inline-math model (docs/development/PLAN_text_inline_math.md §Phase 1):

- $...$ in TEXT: prose is whiteboard-only.  The content is routed through the
  real lexer → parser → generator (no backslash).
- A backslash inside $...$ raises ``InlineMathError`` with a clear message
  directing the author to either use whiteboard notation (``$p <=> q$``) or
  move raw LaTeX to a ``LATEX:`` block.

The garbled-output symptom of bug 7.E can no longer occur because any span
with a backslash is rejected before parsing.
"""

from __future__ import annotations

import pytest

from txt2tex.codegen.text_pipeline import InlineMathError
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


class TestBackslashInDollarMathRaisesError:
    r"""Bug 7.E superseded: any backslash in $...$ raises ValueError.

    The old behaviour (allow-list pass-through, bug 7.E fix) is replaced by a
    hard error.  Use whiteboard notation inside $...$:

        $p <=> q$       (not $p \Leftrightarrow q$)
        $forall x : N | P$  (not $\forall x : N | P$)
        $x elem S$      (not $x \in S$)

    Or move raw LaTeX to a LATEX: block.
    """

    def test_leftrightarrow_raises(self) -> None:
        r"""$p \Leftrightarrow q$ raises — use $p <=> q$ instead."""
        with pytest.raises(InlineMathError, match="whiteboard-only inline math"):
            _gen(r"TEXT: The formula $p \Leftrightarrow x > 1$ holds.")

    def test_rightarrow_raises(self) -> None:
        r"""$p \Rightarrow q$ raises — use $p => q$ instead."""
        with pytest.raises(InlineMathError, match="whiteboard-only inline math"):
            _gen(r"TEXT: Note that $p \Rightarrow q$ is an implication.")

    def test_forall_backslash_raises(self) -> None:
        r"""$\forall x$ raises — use $forall x : T | P$ instead."""
        with pytest.raises(InlineMathError, match="whiteboard-only inline math"):
            _gen(r"TEXT: The claim $\forall x$ is universal.")

    def test_exists_backslash_raises(self) -> None:
        r"""$\exists x$ raises — use $exists x : T | P$ instead."""
        with pytest.raises(InlineMathError, match="whiteboard-only inline math"):
            _gen(r"TEXT: We have $\exists x$ in the set.")

    def test_land_backslash_raises(self) -> None:
        r"""$p \land q$ raises — use $p land q$ instead."""
        with pytest.raises(InlineMathError, match="whiteboard-only inline math"):
            _gen(r"TEXT: The conjunction $p \land q$ is true.")

    def test_lor_backslash_raises(self) -> None:
        r"""$p \lor q$ raises — use $p lor q$ instead."""
        with pytest.raises(InlineMathError, match="whiteboard-only inline math"):
            _gen(r"TEXT: The disjunction $p \lor q$ is false.")

    def test_neg_backslash_raises(self) -> None:
        r"""$\neg p$ raises — use $lnot p$ instead."""
        with pytest.raises(InlineMathError, match="whiteboard-only inline math"):
            _gen(r"TEXT: Negation $\neg p$ is the complement.")

    def test_in_backslash_raises(self) -> None:
        r"""$x \in S$ raises — use $x elem S$ instead."""
        with pytest.raises(InlineMathError, match="whiteboard-only inline math"):
            _gen(r"TEXT: We know $x \in S$.")

    def test_multiple_backslash_commands_raise(self) -> None:
        r"""Multiple \cmd in a single $...$ span raise on the first backslash."""
        with pytest.raises(InlineMathError, match="whiteboard-only inline math"):
            _gen(r"TEXT: $\forall x \in S \bullet x > 0$")


class TestWhiteboardAlternatives:
    r"""Whiteboard equivalents of the old backslash constructs parse correctly.

    The authors' workaround from bug 7.E — "use the txt2tex ascii operators
    inside $...$" — is now the required approach.
    """

    def test_ascii_biconditional(self) -> None:
        r"""$p <=> q$ (whiteboard) emits \Leftrightarrow (or \iff in fuzz)."""
        latex = _gen("TEXT: We have $p <=> q$ as an equivalence.")
        assert r"\iff" in latex or r"\Leftrightarrow" in latex

    def test_ascii_implication(self) -> None:
        r"""$p => q$ (whiteboard) emits \implies (fuzz) or \Rightarrow (std)."""
        latex = _gen("TEXT: We have $p => q$ as an implication.")
        assert r"\implies" in latex or r"\Rightarrow" in latex

    def test_ascii_forall(self) -> None:
        r"""$forall x : N | x > 0$ (whiteboard) emits \forall."""
        latex = _gen("TEXT: The claim $forall x : N | x > 0$ holds.")
        assert r"\forall" in latex

    def test_ascii_elem(self) -> None:
        r"""$x elem S$ (whiteboard) emits \in."""
        latex = _gen("TEXT: We know $x elem S$.")
        assert r"\in" in latex

    def test_prose_preserved_around_whiteboard_span(self) -> None:
        """Prose outside $...$ is not affected."""
        latex = _gen("TEXT: The formula $p <=> q$ is important here.")
        assert "The formula" in latex
        assert "is important here" in latex
