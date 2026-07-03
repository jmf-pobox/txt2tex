"""Phase 1 strict inline-math tests: $...$ takes whiteboard notation only.

Under the Phase 1 strict model (docs/development/PLAN_text_inline_math.md §Phase 1):
- $...$ in TEXT: prose routes content through the real lexer → parser → generator.
- A backslash inside $...$ raises InlineMathError; use LATEX: for raw LaTeX.
- A Z paragraph construct (schema, axdef, etc.) inside $...$ raises InlineMathError.
- The inline flag (_in_z_paragraph=False) ensures o9 → \\semi (not \\comp).
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


class TestWhiteboardInlineMath:
    """$...$ routes whiteboard notation through the real parser."""

    def test_forall_inline(self) -> None:
        r"""$forall x : X | x land p$ emits \forall x : X @ x \land p."""
        latex = _gen("TEXT: We say $forall x : X | x land p$ holds.")
        assert r"\forall x : X @ x \land p" in latex

    def test_maplet_selection_inline(self) -> None:
        r"""$p.a |-> p.b$ emits p.a \mapsto p.b."""
        latex = _gen("TEXT: The pair $p.a |-> p.b$ is a maplet.")
        assert r"p.a \mapsto p.b" in latex

    def test_o9_inline_uses_semi_not_comp(self) -> None:
        r"""$a o9 b$ inline emits \semi, not \comp.

        The inline path sets _in_z_paragraph=False; only the Z-paragraph path
        (zed/axdef/schema blocks) produces \comp via _in_z_paragraph=True.
        """
        latex = _gen("TEXT: The composition $a o9 b$ is a relation.")
        assert r"\semi" in latex
        assert r"\comp" not in latex


class TestStrictBackslashError:
    r"""Any backslash inside $...$ raises InlineMathError in Phase 1.

    Error message: "$...$ is whiteboard-only inline math; raw LaTeX (...) belongs
    in a LATEX: block."
    """

    def test_backslash_geq_raises(self) -> None:
        r"""$\geq$ raises InlineMathError — raw LaTeX must go through LATEX:."""
        with pytest.raises(InlineMathError, match="whiteboard-only inline math"):
            _gen(r"TEXT: We need $n \geq 0$ here.")

    def test_backslash_leftrightarrow_raises(self) -> None:
        r"""$p \Leftrightarrow q$ raises — use $p <=> q$ (whiteboard) instead."""
        with pytest.raises(InlineMathError, match="whiteboard-only inline math"):
            _gen(r"TEXT: The biconditional $p \Leftrightarrow q$ holds.")

    def test_backslash_forall_raises(self) -> None:
        r"""$\forall x$ raises — use $forall x$ (whiteboard) instead."""
        with pytest.raises(InlineMathError, match="whiteboard-only inline math"):
            _gen(r"TEXT: The claim $\forall x$ is universal.")

    def test_backslash_in_raises(self) -> None:
        r"""$x \in S$ raises — use $x elem S$ (whiteboard) instead."""
        with pytest.raises(InlineMathError, match="whiteboard-only inline math"):
            _gen(r"TEXT: We have $x \in S$.")

    def test_blocked_command_raises(self) -> None:
        r"""$\input{secret.tex}$ raises — dangerous commands also hit strict check."""
        with pytest.raises(InlineMathError, match="whiteboard-only inline math"):
            _gen(r"TEXT: The value $\input{secret.tex}$ is computed.")

    def test_multiple_backslash_commands_raise(self) -> None:
        r"""$\forall x \in S \bullet x > 0$ raises on first backslash."""
        with pytest.raises(InlineMathError, match="whiteboard-only inline math"):
            _gen(r"TEXT: We require $\forall x \in S \bullet x > 0$.")


class TestParagraphConstructError:
    """Z paragraph constructs in $...$ raise InlineMathError.

    Error message: "$...$ takes an inline Z expression or predicate; schema/axdef/...
    is a Z paragraph — use a schema/axdef/zed block, not inline."
    """

    def test_schema_inline_raises(self) -> None:
        """$schema S end$ raises InlineMathError — Z paragraphs not allowed inline."""
        with pytest.raises(InlineMathError, match="Z paragraph"):
            _gen("TEXT: $schema S end$")


class TestEmptyInlineMath:
    """A whitespace/empty $...$ span is left unchanged, not an error.

    An empty or whitespace-only span parses to an empty Document (no items),
    which is NOT a Z paragraph construct and must not raise the paragraph
    error — it is left in place like a parse failure (Bugbot #78).
    """

    def test_whitespace_span_does_not_raise(self) -> None:
        """$ $ (whitespace only) does not raise InlineMathError."""
        latex = _gen("TEXT: A degenerate $ $ span here.")
        assert "span here" in latex

    def test_whitespace_span_left_unchanged(self) -> None:
        """The whitespace span is emitted unchanged (no paragraph error)."""
        # Must not raise; the sentence renders around the untouched span.
        latex = _gen("TEXT: Text $  $ more.")
        assert "more" in latex
