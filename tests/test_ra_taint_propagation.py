"""Tests for RA (relational-algebra) taint propagation by reference.

RA constructs (join, pi/project, sigma/restrict, div, group, ungroup, extend)
are not fuzz-checkable, so an abbreviation whose RHS contains one is routed
to inline math (``\\noindent$...$``) instead of a fuzz ``\\begin{zed}``
paragraph.  That routing decision used to look only for a literal RA
operator token.  An abbreviation that merely *references* an RA-defined
name — with no RA operator of its own — was wrongly kept inside the zed
block, producing a fuzz "Identifier ... is not declared" error, because RA
names are invisible to fuzz.

These tests pin the fix: RA-ness propagates by reference through
``LaTeXGenerator._ra_tainted_names``, a set of names defined by RA
abbreviations, computed to a fixpoint over document items.  RA names are
display-math only, so fuzz imposes no declare-before-use ordering on
them -- an abbreviation may legally reference an RA name defined *later*
in the document, or transitively through a chain of forward references.
A single forward pass over the abbreviation list misses that; the
collection loop repeats until a full scan adds nothing.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from txt2tex.ast_nodes import AxDef, Document, Part, Section, Solution
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

_FORWARD_REF_SRC = """given T
axdef
  S : T <-> T
end

B == A union S

A == S join S

D == B union S
"""

_TRANSITIVE_FORWARD_SRC = """given T
axdef
  S : T <-> T
end

C == B union S

B == A union S

A == S join S
"""


# ---------------------------------------------------------------------------
# Direct reference: Combined references RJoin (RA-tainted), no RA operator
# ---------------------------------------------------------------------------


class TestDirectReferenceTaint:
    """An abbreviation referencing an RA-tainted name is inline math."""

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
        """`RJoin == S join U` — direct RA operator — also routes to inline math."""
        latex = _fragment(_REPRO_SRC)
        assert "\\noindent\n$RJoin == \\mathrm{Join}(S, U)$" in latex


# ---------------------------------------------------------------------------
# Transitivity: Extra references Combined, which is itself only RA-tainted
# by reference (no RA operator of its own)
# ---------------------------------------------------------------------------


class TestTransitiveTaint:
    """RA taint propagates through a chain of references, not just one hop."""

    def test_extra_referencing_combined_is_display_math(self) -> None:
        """`Extra == Combined setminus S` is inline math via transitive taint."""
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


# ---------------------------------------------------------------------------
# Axdef bridge: RJoin is ALSO declared in an axdef, so fuzz genuinely knows
# it. Referencing it must NOT taint the referencing abbreviation, even
# though RJoin also has an (inline-math-only) RA definition.
# ---------------------------------------------------------------------------


class TestAxdefBridgeUntaints:
    """A name declared in an axdef is never RA-tainted by reference."""

    def test_combined_stays_in_zed_block(self) -> None:
        """`Combined == RJoin union S` renders INSIDE `\\begin{zed}`.

        RJoin's RA definition (`RJoin == S join U`) still degrades to
        inline math on its own -- it contains a literal `join` -- but
        that must not poison `Combined`, since RJoin is independently
        declared in the axdef above and so is a real, known-to-fuzz name.
        """
        latex = _fragment(_BRIDGE_SRC)
        assert any("Combined == RJoin \\cup S" in block for block in _zed_blocks(latex))

    def test_combined_not_display_math(self) -> None:
        """`Combined` must not be pushed out to inline math."""
        latex = _fragment(_BRIDGE_SRC)
        assert "$Combined == RJoin \\cup S$" not in latex

    def test_rjoin_definition_still_display_math(self) -> None:
        """`RJoin == S join U` still degrades -- it contains a literal `join`."""
        latex = _fragment(_BRIDGE_SRC)
        assert "\\noindent\n$RJoin == \\mathrm{Join}(S, U)$" in latex

    def test_bridge_document_fuzz_checks_clean(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """The axdef-declared name lets `Combined` type-check with real fuzz."""
        ast = Parser(Lexer(_BRIDGE_SRC).tokenize()).parse()
        assert isinstance(ast, Document)
        latex = LaTeXGenerator(use_fuzz=True).generate_document(ast)

        tex_path = tmp_path / "ra_taint_bridge.tex"
        tex_path.write_text(latex)

        passed = typecheck_fuzz(tex_path)
        captured = capsys.readouterr()

        assert passed, captured.out + captured.err
        assert "is not declared" not in captured.err


# ---------------------------------------------------------------------------
# Regression: without the axdef bridge, RJoin has no other declaration, so
# Combined must still degrade to inline math (the original fix, unchanged).
# ---------------------------------------------------------------------------


class TestNoBridgeStillTaints:
    """Without an independent declaration, RA-by-reference taint still applies."""

    def test_combined_still_display_math_without_axdef_bridge(self) -> None:
        """Same document, minus the `RJoin : T <-> T` axdef line, still degrades."""
        latex = _fragment(_REPRO_SRC)
        assert "\\noindent\n$Combined == RJoin \\cup S$" in latex

    def test_no_bridge_document_fuzz_checks_clean(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Degrading to inline math still avoids fuzz's "not declared" error."""
        ast = Parser(Lexer(_REPRO_SRC).tokenize()).parse()
        assert isinstance(ast, Document)
        latex = LaTeXGenerator(use_fuzz=True).generate_document(ast)

        tex_path = tmp_path / "ra_taint_no_bridge.tex"
        tex_path.write_text(latex)

        passed = typecheck_fuzz(tex_path)
        captured = capsys.readouterr()

        assert passed, captured.out + captured.err
        assert "is not declared" not in captured.err


