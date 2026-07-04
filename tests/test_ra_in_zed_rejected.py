"""Tests for rejecting a relational-algebra construct inside a `zed` block.

Closes issue #83.  ``_generate_zed`` used to emit every Zed-nested item
unconditionally into the ``\\begin{zed}...\\end{zed}`` box.  When an item's
RHS was RA-tainted (e.g. ``RJoin == S join U``), the generator rendered
``RJoin == \\mathrm{Join}(S, U)`` *inside* the box -- ``\\mathrm{Join}`` is
not Z, so fuzz rejected it with an opaque ``Syntax error at symbol "{"``.

Per the ADR in ``docs/DESIGN.md`` ("RA construct inside an explicit `zed`
block -- hard rejection"), the fix is to reject at generation time with an
actionable error, not to relocate the line or emit invalid Z.  These tests
pin that rejection: an RA-tainted item anywhere inside an explicit
``zed ... end`` block raises, naming the offending line and directing the
user to write it at top level.  A plain-Z-only ``zed`` block is unaffected.
"""

from __future__ import annotations

import pytest

from txt2tex.ast_nodes import (
    Abbreviation,
    BinaryOp,
    Declaration,
    Document,
    Identifier,
    NaturalJoin,
    SchemaInclusion,
    SchemaText,
)
from txt2tex.codegen.paragraphs import RaInZedError
from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_RA_ALONE_SRC = """given T
axdef
  S : T <-> T
  U : T <-> T
end

zed
  RJoin == S join U
end
"""

_MIXED_SRC = """given T
axdef
  S : T <-> T
  U : T <-> T
end

zed
  X == S union U
  RJoin == S join U
end
"""

_PLAIN_Z_ONLY_SRC = """given T
axdef
  S : T <-> T
  U : T <-> T
end

zed
  X == S union U
end
"""


def _fragment(src: str) -> str:
    """Generate a LaTeX fragment (no preamble) from source."""
    ast = Parser(Lexer(src).tokenize()).parse()
    assert isinstance(ast, Document)
    return LaTeXGenerator(use_fuzz=True).generate_fragment(ast)


# ---------------------------------------------------------------------------
# An RA abbreviation alone in a zed block
# ---------------------------------------------------------------------------


class TestRaAloneInZedRejected:
    """A `zed` block containing only an RA-tainted abbreviation is rejected."""

    def test_raises_ra_in_zed_error(self) -> None:
        with pytest.raises(RaInZedError):
            _fragment(_RA_ALONE_SRC)

    def test_error_names_offending_line(self) -> None:
        """`RJoin == S join U` sits on source line 8."""
        with pytest.raises(RaInZedError) as exc_info:
            _fragment(_RA_ALONE_SRC)
        assert "line 8" in str(exc_info.value)

    def test_error_directs_to_top_level(self) -> None:
        with pytest.raises(RaInZedError, match="top level"):
            _fragment(_RA_ALONE_SRC)

    def test_error_names_zed_block(self) -> None:
        with pytest.raises(RaInZedError, match="`zed` block"):
            _fragment(_RA_ALONE_SRC)


# ---------------------------------------------------------------------------
# A mixed block: one plain-Z line, one RA line -- only the RA line rejects
# ---------------------------------------------------------------------------


class TestMixedBlockRejectsOnlyRaLine:
    """A mixed `zed` block still rejects because of its one RA-tainted line."""

    def test_raises_ra_in_zed_error(self) -> None:
        with pytest.raises(RaInZedError):
            _fragment(_MIXED_SRC)

    def test_error_names_the_ra_line_not_the_plain_line(self) -> None:
        """`X == S union U` is line 8 (plain Z); `RJoin == S join U` is line 9."""
        with pytest.raises(RaInZedError) as exc_info:
            _fragment(_MIXED_SRC)
        message = str(exc_info.value)
        assert "line 9" in message
        assert "line 8" not in message


# ---------------------------------------------------------------------------
# Regression: a plain-Z-only zed block still generates cleanly
# ---------------------------------------------------------------------------


class TestPlainZOnlyZedStillGeneratesCleanly:
    """A `zed` block with no RA-tainted content is unaffected by the guard."""

    def test_no_regression(self) -> None:
        latex = _fragment(_PLAIN_Z_ONLY_SRC)
        assert r"\begin{zed}" in latex
        assert "X == S \\cup U" in latex


