"""Regression tests for bug 7.E: backslash LaTeX commands inside $...$ are re-lexed.

When TEXT prose contains ``$p \\Leftrightarrow x > 1$``, the engine previously
routed the inner content through the math/Z lexer, which parsed \\ as the
SETMINUS operator and Leftrightarrow as an identifier.

Required behaviour: backslash-prefixed LaTeX commands inside $...$ in TEXT
prose are already-rendered LaTeX and must pass through verbatim.
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


class TestBackslashCommandsInDollarMath:
    """Bug 7.E: \\cmd inside $...$ in TEXT prose must pass through verbatim."""

    def test_leftrightarrow_passes_through(self) -> None:
        """$p \\Leftrightarrow x > 1$ emits verbatim, not as setminus + identifier."""
        latex = _gen(r"TEXT: The formula $p \Leftrightarrow x > 1$ holds.")
        # The LaTeX command must appear verbatim in the output
        assert r"\Leftrightarrow" in latex
        # The broken parse must NOT appear
        assert r"\setminus" not in latex
        assert "Leftrightarrow(" not in latex

    def test_rightarrow_passes_through(self) -> None:
        """$p \\Rightarrow q$ emits verbatim."""
        latex = _gen(r"TEXT: Note that $p \Rightarrow q$ is an implication.")
        assert r"\Rightarrow" in latex
        assert r"\setminus" not in latex

    def test_forall_backslash_passes_through(self) -> None:
        """$\\forall x$ emits verbatim."""
        latex = _gen(r"TEXT: The claim $\forall x$ is universal.")
        assert r"\forall" in latex
        assert r"\setminus" not in latex

    def test_exists_backslash_passes_through(self) -> None:
        """$\\exists x$ emits verbatim."""
        latex = _gen(r"TEXT: We have $\exists x$ in the set.")
        assert r"\exists" in latex
        assert r"\setminus" not in latex

    def test_land_backslash_passes_through(self) -> None:
        """$p \\land q$ emits verbatim."""
        latex = _gen(r"TEXT: The conjunction $p \land q$ is true.")
        assert r"\land" in latex
        assert r"\setminus" not in latex

    def test_lor_backslash_passes_through(self) -> None:
        """$p \\lor q$ emits verbatim."""
        latex = _gen(r"TEXT: The disjunction $p \lor q$ is false.")
        assert r"\lor" in latex
        assert r"\setminus" not in latex

    def test_neg_backslash_passes_through(self) -> None:
        """$\\neg p$ emits verbatim."""
        latex = _gen(r"TEXT: Negation $\neg p$ is the complement.")
        assert r"\neg" in latex
        assert r"\setminus" not in latex

    def test_in_backslash_passes_through(self) -> None:
        """$x \\in S$ emits verbatim."""
        latex = _gen(r"TEXT: We know $x \in S$.")
        assert r"\in" in latex
        assert r"\setminus" not in latex

    def test_mixed_ascii_and_backslash_commands(self) -> None:
        """Mixed: txt2tex ascii syntax and backslash commands coexist."""
        # txt2tex syntax (no backslash): should be translated to some biconditional
        # In fuzz mode <=> → \iff; in standard LaTeX mode → \Leftrightarrow
        latex_ascii = _gen("TEXT: We have $p <=> q$ as an equivalence.")
        assert r"\iff" in latex_ascii or r"\Leftrightarrow" in latex_ascii

        # LaTeX backslash command: should pass through verbatim
        latex_bs = _gen(r"TEXT: We have $p \Leftrightarrow q$ as an equivalence.")
        assert r"\Leftrightarrow" in latex_bs

    def test_surrounding_prose_is_preserved(self) -> None:
        """Prose outside $...$ is not affected by the fix."""
        latex = _gen(r"TEXT: The formula $p \Leftrightarrow q$ is important here.")
        assert "The formula" in latex
        assert "is important here" in latex

    def test_no_setminus_corruption(self) -> None:
        """The primary corruption symptom — setminus + identifier — is absent."""
        latex = _gen(r"TEXT: $p \Leftrightarrow x > 1$")
        # setminus should not appear (it is not a valid inline operator here)
        assert r"\setminus" not in latex
        # The identifier must not appear as a function call
        assert "Leftrightarrow(" not in latex

    def test_multiple_backslash_commands_in_span(self) -> None:
        """Multiple \\cmd in a single $...$ span all pass through."""
        latex = _gen(r"TEXT: $\forall x \in S \bullet x > 0$")
        assert r"\forall" in latex
        assert r"\in" in latex
        assert r"\setminus" not in latex