# ---------------------------------------------------------------------------
# Nested-under-Part: the axdef/RA chain is not a Document-level sibling --
# it is entirely inside a single Part's ``.items``.  ``_parse_part`` consumes
# every item after ``(a) ...`` up to the next part/solution/section marker,
# so any Z paragraph following a part label nests here rather than sitting
# beside it.  Before the pre-pass refactor, ``_generate_part``'s default
# (subsection) branch called ``generate_document_item`` per item directly,
# never routing through ``_generate_document_items_with_consolidation`` --
# the only place the old code updated ``_fuzz_declared_names`` and
# ``_ra_tainted_names``.  RJoin's declaration and taint were silently
# dropped, and ``Combined`` was left inside a fuzz zed block it does not
# belong in, producing "Identifier RJoin is not declared".
# ---------------------------------------------------------------------------

_PART_NO_BRIDGE_SRC = """=== Q1 ===

** Solution 1 **

(a) Relational algebra

given T

axdef
  S : T <-> T
  U : T <-> T
end

RJoin == S join U

Combined == RJoin union S
"""


class TestNestedUnderPartTaint:
    """The declared/tainted-name pre-pass reaches items nested under a Part."""

    def test_part_items_actually_nest_the_declaration(self) -> None:
        """Sanity check: RJoin's axdef is a Part item, not a Document item.

        Confirms this fixture exercises the exact layout Cursor flagged --
        without this, the regression below would pass for the wrong reason.
        """
        ast = Parser(Lexer(_PART_NO_BRIDGE_SRC).tokenize()).parse()
        assert isinstance(ast, Document)
        section = ast.items[0]
        assert isinstance(section, Section)
        solution = section.items[0]
        assert isinstance(solution, Solution)
        part = solution.items[0]
        assert isinstance(part, Part)
        assert any(isinstance(item, AxDef) for item in part.items)

    def test_combined_pushed_to_inline_math_without_bridge(self) -> None:
        """Without an axdef bridge, `Combined` must degrade even nested in a Part."""
        latex = _fragment(_PART_NO_BRIDGE_SRC)
        assert "$Combined == RJoin \\cup S$" in latex

    def test_combined_not_left_in_zed_block(self) -> None:
        """Leaving `Combined` in a zed block here is the regression Cursor found."""
        latex = _fragment(_PART_NO_BRIDGE_SRC)
        for block in _zed_blocks(latex):
            assert "Combined" not in block

    def test_nested_part_document_fuzz_checks_clean(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """The regression manifests as fuzz's "not declared" error; must not recur."""
        ast = Parser(Lexer(_PART_NO_BRIDGE_SRC).tokenize()).parse()
        assert isinstance(ast, Document)
        latex = LaTeXGenerator(use_fuzz=True).generate_document(ast)

        tex_path = tmp_path / "ra_taint_part_no_bridge.tex"
        tex_path.write_text(latex)

        passed = typecheck_fuzz(tex_path)
        captured = capsys.readouterr()

        assert passed, captured.out + captured.err
        assert "is not declared" not in captured.err


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