# ---------------------------------------------------------------------------
# HorizDef whose body is a SchemaText (`[ decl | pred ]`) -- issue #83 sweep.
#
# ``_generate_horiz_def`` guards its bare-Expr branch with
# ``_reject_ra_in_box`` but, until now, not its SchemaText branch.
# ``_generate_schema_text`` renders each declaration's type and each
# predicate via ``generate_expr`` with no guard at all, so an RA construct
# in either position rendered `\mathrm{Join}(...)` straight into the
# `\begin{zed}...\end{zed}` box -- exactly the #83 failure mode, just
# reached through a different AST shape.
# ---------------------------------------------------------------------------

_HORIZ_DEF_SCHEMA_TEXT_TYPE_RA_SRC = """given T
axdef
  S : T <-> T
  U : T <-> T
end

RJoinType defs [ x : S join U ]
"""

_HORIZ_DEF_SCHEMA_TEXT_PRED_RA_SRC = """given T
axdef
  S : T <-> T
  U : T <-> T
end

RJoinPred defs [ x : T | S join U = S ]
"""

_HORIZ_DEF_SCHEMA_TEXT_PLAIN_SRC = """given T
axdef
  S : P T
  U : P T
end

NatPair defs [ x : S; y : U | x elem S ]
"""


class TestHorizDefSchemaTextTypeRaRejected:
    """An RA construct in a SchemaText declaration's type is rejected."""

    def test_raises_ra_in_zed_error(self) -> None:
        with pytest.raises(RaInZedError):
            _fragment(_HORIZ_DEF_SCHEMA_TEXT_TYPE_RA_SRC)

    def test_error_names_offending_line(self) -> None:
        """`RJoinType defs [ x : S join U ]` sits on source line 7."""
        with pytest.raises(RaInZedError) as exc_info:
            _fragment(_HORIZ_DEF_SCHEMA_TEXT_TYPE_RA_SRC)
        assert "line 7" in str(exc_info.value)

    def test_error_directs_to_top_level(self) -> None:
        with pytest.raises(RaInZedError, match="top level"):
            _fragment(_HORIZ_DEF_SCHEMA_TEXT_TYPE_RA_SRC)


class TestHorizDefSchemaTextPredRaRejected:
    """An RA construct in a SchemaText predicate is rejected."""

    def test_raises_ra_in_zed_error(self) -> None:
        with pytest.raises(RaInZedError):
            _fragment(_HORIZ_DEF_SCHEMA_TEXT_PRED_RA_SRC)

    def test_error_names_offending_line(self) -> None:
        """`RJoinPred defs [ x : T | S join U = S ]` sits on source line 7."""
        with pytest.raises(RaInZedError) as exc_info:
            _fragment(_HORIZ_DEF_SCHEMA_TEXT_PRED_RA_SRC)
        assert "line 7" in str(exc_info.value)

    def test_error_directs_to_top_level(self) -> None:
        with pytest.raises(RaInZedError, match="top level"):
            _fragment(_HORIZ_DEF_SCHEMA_TEXT_PRED_RA_SRC)


class TestHorizDefSchemaTextPlainStillGeneratesCleanly:
    """A HorizDef with a plain-Z SchemaText body is unaffected by the guard."""

    def test_no_regression(self) -> None:
        latex = _fragment(_HORIZ_DEF_SCHEMA_TEXT_PLAIN_SRC)
        assert r"\begin{zed}" in latex
        assert "NatPair \\defs [ x : S; y : U | x \\in S ]" in latex


