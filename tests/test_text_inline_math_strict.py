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


class TestSetDifferenceInlineMath:
    r"""$A \ B$ (whiteboard set difference) is allowed in $...$ spans.

    The whiteboard set-difference operator is always written ``A \\ B``
    (backslash surrounded by spaces).  ``re.search(r"\\[A-Za-z]", inner)``
    does NOT match it, so it is not rejected as a raw LaTeX command.
    """

    def test_set_difference_inline(self) -> None:
        r"""$A \ B$ parses and emits A \setminus B."""
        latex = _gen("TEXT: The complement is $A \\ B$ here.")
        assert r"\setminus" in latex

    def test_set_difference_in_expression(self) -> None:
        r"""$S \ T$ works as inline set difference."""
        latex = _gen("TEXT: The result $S \\ T$ is non-empty.")
        assert r"\setminus" in latex


class TestStrictBackslashError:
    r"""Raw LaTeX commands (\cmd) in $...$ raise InlineMathError.

    A ``\\cmd`` pattern (backslash immediately before a letter) is rejected.
    The whiteboard set-difference operator ``A \\ B`` (backslash + space) is
    allowed and does NOT trigger this error.

    Error message: "$...$ is whiteboard notation only; raw LaTeX (...) belongs
    in a LATEX: block."
    """

    def test_raw_geq_raises(self) -> None:
        r"""$\geq$ raises InlineMathError — starts with SETMINUS, no left operand."""
        with pytest.raises(InlineMathError, match="whiteboard notation only"):
            _gen(r"TEXT: We need $\geq 0$ to hold.")

    def test_raw_forall_raises(self) -> None:
        r"""$\forall x$ raises InlineMathError — write $forall x : T | P$ instead."""
        with pytest.raises(InlineMathError, match="whiteboard notation only"):
            _gen(r"TEXT: The claim $\forall x$ is universal.")

    def test_backslash_geq_raises(self) -> None:
        r"""$n \geq 0$ raises InlineMathError — \g is a raw LaTeX command pattern."""
        with pytest.raises(InlineMathError, match="whiteboard notation only"):
            _gen(r"TEXT: We need $n \geq 0$ here.")

    def test_backslash_leftrightarrow_raises(self) -> None:
        r"""$p \Leftrightarrow q$ raises — use $p <=> q$ (whiteboard) instead."""
        with pytest.raises(InlineMathError, match="whiteboard notation only"):
            _gen(r"TEXT: The biconditional $p \Leftrightarrow q$ holds.")

    def test_backslash_forall_raises(self) -> None:
        r"""$\forall x$ raises — use $forall x$ (whiteboard) instead."""
        with pytest.raises(InlineMathError, match="whiteboard notation only"):
            _gen(r"TEXT: The claim $\forall x$ is universal.")

    def test_backslash_in_raises(self) -> None:
        r"""$x \in S$ raises — use $x elem S$ (whiteboard) instead."""
        with pytest.raises(InlineMathError, match="whiteboard notation only"):
            _gen(r"TEXT: We have $x \in S$.")

    def test_blocked_command_raises(self) -> None:
        r"""$\input{secret.tex}$ raises — dangerous commands also hit strict check."""
        with pytest.raises(InlineMathError, match="whiteboard notation only"):
            _gen(r"TEXT: The value $\input{secret.tex}$ is computed.")

    def test_multiple_backslash_commands_raise(self) -> None:
        r"""$\forall x \in S \bullet x > 0$ raises on first backslash."""
        with pytest.raises(InlineMathError, match="whiteboard notation only"):
            _gen(r"TEXT: We require $\forall x \in S \bullet x > 0$.")


class TestParagraphConstructError:
    """Z paragraph constructs in $...$ raise InlineMathError.

    Error message: "$...$ takes an inline Z expression or predicate; schema/axdef/...
    is a Z paragraph — use a schema/axdef/zed block, not inline."
    """

    def test_schema_inline_raises(self) -> None:
        """$schema S end$ raises InlineMathError — Z paragraphs not allowed inline."""
        with pytest.raises(InlineMathError, match="block-level Z"):
            _gen("TEXT: $schema S end$")


