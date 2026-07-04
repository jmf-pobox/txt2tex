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

from txt2tex.ast_nodes import (
    Abbreviation,
    AxDef,
    Document,
    Identifier,
    Part,
    Section,
    Solution,
    Zed,
)
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
# Forward reference: B references A, but A's RA-tainting definition appears
# LATER in the document. RA names are display-math only, so fuzz imposes no
# declare-before-use ordering on them -- a single forward collection pass
# missed this because B was visited before A had been marked tainted.
# ---------------------------------------------------------------------------


class TestForwardReferenceTaint:
    """RA taint reaches a fixpoint, independent of document order."""

    def test_b_referencing_later_a_is_display_math(self) -> None:
        """`B == A union S`, with `A == S join S` defined afterward, degrades."""
        latex = _fragment(_FORWARD_REF_SRC)
        assert "\\noindent\n$B == A \\cup S$" in latex

    def test_d_referencing_b_is_display_math(self) -> None:
        """`D == B union S` must also degrade -- B is tainted only by forward ref."""
        latex = _fragment(_FORWARD_REF_SRC)
        assert "\\noindent\n$D == B \\cup S$" in latex

    def test_b_and_d_not_left_in_zed_block(self) -> None:
        """Neither `B` nor `D` may land inside `\\begin{zed}...\\end{zed}`."""
        latex = _fragment(_FORWARD_REF_SRC)
        for block in _zed_blocks(latex):
            assert "B" not in block
            assert "D" not in block

    def test_forward_ref_document_fuzz_checks_clean(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Without the fixpoint, `D` was left in a zed block referencing an
        undeclared `B`, and fuzz reported "Identifier B is not declared".
        """
        ast = Parser(Lexer(_FORWARD_REF_SRC).tokenize()).parse()
        assert isinstance(ast, Document)
        latex = LaTeXGenerator(use_fuzz=True).generate_document(ast)

        tex_path = tmp_path / "ra_taint_forward_ref.tex"
        tex_path.write_text(latex)

        passed = typecheck_fuzz(tex_path)
        captured = capsys.readouterr()

        assert passed, captured.out + captured.err
        assert "is not declared" not in captured.err


# ---------------------------------------------------------------------------
# Transitive forward chain: C references B, B references A, and only A
# contains a literal RA operator -- taint must propagate across two forward
# hops (C -> B -> A), all defined in reverse dependency order.
# ---------------------------------------------------------------------------


class TestTransitiveForwardChainTaint:
    """RA taint propagates across multiple forward hops to a fixpoint."""

    def test_c_two_hops_from_tainting_operator_is_display_math(self) -> None:
        """`C == B union S` degrades even though the tainting `join` is on `A`,
        two forward references away.
        """
        latex = _fragment(_TRANSITIVE_FORWARD_SRC)
        assert "\\noindent\n$C == B \\cup S$" in latex

    def test_b_one_hop_from_tainting_operator_is_display_math(self) -> None:
        """`B == A union S` degrades -- one forward reference from the `join`."""
        latex = _fragment(_TRANSITIVE_FORWARD_SRC)
        assert "\\noindent\n$B == A \\cup S$" in latex

    def test_none_of_the_chain_left_in_zed_block(self) -> None:
        """`A`, `B`, and `C` must all sit outside any zed block."""
        latex = _fragment(_TRANSITIVE_FORWARD_SRC)
        for block in _zed_blocks(latex):
            assert "A" not in block
            assert "B" not in block
            assert "C" not in block

    def test_transitive_forward_chain_fuzz_checks_clean(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """The full two-hop forward chain still fuzz-checks clean."""
        ast = Parser(Lexer(_TRANSITIVE_FORWARD_SRC).tokenize()).parse()
        assert isinstance(ast, Document)
        latex = LaTeXGenerator(use_fuzz=True).generate_document(ast)

        tex_path = tmp_path / "ra_taint_transitive_forward.tex"
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


# ---------------------------------------------------------------------------
# Nested-inside-Zed: an explicit ``zed ... end`` block wraps its paragraphs
# in a *nested* Document (``Zed.content``), not a flat ``.items`` list like
# Section/Solution/Part.  Before the walker recursed into it, an RA
# abbreviation defined inside a zed block was invisible to the
# declared/tainted-name pre-pass -- ``Combined`` (a Document-level sibling
# referencing ``RJoin``) was wrongly left inside its own top-level zed
# block, referencing an identifier fuzz never saw declared.
#
# Note: the zed block's OWN rendering of ``RJoin == S join U`` is a
# separate, still-open defect -- ``_generate_zed`` renders every item
# unconditionally, so the RA-tainted line still ends up inside
# ``\begin{zed}...\end{zed}`` where fuzz will reject its ``\mathrm{Join}``.
# That is a generator/rendering gap, not a traversal gap, and is out of
# scope here (see PR #82 review discussion) -- these tests only pin the
# traversal fix's effect on ``Combined``, not a full fuzz round-trip.
# ---------------------------------------------------------------------------

_RA_INSIDE_ZED_SRC = """zed
  RJoin == S join U
end

Combined == RJoin union S
"""


class TestRAInsideZedBlockTaints:
    """RA taint from an abbreviation nested inside a zed block still propagates."""

    def test_combined_is_display_math_not_zed(self) -> None:
        """`Combined` degrades to inline math -- `RJoin` is defined inside `zed`."""
        latex = _fragment(_RA_INSIDE_ZED_SRC)
        assert "\\noindent\n$Combined == RJoin \\cup S$" in latex

    def test_combined_not_left_in_a_zed_block(self) -> None:
        """`Combined` must not sit in any `\\begin{zed}...\\end{zed}` block.

        Before the fix, this was exactly the regression: the pre-pass
        never descended into the zed block's nested Document, so
        ``RJoin`` was never marked RA-tainted, and ``Combined`` was left
        in its own zed block referencing an identifier fuzz never
        declared -- a real "not declared" error.
        """
        latex = _fragment(_RA_INSIDE_ZED_SRC)
        for block in _zed_blocks(latex):
            assert "Combined" not in block


class TestIterItemsDescendsIntoZed:
    """Direct unit test on the walker: it must yield a zed-nested item."""

    def test_walker_yields_abbreviation_nested_inside_zed(self) -> None:
        """A hand-built `Zed(content=Document([...]))` must surface its item.

        This pins the traversal contract itself, independent of whether
        any particular RA/taint scenario is reachable through the parser
        for a given nested item type (GivenType, FreeType, Abbreviation).
        """
        nested_abbrev = Abbreviation(
            name="Inner",
            expression=Identifier(name="S", line=2, column=3),
            line=2,
            column=3,
        )
        zed = Zed(
            content=Document(items=[nested_abbrev], line=1, column=1),
            line=1,
            column=1,
        )
        generator = LaTeXGenerator(use_fuzz=True)

        seen = list(generator._iter_items_in_document_order([zed]))

        assert zed in seen
        assert nested_abbrev in seen


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