class TestSchemaTextAsInlineExprRoutesToDisplayMath:
    """SchemaText reached as an ``Expr`` operand is display math, never a box.

    ``_generate_schema_text_expr`` (the ``SchemaText`` handler registered on
    ``generate_expr``) is unreachable through the current grammar as a
    standalone value -- ``_parse_horiz_def`` special-cases a leading ``[``
    to always call ``_parse_schema_text`` directly, so a ``SchemaText`` can
    never end up as an operand nested inside a schema-calculus expression
    or as an ``Abbreviation`` RHS via parsing.  This test exercises the
    handler directly with a hand-built AST (matching the style of
    ``tests/test_ra_taint_propagation.py``) to confirm the *existing*
    behaviour: an RA-tainted SchemaText used as an Abbreviation's RHS is
    routed to display math by ``_generate_abbreviation``'s taint check,
    never reaching a boxed ``\\begin{zed}`` and never raising
    ``RaInZedError``.  The HorizDef fix above must not change this.
    """

    def test_ra_tainted_schema_text_as_abbrev_rhs_is_display_math(self) -> None:
        tainted_type = NaturalJoin(
            left=Identifier(name="S", line=1, column=1),
            right=Identifier(name="U", line=1, column=1),
            subscript=None,
            line=1,
            column=1,
        )
        decl = Declaration(
            variable="x",
            type_expr=tainted_type,
            is_primary_key=False,
            line=1,
            column=1,
        )
        schema_text = SchemaText(declarations=[decl], predicates=[], line=1, column=1)
        abbrev = Abbreviation(
            name="Combined",
            expression=schema_text,
            generic_params=None,
            line=1,
            column=1,
        )
        ast = Document(items=[abbrev], line=1, column=1)

        generator = LaTeXGenerator(use_fuzz=True)
        latex = generator.generate_fragment(ast)

        assert r"\begin{zed}" not in latex
        assert "\\noindent" in latex
        assert "$Combined == [ x : \\mathrm{Join}(S, U) ]$" in latex

    def test_ra_tainted_schema_text_predicate_as_abbrev_rhs_is_display_math(
        self,
    ) -> None:
        """RA taint in a *predicate* position must not raise either.

        Same routing argument as the declaration-type case above, but the
        RA-tainted expression sits in ``predicates`` rather than a
        declaration's ``type_expr``.
        """
        s_ref = Identifier(name="S", line=1, column=1)
        u_ref = Identifier(name="U", line=1, column=1)
        tainted_pred = BinaryOp(
            operator="=",
            left=NaturalJoin(left=s_ref, right=u_ref, subscript=None, line=1, column=1),
            right=Identifier(name="S", line=1, column=1),
            line=1,
            column=1,
        )
        decl = Declaration(
            variable="x",
            type_expr=Identifier(name="T", line=1, column=1),
            is_primary_key=False,
            line=1,
            column=1,
        )
        schema_text = SchemaText(
            declarations=[decl], predicates=[tainted_pred], line=1, column=1
        )
        abbrev = Abbreviation(
            name="Combined",
            expression=schema_text,
            generic_params=None,
            line=1,
            column=1,
        )
        ast = Document(items=[abbrev], line=1, column=1)

        generator = LaTeXGenerator(use_fuzz=True)
        latex = generator.generate_fragment(ast)

        assert r"\begin{zed}" not in latex
        assert "\\noindent" in latex
        assert "\\mathrm{Join}(S, U) = S" in latex

    def test_ra_tainted_schema_inclusion_generic_as_abbrev_rhs_is_display_math(
        self,
    ) -> None:
        """RA taint in a schema-inclusion generic argument must not raise either.

        Same routing argument again, but the RA-tainted expression sits in a
        nested ``SchemaInclusion``'s ``generics`` list -- exercising
        ``_emit_schema_inclusion`` reached through the inline path.
        """
        s_ref = Identifier(name="S", line=1, column=1)
        u_ref = Identifier(name="U", line=1, column=1)
        tainted_generic = NaturalJoin(
            left=s_ref, right=u_ref, subscript=None, line=1, column=1
        )
        incl = SchemaInclusion(
            name="Stack",
            decoration=None,
            generics=[tainted_generic],
            line=1,
            column=1,
        )
        schema_text = SchemaText(declarations=[incl], predicates=[], line=1, column=1)
        abbrev = Abbreviation(
            name="Combined",
            expression=schema_text,
            generic_params=None,
            line=1,
            column=1,
        )
        ast = Document(items=[abbrev], line=1, column=1)

        generator = LaTeXGenerator(use_fuzz=True)
        latex = generator.generate_fragment(ast)

        assert r"\begin{zed}" not in latex
        assert "\\noindent" in latex
        assert "Stack[\\mathrm{Join}(S, U)]" in latex


