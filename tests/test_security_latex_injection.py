"""Security tests: raw LaTeX injection via $...$ in TEXT prose is blocked.

Under the Phase 1 strict inline-math model ($...$ is whiteboard-only), any
backslash inside $...$ raises ``InlineMathError`` before any LaTeX is generated.
This applies uniformly to:

- Dangerous TeX primitives (\\input, \\write18, \\def, \\csname, ...) — they
  cannot appear in the emitted .tex because processing halts with an error.
- Previously "allowed" math commands (\\forall, \\land, \\Leftrightarrow, ...) —
  they are now invalid in $...$; use whiteboard notation ($forall ...$) instead.

The security invariant is preserved: a dangerous command written as
``$\\input{secret.tex}$`` in a TEXT: block can never reach pdflatex.
The enforcement mechanism changed from output-escaping to source-rejection.
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


# ---------------------------------------------------------------------------
# Dangerous commands — each raises ValueError before any output is produced
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "prose_fragment",
    [
        # File inclusion
        r"TEXT: The value $\input{secret.tex}$ is computed.",
        r"TEXT: See $\include{appendix}$ for more.",
        # Shell escape / write
        r"TEXT: Step $\write18{rm -rf .}$ is executed.",
        r"TEXT: Output $\immediate\write18{ls}$ here.",
        # Category code manipulation
        r"TEXT: Set $\catcode`@=11$ for active chars.",
        # Definition commands
        r"TEXT: We define $\def\evil{bad}$ inline.",
        r"TEXT: We define $\edef\evil{bad}$ inline.",
        r"TEXT: We define $\gdef\evil{bad}$ inline.",
        r"TEXT: We define $\xdef\evil{bad}$ inline.",
        # let assignment
        r"TEXT: Assignment $\let\oldcmd=\newcmd$ here.",
        # csname construction
        r"TEXT: Dynamic $\csname mycommand\endcsname$ access.",
        # LuaTeX direct Lua execution
        r"TEXT: Lua $\directlua{os.execute('ls')}$ call.",
        # File I/O
        r"TEXT: Open $\openin\myfile=secret.txt$ then read.",
        r"TEXT: Write $\openout\myfile=out.txt$ to file.",
        # expansion control
        r"TEXT: Expand $\expandafter\cmd$ next.",
        r"TEXT: Unexpand $\noexpand\cmd$ here.",
    ],
)
def test_dangerous_command_raises(prose_fragment: str) -> None:
    """Dangerous LaTeX commands in $...$ raise ValueError before any output."""
    with pytest.raises(InlineMathError, match="whiteboard-only inline math"):
        _gen(prose_fragment)


# ---------------------------------------------------------------------------
# Previously "unknown" commands also raise
# ---------------------------------------------------------------------------


def test_unknown_command_raises() -> None:
    r"""$\unknowncmd{x}$ raises — all backslashes are rejected."""
    with pytest.raises(InlineMathError, match="whiteboard-only inline math"):
        _gen(r"TEXT: Unknown $\unknowncmd{x}$ is rejected.")


# ---------------------------------------------------------------------------
# Previously "allowed" math commands also raise — use whiteboard notation
# ---------------------------------------------------------------------------


def test_forall_backslash_raises() -> None:
    r"""$\forall x$ raises — write $forall x : T | P$ (whiteboard) instead."""
    with pytest.raises(InlineMathError, match="whiteboard-only inline math"):
        _gen(r"TEXT: The claim $\forall x$ is universal.")


def test_land_backslash_raises() -> None:
    r"""$p \land q$ raises — write $p land q$ (whiteboard) instead."""
    with pytest.raises(InlineMathError, match="whiteboard-only inline math"):
        _gen(r"TEXT: The conjunction $p \land q$ is true.")


def test_leftrightarrow_backslash_raises() -> None:
    r"""$p \Leftrightarrow q$ raises — write $p <=> q$ (whiteboard) instead."""
    with pytest.raises(InlineMathError, match="whiteboard-only inline math"):
        _gen(r"TEXT: The biconditional $p \Leftrightarrow q$ holds.")


def test_in_backslash_raises() -> None:
    r"""$x \in S$ raises — write $x elem S$ (whiteboard) instead."""
    with pytest.raises(InlineMathError, match="whiteboard-only inline math"):
        _gen(r"TEXT: We know $x \in S$.")


def test_exists_backslash_raises() -> None:
    r"""$\exists x$ raises — write $exists x : T | P$ (whiteboard) instead."""
    with pytest.raises(InlineMathError, match="whiteboard-only inline math"):
        _gen(r"TEXT: We have $\exists x$ in the set.")


# ---------------------------------------------------------------------------
# Whiteboard $...$ syntax works correctly (the replacement for raw LaTeX)
# ---------------------------------------------------------------------------


def test_whiteboard_forall_renders() -> None:
    r"""$forall x : N | x > 0$ (whiteboard) renders \forall correctly."""
    latex = _gen("TEXT: The claim $forall x : N | x > 0$ holds.")
    assert r"\forall" in latex


def test_whiteboard_land_renders() -> None:
    r"""$p land q$ (whiteboard) renders \land correctly."""
    latex = _gen("TEXT: The conjunction $p land q$ is true.")
    assert r"\land" in latex


def test_whiteboard_biconditional_renders() -> None:
    r"""$p <=> q$ (whiteboard) renders \Leftrightarrow or \iff correctly."""
    latex = _gen("TEXT: The biconditional $p <=> q$ holds.")
    assert r"\iff" in latex or r"\Leftrightarrow" in latex


def test_whiteboard_elem_renders() -> None:
    r"""$x elem S$ (whiteboard) renders \in correctly."""
    latex = _gen("TEXT: We know $x elem S$.")
    assert r"\in" in latex


def test_prose_preserved_around_whiteboard_span() -> None:
    """Text before and after a whiteboard $...$ span is preserved."""
    latex = _gen("TEXT: Before $p land q$ and after.")
    assert "Before" in latex
    assert "and after" in latex
