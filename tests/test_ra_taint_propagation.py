"""Tests for RA (relational-algebra) taint propagation by reference.

RA constructs (join, pi/project, sigma/restrict, div, group, ungroup, extend)
are not fuzz-checkable, so an abbreviation whose RHS contains one is routed
to display math (``\\noindent$...$``) instead of a fuzz ``\\begin{zed}``
paragraph.  That routing decision used to look only for a literal RA
operator token.  An abbreviation that merely *references* an RA-defined
name — with no RA operator of its own — was wrongly kept inside the zed
block, producing a fuzz "Identifier ... is not declared" error, because RA
names are invisible to fuzz.

These tests pin the fix: RA-ness propagates by reference through
``LaTeXGenerator._ra_tainted_names``, a forward-built set of names defined
by earlier RA abbreviations.  Fuzz requires declare-before-use, so a single
forward pass over document items suffices.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from txt2tex.ast_nodes import Document
from txt2tex.cli import typecheck_fuzz
from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser

if TYPE_CHECKING:
    import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _fragment(src: str) -> str:
    """Generate a LaTeX fragment (no preamble) from source."""
    ast = Parser(Lexer(src).tokenize()).parse()
    assert isinstance(ast, Document)
    return LaTeXGenerator(use_fuzz=True).generate_fragment(ast)


_REPRO_SRC = """given T
axdef
  S : T <-> T
  U : T <-> T
end

RJoin == S join U

Combined == RJoin union S
"""

_TRANSITIVE_SRC = """given T
axdef
  S : T <-> T
  U : T <-> T
end

RJoin == S join U

Combined == RJoin union S

Extra == Combined setminus S
"""

_PLAIN_Z_SRC = """given T
axdef
  A : P T
  B : P T
end

X == A union B
"""

_BRIDGE_SRC = """given T
axdef
  S : T <-> T
  U : T <-> T
  RJoin : T <-> T
end

RJoin == S join U

Combined == RJoin union S
"""


# ---------------------------------------------------------------------------
# Direct reference: Combined references RJoin (RA-tainted), no RA operator
# ---------------------------------------------------------------------------


class TestDirectReferenceTaint:
    """An abbreviation referencing an RA-tainted name is display math."""

    def test_combined_is_display_math_not_zed(self) -> None:
        """`Combined == RJoin union S` emits as `$...$`, no RA operator present."""
        latex = _fragment(_REPRO_SRC)
        assert "\\noindent\n$Combined == RJoin \\cup S$" in latex

    def test_combined_line_not_between_zed_markers(self) -> None:
        """The Combined definition is outside any `\\begin{zed}...\\end{zed}` block."""
        latex = _fragment(_REPRO_SRC)
        for block in _zed_blocks(latex):
            assert "Combined" not in block

    def test_rjoin_itself_is_display_math(self) -> None:
        """`RJoin == S join U` — direct RA operator — also routes to display math."""
        latex = _fragment(_REPRO_SRC)
        assert "\\noindent\n$RJoin == \\mathrm{Join}(S, U)$" in latex


# ---------------------------------------------------------------------------
# Transitivity: Extra references Combined, which is itself only RA-tainted
# by reference (no RA operator of its own)
# ---------------------------------------------------------------------------


class TestTransitiveTaint:
    """RA taint propagates through a chain of references, not just one hop."""

    def test_extra_referencing_combined_is_display_math(self) -> None:
        """`Extra == Combined setminus S` is display math via transitive taint."""
        latex = _fragment(_TRANSITIVE_SRC)
        assert "\\noindent\n$Extra == Combined \\setminus S$" in latex

    def test_extra_line_not_between_zed_markers(self) -> None:
        """The Extra definition is outside any `\\begin{zed}...\\end{zed}` block."""
        latex = _fragment(_TRANSITIVE_SRC)
        for block in _zed_blocks(latex):
            assert "Extra" not in block


# ---------------------------------------------------------------------------
# Regression: plain Z union of ordinary declared sets stays in the zed block
# ---------------------------------------------------------------------------


class TestPlainZUntouched:
    """An abbreviation with no RA operator and no RA-tainted reference is unaffected."""

    def test_plain_union_stays_in_zed_block(self) -> None:
        """`X == A union B` over ordinary declared sets stays inside `\\begin{zed}`."""
        latex = _fragment(_PLAIN_Z_SRC)
        assert any("X == A \\cup B" in block for block in _zed_blocks(latex))

    def test_plain_union_not_routed_to_display_math(self) -> None:
        """The plain-Z abbreviation must not be pushed out to inline math."""
        latex = _fragment(_PLAIN_Z_SRC)
        assert "$X == A \\cup B$" not in latex


def _zed_blocks(latex: str) -> list[str]:
    """Return the content of each `\\begin{zed}...\\end{zed}` block in latex."""
    blocks: list[str] = []
    lines = latex.splitlines()
    in_block = False
    current: list[str] = []
    for line in lines:
        if line.strip() == r"\begin{zed}":
            in_block = True
            current = []
            continue
        if line.strip() == r"\end{zed}":
            in_block = False
            blocks.append("\n".join(current))
            continue
        if in_block:
            current.append(line)
    return blocks


# ---------------------------------------------------------------------------
# End-to-end: the repro document fuzz-type-checks clean
# ---------------------------------------------------------------------------


class TestFuzzEndToEnd:
    """The RA-taint-by-reference document type-checks with the real fuzz binary."""

    def test_repro_document_fuzz_checks_clean(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """`Combined == RJoin union S` no longer trips "not declared" in fuzz."""
        ast = Parser(Lexer(_REPRO_SRC).tokenize()).parse()
        assert isinstance(ast, Document)
        latex = LaTeXGenerator(use_fuzz=True).generate_document(ast)

        tex_path = tmp_path / "ra_taint_repro.tex"
        tex_path.write_text(latex)

        passed = typecheck_fuzz(tex_path)
        captured = capsys.readouterr()

        assert passed, captured.out + captured.err
        assert "is not declared" not in captured.err