# ---------------------------------------------------------------------------
# SchemaInclusion generics (`Delta Stack[S join U]`) -- issue #83 sweep.
#
# ``_emit_schema_inclusion`` renders every generic-instantiation argument via
# ``generate_expr`` with no RA guard.  Every reachable caller is a boxed Z
# environment (axdef, gendef, schema, zed-via-HorizDef), so an RA-tainted
# generic rendered `\mathrm{Join}(...)` straight into the box -- the same
# #83 failure mode, reached through a schema-inclusion's generic-argument
# list instead of a declaration type or predicate.
# ---------------------------------------------------------------------------

_AXDEF_INCLUSION_GENERIC_RA_SRC = """given T
axdef
  S : T <-> T
  U : T <-> T
end

axdef
  Delta Stack[S join U]
where
  true
end
"""

_SCHEMA_INCLUSION_GENERIC_RA_SRC = """given T
axdef
  S : T <-> T
  U : T <-> T
end

schema Foo
  Delta Stack[S join U]
where
  true
end
"""

_AXDEF_INCLUSION_GENERIC_PLAIN_SRC = """given T, X
axdef
  Stack[X]
where
  true
end
"""


class TestAxdefSchemaInclusionGenericRaRejected:
    """An RA construct in an axdef schema-inclusion's generic arg is rejected."""

    def test_raises_ra_in_zed_error(self) -> None:
        with pytest.raises(RaInZedError):
            _fragment(_AXDEF_INCLUSION_GENERIC_RA_SRC)

    def test_error_names_offending_line(self) -> None:
        """`Delta Stack[S join U]` sits on source line 8."""
        with pytest.raises(RaInZedError) as exc_info:
            _fragment(_AXDEF_INCLUSION_GENERIC_RA_SRC)
        assert "line 8" in str(exc_info.value)

    def test_error_directs_to_top_level(self) -> None:
        with pytest.raises(RaInZedError, match="top level"):
            _fragment(_AXDEF_INCLUSION_GENERIC_RA_SRC)

    def test_error_names_axdef_block(self) -> None:
        with pytest.raises(RaInZedError, match="`axdef` block"):
            _fragment(_AXDEF_INCLUSION_GENERIC_RA_SRC)


class TestSchemaInclusionGenericRaRejected:
    """An RA construct in a schema's schema-inclusion generic arg is rejected."""

    def test_raises_ra_in_zed_error(self) -> None:
        with pytest.raises(RaInZedError):
            _fragment(_SCHEMA_INCLUSION_GENERIC_RA_SRC)

    def test_error_names_offending_line(self) -> None:
        """`Delta Stack[S join U]` sits on source line 8."""
        with pytest.raises(RaInZedError) as exc_info:
            _fragment(_SCHEMA_INCLUSION_GENERIC_RA_SRC)
        assert "line 8" in str(exc_info.value)

    def test_error_names_schema_block(self) -> None:
        with pytest.raises(RaInZedError, match="`schema` block"):
            _fragment(_SCHEMA_INCLUSION_GENERIC_RA_SRC)


class TestSchemaInclusionGenericPlainStillGeneratesCleanly:
    """A plain-Z schema-inclusion generic (`Stack[N]`) is unaffected."""

    def test_no_regression(self) -> None:
        latex = _fragment(_AXDEF_INCLUSION_GENERIC_PLAIN_SRC)
        assert r"\begin{axdef}" in latex
        assert "Stack[X]" in latex


# ---------------------------------------------------------------------------
# FreeType / SyntaxBlock constructor parameters -- completeness-sweep find.
#
# ``_generate_free_type`` wraps its output in ``\begin{zed}...\end{zed}`` and
# ``_generate_syntax_definition_branches`` (used by ``_generate_syntax_block``)
# wraps its output in ``\begin{syntax}...\end{syntax}`` -- fuzz.sty defines
# ``\syntax`` in terms of ``\@zed`` (fuzz.sty line 232), so it is type-checked
# identically.  Neither guarded a constructor's parameter expression, so a
# free-type branch referencing an RA-tainted name (e.g. an earlier
# ``RJoin == S join U`` abbreviation) rendered `RJoin` straight into the box
# -- fuzz has never seen `RJoin` declared, since it was routed to display
# math, not a zed paragraph.
# ---------------------------------------------------------------------------

_FREE_TYPE_PARAM_RA_SRC = """given T
axdef
  S : T <-> T
  U : T <-> T
end

RJoin == S join U

Tree ::= leaf<RJoin>
"""

