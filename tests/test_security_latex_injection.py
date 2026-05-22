"""Security tests: LaTeX injection via $...$ in TEXT prose is blocked.

The allow-list in _process_explicit_dollar_math must reject dangerous TeX
primitives that could execute shell commands, read files, or redefine the
engine.  Any $...\blocked_cmd...$ span must be rendered as literal text
(escaped dollar signs), never as math mode that pdflatex would evaluate.
"""

from __future__ import annotations

import pytest

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


def _is_safe(latex: str, dangerous_cmd: str) -> bool:
    """Return True if the dangerous command never appears as an active TeX call.

    A command is 'active' when preceded by a backslash that is not itself the
    result of escaping (i.e. not \\textbackslash{}).  We detect safety by
    confirming the dangerous token does not appear literally as \\cmd in the
    output.
    """
    return dangerous_cmd not in latex


# ---------------------------------------------------------------------------
# Block-listed commands — each must NOT appear verbatim in emitted LaTeX
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("prose_fragment", "dangerous_cmd"),
    [
        # File inclusion
        (r"TEXT: The value $\input{secret.tex}$ is computed.", r"\input"),
        (r"TEXT: See $\include{appendix}$ for more.", r"\include"),
        # Shell escape / write
        (r"TEXT: Step $\write18{rm -rf .}$ is executed.", r"\write"),
        (r"TEXT: Output $\immediate\write18{ls}$ here.", r"\write"),
        # Category code manipulation
        (r"TEXT: Set $\catcode`@=11$ for active chars.", r"\catcode"),
        # Definition commands
        (r"TEXT: We define $\def\evil{bad}$ inline.", r"\def"),
        (r"TEXT: We define $\edef\evil{bad}$ inline.", r"\edef"),
        (r"TEXT: We define $\gdef\evil{bad}$ inline.", r"\gdef"),
        (r"TEXT: We define $\xdef\evil{bad}$ inline.", r"\xdef"),
        # let assignment
        (r"TEXT: Assignment $\let\oldcmd=\newcmd$ here.", r"\let"),
        # csname construction
        (r"TEXT: Dynamic $\csname mycommand\endcsname$ access.", r"\csname"),
        (r"TEXT: Dynamic $\csname mycommand\endcsname$ access.", r"\endcsname"),
        # LuaTeX direct Lua execution
        (r"TEXT: Lua $\directlua{os.execute('ls')}$ call.", r"\directlua"),
        # File I/O
        (r"TEXT: Open $\openin\myfile=secret.txt$ then read.", r"\openin"),
        (r"TEXT: Write $\openout\myfile=out.txt$ to file.", r"\openout"),
        # expansion control
        (r"TEXT: Expand $\expandafter\cmd$ next.", r"\expandafter"),
        (r"TEXT: Unexpand $\noexpand\cmd$ here.", r"\noexpand"),
    ],
)
def test_blocked_command_not_in_output(prose_fragment: str, dangerous_cmd: str) -> None:
    """Blocked LaTeX commands must not appear verbatim in the emitted .tex."""
    latex = _gen(prose_fragment)
    pos = latex.find(dangerous_cmd)
    snippet = latex[max(0, pos - 30) : pos + 50] if pos != -1 else ""
    assert _is_safe(latex, dangerous_cmd), (
        f"{dangerous_cmd!r} appeared verbatim in the emitted LaTeX.\n"
        f"Output snippet: {snippet!r}"
    )


# ---------------------------------------------------------------------------
# The $ delimiters of a blocked span must be escaped (literal \$ in output)
# ---------------------------------------------------------------------------


def test_blocked_span_dollar_delimiters_escaped() -> None:
    r"""$\input{...}$ renders with escaped dollar signs, not math mode."""
    latex = _gen(r"TEXT: The span $\input{secret.tex}$ is dangerous.")
    # The $ delimiters must have been escaped; literal \$ appears
    assert r"\$" in latex


def test_write18_dollar_delimiters_escaped() -> None:
    r"""$\write18{...}$ renders with escaped dollar signs."""
    latex = _gen(r"TEXT: Shell call $\write18{rm -rf .}$ is escaped.")
    assert r"\$" in latex


def test_csname_dollar_delimiters_escaped() -> None:
    r"""$\csname...\endcsname$ renders with escaped dollar signs."""
    latex = _gen(r"TEXT: Dynamic $\csname mycommand\endcsname$ is escaped.")
    assert r"\$" in latex


def test_def_dollar_delimiters_escaped() -> None:
    r"""$\def\evil{bad}$ renders with escaped dollar signs."""
    latex = _gen(r"TEXT: Define $\def\evil{bad}$ inline is escaped.")
    assert r"\$" in latex


# ---------------------------------------------------------------------------
# Unknown commands (not on allow-list, not on block-list) are also escaped
# ---------------------------------------------------------------------------


def test_unknown_command_escaped() -> None:
    r"""$\unknowncmd{x}$ — not on allow-list — is escaped, not passed through."""
    latex = _gen(r"TEXT: Unknown $\unknowncmd{x}$ is escaped.")
    # The unknown command must not appear as an active LaTeX command
    assert r"\unknowncmd" not in latex


# ---------------------------------------------------------------------------
# Allow-listed commands still pass through verbatim (bug 7.E regression)
# ---------------------------------------------------------------------------


def test_forall_allowed_passes_through() -> None:
    r"""$\forall x$ in TEXT prose passes through verbatim (on allow-list)."""
    latex = _gen(r"TEXT: The claim $\forall x$ is universal.")
    assert r"\forall" in latex
    assert r"\$" not in latex


def test_land_allowed_passes_through() -> None:
    r"""$p \land q$ in TEXT prose passes through verbatim."""
    latex = _gen(r"TEXT: The conjunction $p \land q$ is true.")
    assert r"\land" in latex
    assert r"\$" not in latex


def test_leftrightarrow_allowed_passes_through() -> None:
    r"""$p \Leftrightarrow q$ in TEXT prose passes through verbatim."""
    latex = _gen(r"TEXT: The biconditional $p \Leftrightarrow q$ holds.")
    assert r"\Leftrightarrow" in latex
    assert r"\$" not in latex


def test_in_allowed_passes_through() -> None:
    r"""$x \in S$ in TEXT prose passes through verbatim."""
    latex = _gen(r"TEXT: We know $x \in S$.")
    assert r"\in" in latex
    assert r"\$" not in latex


def test_exists_allowed_passes_through() -> None:
    r"""$\exists x$ in TEXT prose passes through verbatim."""
    latex = _gen(r"TEXT: We have $\exists x$ in the set.")
    assert r"\exists" in latex
    assert r"\$" not in latex


# ---------------------------------------------------------------------------
# Surrounding prose is not affected by the security fix
# ---------------------------------------------------------------------------


def test_prose_preserved_around_blocked_span() -> None:
    r"""Text before and after a blocked span is preserved."""
    latex = _gen(r"TEXT: Before $\input{file}$ and after.")
    assert "Before" in latex
    assert "and after" in latex


def test_prose_preserved_around_allowed_span() -> None:
    r"""Text before and after an allowed span is preserved."""
    latex = _gen(r"TEXT: We require $\forall x$ in all cases.")
    assert "We require" in latex
    assert "in all cases" in latex