class TestSourceLocationInError:
    r"""InlineMathError messages include the source line number and span text.

    The format is "line N: $span$ — <original message>".  Every raise site in
    _process_explicit_dollar_math embeds ``actual_line`` (node base line + the
    count of newlines in the block text before the match) and the full
    ``$inner$`` span so users can locate the offending text in a large file.
    """

    # _gen prepends "=== Test ===\n\n" (2 lines), so the first TEXT: is line 3.

    def test_raw_latex_error_includes_line_number(self) -> None:
        r"""InlineMathError for $\geq$ includes the source line number."""
        with pytest.raises(InlineMathError) as exc_info:
            _gen(r"TEXT: We need $\geq 0$ here.")
        msg = str(exc_info.value)
        assert "line 3:" in msg

    def test_raw_latex_error_includes_span_text(self) -> None:
        r"""InlineMathError for $\geq$ includes the offending $...$  span."""
        with pytest.raises(InlineMathError) as exc_info:
            _gen(r"TEXT: We need $\geq 0$ here.")
        msg = str(exc_info.value)
        # Span text is the full $inner$ with delimiters.
        assert r"$\geq 0$" in msg

    def test_paragraph_construct_error_includes_line_number(self) -> None:
        """InlineMathError for $schema S end$ includes the source line number."""
        with pytest.raises(InlineMathError) as exc_info:
            _gen("TEXT: $schema S end$")
        msg = str(exc_info.value)
        assert "line 3:" in msg

    def test_paragraph_construct_error_includes_span_text(self) -> None:
        """InlineMathError for $schema S end$ includes the offending span."""
        with pytest.raises(InlineMathError) as exc_info:
            _gen("TEXT: $schema S end$")
        msg = str(exc_info.value)
        assert "$schema S end$" in msg

    def test_line_arithmetic_across_blocks(self) -> None:
        r"""Error on the third TEXT: block reports its source line, not block 1's line.

        Three separate TEXT: paragraphs (blank lines between them) produce three
        Paragraph nodes.  The bad $\rightarrow$ span is in the third paragraph
        (source line 7 after the "=== Test ===\\n\\n" prefix).  The error must
        say "line 7:", not "line 3:" (the first paragraph's line).
        """
        source = (
            "TEXT: first paragraph.\n\n"
            "TEXT: second paragraph.\n\n"
            r"TEXT: third paragraph with bad $\rightarrow$ span."
        )
        with pytest.raises(InlineMathError) as exc_info:
            _gen(source)
        msg = str(exc_info.value)
        assert "line 7:" in msg
        assert "line 3:" not in msg


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


class TestBlockLineNumber:
    """Line numbers are exact for separated blocks; coalesced blocks approximate.

    Adjacent TEXT: lines (no blank line between) coalesce into one Paragraph,
    joined with a space (required by the Phase 1 bare-prose heuristics, which
    assume ". " sentence boundaries). So a coalesced block's error reports the
    block's FIRST line — a documented Phase-1 approximation. Single and
    blank-separated blocks are exact. Phase 2 removes the heuristics and makes
    coalesced line numbers exact.
    """

    def test_separated_block_reports_exact_line(self) -> None:
        r"""A blank-separated TEXT block reports the span's exact line."""
        # _gen prepends "=== Test ===\n\n" (lines 1-2); blank-separated blocks
        # are at lines 3 and 5; the bad span sits on line 5.
        with pytest.raises(InlineMathError) as exc_info:
            _gen("TEXT: first block.\n\nTEXT: second has $\\geq$ x.")
        assert "line 5:" in str(exc_info.value)

    def test_coalesced_block_reports_block_first_line(self) -> None:
        r"""A span on a coalesced block reports the block's first line.

        Documented Phase-1 approximation (space-join for heuristic
        compatibility); exact coalesced line numbers land in Phase 2.
        """
        with pytest.raises(InlineMathError) as exc_info:
            _gen("TEXT: first line here.\nTEXT: second has $\\geq$ x.")
        # Both TEXT: lines coalesce; the block starts at line 3, so the span
        # reports line 3 (the exact line is 4 — see class docstring).
        assert "line 3:" in str(exc_info.value)