_SYNTAX_BLOCK_PARAM_RA_SRC = """given T
axdef
  S : T <-> T
  U : T <-> T
end

RJoin == S join U

syntax
  Tree ::= leaf<RJoin>
end
"""

_FREE_TYPE_PARAM_PLAIN_SRC = "Tree ::= stalk | leaf<N> | branch<Tree x Tree>"

_SYNTAX_BLOCK_PARAM_PLAIN_SRC = """syntax
  Tree ::= stalk | leaf<N> | branch<Tree x Tree>
end
"""


class TestFreeTypeParamRaRejected:
    """An RA-tainted-by-reference free-type constructor parameter is rejected."""

    def test_raises_ra_in_zed_error(self) -> None:
        with pytest.raises(RaInZedError):
            _fragment(_FREE_TYPE_PARAM_RA_SRC)

    def test_error_names_offending_line(self) -> None:
        """`Tree ::= leaf<RJoin>` sits on source line 9."""
        with pytest.raises(RaInZedError) as exc_info:
            _fragment(_FREE_TYPE_PARAM_RA_SRC)
        assert "line 9" in str(exc_info.value)

    def test_error_names_zed_block(self) -> None:
        with pytest.raises(RaInZedError, match="`zed` block"):
            _fragment(_FREE_TYPE_PARAM_RA_SRC)


class TestSyntaxBlockParamRaRejected:
    """An RA-tainted-by-reference syntax-block constructor parameter is rejected."""

    def test_raises_ra_in_zed_error(self) -> None:
        with pytest.raises(RaInZedError):
            _fragment(_SYNTAX_BLOCK_PARAM_RA_SRC)

    def test_error_names_offending_line(self) -> None:
        """`Tree ::= leaf<RJoin>` sits on source line 10."""
        with pytest.raises(RaInZedError) as exc_info:
            _fragment(_SYNTAX_BLOCK_PARAM_RA_SRC)
        assert "line 10" in str(exc_info.value)

    def test_error_names_syntax_block(self) -> None:
        with pytest.raises(RaInZedError, match="`syntax` block"):
            _fragment(_SYNTAX_BLOCK_PARAM_RA_SRC)


class TestFreeTypeAndSyntaxBlockParamPlainStillGenerateCleanly:
    """Plain-Z constructor parameters are unaffected by the guard."""

    def test_free_type_no_regression(self) -> None:
        latex = _fragment(_FREE_TYPE_PARAM_PLAIN_SRC)
        assert r"\begin{zed}" in latex
        assert "leaf \\ldata \\nat \\rdata" in latex

    def test_syntax_block_no_regression(self) -> None:
        latex = _fragment(_SYNTAX_BLOCK_PARAM_PLAIN_SRC)
        assert r"\begin{syntax}" in latex
        assert "leaf \\ldata \\nat \\rdata" in latex


# ---------------------------------------------------------------------------
# FreeType nested inside a multi-item `zed` block -- completeness-sweep find.
#
# ``_generate_zed``'s ``Document`` branch renders a nested ``FreeType``'s own
# constructor parameters (distinct from the standalone-``FreeType`` handler
# above) via ``generate_expr`` with no RA guard at all -- reachable whenever
# a `zed` block mixes a `given` clause with a free-type definition.
# ---------------------------------------------------------------------------

_ZED_NESTED_FREE_TYPE_PARAM_RA_SRC = """given T
axdef
  S : T <-> T
  U : T <-> T
end

RJoin == S join U

zed
  given X
  Tree ::= leaf<RJoin>
end
"""

_ZED_NESTED_FREE_TYPE_PARAM_PLAIN_SRC = """zed
  given X
  Tree ::= stalk | leaf<N>
end
"""


class TestZedNestedFreeTypeParamRaRejected:
    """An RA-tainted-by-reference param in a zed-nested FreeType is rejected."""

    def test_raises_ra_in_zed_error(self) -> None:
        with pytest.raises(RaInZedError):
            _fragment(_ZED_NESTED_FREE_TYPE_PARAM_RA_SRC)

    def test_error_names_offending_line(self) -> None:
        """`Tree ::= leaf<RJoin>` sits on source line 11."""
        with pytest.raises(RaInZedError) as exc_info:
            _fragment(_ZED_NESTED_FREE_TYPE_PARAM_RA_SRC)
        assert "line 11" in str(exc_info.value)

    def test_error_names_zed_block(self) -> None:
        with pytest.raises(RaInZedError, match="`zed` block"):
            _fragment(_ZED_NESTED_FREE_TYPE_PARAM_RA_SRC)


class TestZedNestedFreeTypeParamPlainStillGeneratesCleanly:
    """A plain-Z zed-nested FreeType parameter is unaffected by the guard."""

    def test_no_regression(self) -> None:
        latex = _fragment(_ZED_NESTED_FREE_TYPE_PARAM_PLAIN_SRC)
        assert r"\begin{zed}" in latex
        assert "leaf \\ldata \\nat \\rdata" in latex


# ---------------------------------------------------------------------------
# Consolidation-path FreeType branch parameters -- PR #87 review (issue #83
# class).  ``_generate_document_items_with_consolidation`` (latex_gen.py)
# packs consecutive top-level GivenType/FreeType/Abbreviation items into one
# ``\begin{zed}`` box via ``_generate_zed_content`` (latex_gen.py) -- a
# *separate* renderer from the standalone ``_generate_free_type`` handler
# above (paragraphs.py).  Neither its SequenceLiteral branch-parameter case
# nor its plain branch-parameter case called ``_reject_ra_in_box``, so an RA
# construct or an RA-tainted-by-reference name in a *consolidated* free
# type's constructor parameters rendered straight into the box.
# ---------------------------------------------------------------------------

_CONSOLIDATED_FREE_TYPE_LITERAL_RA_SRC = """given T
Tree ::= leaf | node<<S join U>>
"""

_CONSOLIDATED_FREE_TYPE_NAME_RA_SRC = """given T
axdef
  S : T <-> T
  U : T <-> T
end

RJoin == S join U

given X
Tree ::= leaf<RJoin>
"""

_CONSOLIDATED_FREE_TYPE_PLAIN_SRC = """given T
Tree ::= leaf | node<<T x T>>
"""


class TestConsolidatedFreeTypeLiteralRaRejected:
    """A literal RA branch parameter in a consolidated free type is rejected."""

    def test_raises_ra_in_zed_error(self) -> None:
        with pytest.raises(RaInZedError):
            _fragment(_CONSOLIDATED_FREE_TYPE_LITERAL_RA_SRC)

    def test_error_names_offending_line(self) -> None:
        """`Tree ::= leaf | node<<S join U>>` sits on source line 2."""
        with pytest.raises(RaInZedError) as exc_info:
            _fragment(_CONSOLIDATED_FREE_TYPE_LITERAL_RA_SRC)
        assert "line 2" in str(exc_info.value)

    def test_error_names_zed_block(self) -> None:
        with pytest.raises(RaInZedError, match="`zed` block"):
            _fragment(_CONSOLIDATED_FREE_TYPE_LITERAL_RA_SRC)


class TestConsolidatedFreeTypeNameRaRejected:
    """An RA-tainted-by-reference param in a consolidated free type is rejected."""

    def test_raises_ra_in_zed_error(self) -> None:
        with pytest.raises(RaInZedError):
            _fragment(_CONSOLIDATED_FREE_TYPE_NAME_RA_SRC)

    def test_error_names_offending_line(self) -> None:
        """`Tree ::= leaf<RJoin>` sits on source line 10."""
        with pytest.raises(RaInZedError) as exc_info:
            _fragment(_CONSOLIDATED_FREE_TYPE_NAME_RA_SRC)
        assert "line 10" in str(exc_info.value)

    def test_error_names_zed_block(self) -> None:
        with pytest.raises(RaInZedError, match="`zed` block"):
            _fragment(_CONSOLIDATED_FREE_TYPE_NAME_RA_SRC)


class TestConsolidatedFreeTypePlainStillGeneratesCleanly:
    """A plain-Z consolidated free type still consolidates and renders cleanly."""

    def test_no_regression(self) -> None:
        latex = _fragment(_CONSOLIDATED_FREE_TYPE_PLAIN_SRC)
        assert r"\begin{zed}" in latex
        assert r"\also" in latex
        assert "node \\ldata T(x)(T) \\rdata" in latex
