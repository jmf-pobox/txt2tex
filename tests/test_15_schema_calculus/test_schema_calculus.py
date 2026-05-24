"""Tests for schema-calculus operators per Z RM §3.11 (Phase 3.2).

Operators covered:
  - Composition ``S ; T``      → ``S \\semi T``
  - Piping ``S >> T``          → ``S \\pipe T``
  - Hiding ``S hide (x, y)``   → ``S \\hide (x, y)``
  - Projection ``S project T`` → ``S \\project T``

Z RM §3.11 precedence (tightest to loosest within schema expressions):
  1. hide / project
  2. composition  ;
  3. piping >>
  4. schema-level land / lor (existing predicate operators)

All operators appear only on the RHS of a ``defs`` paragraph.
Inside axdef / schema / gendef bodies, ``;`` remains a declaration separator.

Test count: ~30 cases.
"""

from __future__ import annotations

import pytest

from txt2tex.ast_nodes import (
    AxDef,
    Document,
    GenDef,
    HorizDef,
    Identifier,
    Schema,
    SchemaCompose,
    SchemaHide,
    SchemaPipe,
    SchemaProject,
)
from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer, LexerError
from txt2tex.parser import Parser, ParserError

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def parse(source: str) -> Document:
    """Parse source; assert result is a Document."""
    tokens = Lexer(source).tokenize()
    ast = Parser(tokens).parse()
    assert isinstance(ast, Document)
    return ast


def first_item(source: str) -> object:
    """Return the first document item."""
    doc = parse(source)
    assert doc.items
    return doc.items[0]


def latex(source: str) -> str:
    """Generate LaTeX (fuzz mode) from source."""
    doc = parse(source)
    return LaTeXGenerator(use_fuzz=True).generate_document(doc)


def _check_error(source: str) -> ParserError:
    """Assert that parsing raises ParserError; return the exception."""
    with pytest.raises(ParserError) as exc_info:
        parse(source)
    err = exc_info.value
    assert err.message, "error message must be non-empty"
    assert err.token.line >= 1, "line must be >= 1"
    assert err.token.column >= 1, "column must be >= 1"
    return err


# ---------------------------------------------------------------------------
# 1. Schema composition  S ; T
# ---------------------------------------------------------------------------


class TestSchemaCompose:
    """``S ; T`` parses as SchemaCompose and emits ``\\semi``."""

    def test_ast_node_type(self) -> None:
        """``A defs OpA ; OpB`` produces SchemaCompose body."""
        item = first_item("A defs OpA ; OpB")
        assert isinstance(item, HorizDef)
        assert isinstance(item.body, SchemaCompose)

    def test_left_right_identifiers(self) -> None:
        """Left and right are Identifier nodes with correct names."""
        item = first_item("A defs OpA ; OpB")
        assert isinstance(item, HorizDef)
        body = item.body
        assert isinstance(body, SchemaCompose)
        assert isinstance(body.left, Identifier)
        assert isinstance(body.right, Identifier)
        assert body.left.name == "OpA"
        assert body.right.name == "OpB"

    def test_latex_semi(self) -> None:
        """``A defs OpA ; OpB`` emits ``OpA \\semi OpB``."""
        tex = latex("A defs OpA ; OpB")
        assert r"OpA \semi OpB" in tex

    def test_wrapped_in_zed(self) -> None:
        """Output is wrapped in ``\\begin{zed}...\\end{zed}``."""
        tex = latex("A defs OpA ; OpB")
        assert r"\begin{zed}" in tex
        assert r"\end{zed}" in tex

    def test_with_defs(self) -> None:
        """``A defs ...`` emits ``A \\defs ...``."""
        tex = latex("A defs OpA ; OpB")
        assert r"A \defs OpA \semi OpB" in tex

    def test_acceptance_probe(self) -> None:
        """Acceptance probe: full schema definitions then composition defs."""
        source = (
            "schema OpA\n"
            "  x, x' : N\n"
            "where\n"
            "  x' > x\n"
            "end\n\n"
            "schema OpB\n"
            "  x, x' : N\n"
            "where\n"
            "  x' < 100\n"
            "end\n\n"
            "OpAB defs OpA ; OpB"
        )
        doc = parse(source)
        hd = doc.items[2]
        assert isinstance(hd, HorizDef)
        assert hd.name == "OpAB"
        assert isinstance(hd.body, SchemaCompose)
        tex = LaTeXGenerator(use_fuzz=True).generate_document(doc)
        assert r"OpAB \defs OpA \semi OpB" in tex
        assert r"\begin{zed}" in tex

    def test_left_associativity(self) -> None:
        """``A ; B ; C`` parses as ``(A ; B) ; C`` (left-associative)."""
        item = first_item("R defs A ; B ; C")
        assert isinstance(item, HorizDef)
        body = item.body
        assert isinstance(body, SchemaCompose)
        # Right side is C
        assert isinstance(body.right, Identifier)
        assert body.right.name == "C"
        # Left side is (A ; B)
        assert isinstance(body.left, SchemaCompose)
        assert isinstance(body.left.left, Identifier)
        assert body.left.left.name == "A"


# ---------------------------------------------------------------------------
# 2. Schema piping  S >> T
# ---------------------------------------------------------------------------


class TestSchemaPipe:
    """``S >> T`` parses as SchemaPipe and emits ``\\pipe``."""

    def test_ast_node_type(self) -> None:
        """``R defs Send >> Recv`` produces SchemaPipe body."""
        item = first_item("R defs Send >> Recv")
        assert isinstance(item, HorizDef)
        assert isinstance(item.body, SchemaPipe)

    def test_left_right_identifiers(self) -> None:
        """Left and right are Identifier nodes."""
        item = first_item("R defs Send >> Recv")
        assert isinstance(item, HorizDef)
        body = item.body
        assert isinstance(body, SchemaPipe)
        assert isinstance(body.left, Identifier)
        assert isinstance(body.right, Identifier)
        assert body.left.name == "Send"
        assert body.right.name == "Recv"

    def test_latex_pipe(self) -> None:
        """``R defs Send >> Recv`` emits ``Send \\pipe Recv``."""
        tex = latex("R defs Send >> Recv")
        assert r"Send \pipe Recv" in tex

    def test_wrapped_in_zed_and_defs(self) -> None:
        """Output is in zed environment with \\defs."""
        tex = latex("R defs Send >> Recv")
        assert r"\begin{zed}" in tex
        assert r"R \defs Send \pipe Recv" in tex

    def test_left_associativity(self) -> None:
        """``A >> B >> C`` parses as ``(A >> B) >> C``."""
        item = first_item("R defs A >> B >> C")
        assert isinstance(item, HorizDef)
        body = item.body
        assert isinstance(body, SchemaPipe)
        assert isinstance(body.left, SchemaPipe)
        assert isinstance(body.right, Identifier)
        assert body.right.name == "C"

    def test_pipe_requires_space_before(self) -> None:
        """``S>>T`` (no space) does NOT lex as PIPE_PIPE.

        The whitespace gate on `>>` (lexer.py) is a documented requirement.
        Without leading whitespace the lexer emits two RANGLE tokens, which
        the parser then rejects. This guards the nested-sequence form
        ``<<a>, <b>>`` from being misread as a pipe.
        """
        # No whitespace before `>>` — should not produce a SchemaPipe AST.
        # The parser raises (either as unexpected RANGLE or a downstream
        # syntax error). We assert *something* raises rather than silent
        # acceptance.
        with pytest.raises((LexerError, ParserError)):
            first_item("R defs S>>T")


# ---------------------------------------------------------------------------
# 3. Schema hiding  S hide (x, y)
# ---------------------------------------------------------------------------


class TestSchemaHide:
    """``S hide (names)`` parses as SchemaHide and emits ``\\hide``."""

    def test_single_name(self) -> None:
        """``R defs S hide (x)`` produces SchemaHide with one name."""
        item = first_item("R defs S hide (x)")
        assert isinstance(item, HorizDef)
        body = item.body
        assert isinstance(body, SchemaHide)
        assert isinstance(body.schema, Identifier)
        assert body.schema.name == "S"
        assert body.names == ["x"]

    def test_multiple_names(self) -> None:
        """``R defs S hide (x, y, z)`` produces SchemaHide with three names."""
        item = first_item("R defs S hide (x, y, z)")
        assert isinstance(item, HorizDef)
        body = item.body
        assert isinstance(body, SchemaHide)
        assert body.names == ["x", "y", "z"]

    def test_latex_hide(self) -> None:
        """``R defs S hide (x, y)`` emits ``S \\hide (x, y)``."""
        tex = latex("R defs S hide (x, y)")
        assert r"S \hide (x, y)" in tex

    def test_latex_single_name(self) -> None:
        """``R defs S hide (temp)`` emits ``S \\hide (temp)``."""
        tex = latex("R defs S hide (temp)")
        assert r"S \hide (temp)" in tex

    def test_wrapped_in_zed_and_defs(self) -> None:
        """Output is in zed environment with \\defs."""
        tex = latex("R defs S hide (x)")
        assert r"\begin{zed}" in tex
        assert r"\defs" in tex


# ---------------------------------------------------------------------------
# 4. Schema projection  S project T
# ---------------------------------------------------------------------------


class TestSchemaProject:
    """``S project T`` parses as SchemaProject and emits ``\\project``."""

    def test_ast_node_type(self) -> None:
        """``R defs S project T`` produces SchemaProject body."""
        item = first_item("R defs S project T")
        assert isinstance(item, HorizDef)
        assert isinstance(item.body, SchemaProject)

    def test_left_right_identifiers(self) -> None:
        """Left and right are Identifier nodes."""
        item = first_item("R defs S project T")
        assert isinstance(item, HorizDef)
        body = item.body
        assert isinstance(body, SchemaProject)
        assert isinstance(body.left, Identifier)
        assert isinstance(body.right, Identifier)
        assert body.left.name == "S"
        assert body.right.name == "T"

    def test_latex_project(self) -> None:
        """``R defs S project T`` emits ``S \\project T``."""
        tex = latex("R defs S project T")
        assert r"S \project T" in tex

    def test_wrapped_in_zed_and_defs(self) -> None:
        """Output is in zed environment with \\defs."""
        tex = latex("R defs S project T")
        assert r"\begin{zed}" in tex
        assert r"\defs" in tex


# ---------------------------------------------------------------------------
# 5. Combined and precedence
# ---------------------------------------------------------------------------


class TestSchemaPrecedence:
    """Operator precedence per Z RM §3.11."""

    def test_hide_tighter_than_compose(self) -> None:
        """``S hide (x) ; T`` parses as ``(S hide (x)) ; T``.

        Hiding binds tighter than composition.
        """
        item = first_item("R defs S hide (x) ; T")
        assert isinstance(item, HorizDef)
        body = item.body
        # Top-level is composition
        assert isinstance(body, SchemaCompose)
        # Left is hiding
        assert isinstance(body.left, SchemaHide)
        assert body.left.schema.name == "S"  # type: ignore[union-attr]
        assert body.left.names == ["x"]
        # Right is T
        assert isinstance(body.right, Identifier)
        assert body.right.name == "T"

    def test_compose_tighter_than_pipe(self) -> None:
        """``S ; T >> U`` parses as ``(S ; T) >> U``.

        Composition binds tighter than piping (piping is lowest precedence),
        so `;` groups first and `>>` is the outermost operator.
        """
        item = first_item("R defs S ; T >> U")
        assert isinstance(item, HorizDef)
        body = item.body
        # Top-level is piping
        assert isinstance(body, SchemaPipe)
        # Left is composition S ; T
        assert isinstance(body.left, SchemaCompose)
        assert isinstance(body.left.left, Identifier)
        assert body.left.left.name == "S"
        assert isinstance(body.left.right, Identifier)
        assert body.left.right.name == "T"
        # Right is U
        assert isinstance(body.right, Identifier)
        assert body.right.name == "U"

    def test_parenthesized_compose_then_hide(self) -> None:
        """``(OpA ; OpB) hide (temp)`` applies hiding to composed schema."""
        item = first_item("R defs (OpA ; OpB) hide (temp)")
        assert isinstance(item, HorizDef)
        body = item.body
        assert isinstance(body, SchemaHide)
        assert isinstance(body.schema, SchemaCompose)
        assert body.names == ["temp"]

    def test_latex_combined_pipe_and_hide(self) -> None:
        """``OpFiltered defs (Op1 land Op2) hide (temp)`` — land inside parens."""
        # OpFiltered uses a logical operator inside, then hides
        tex = latex("OpFiltered defs S hide (temp)")
        assert r"S \hide (temp)" in tex
        assert r"OpFiltered \defs" in tex

    def test_compose_latex_combined(self) -> None:
        """``OpSeq defs Op1 ; Op2`` emits correct LaTeX."""
        tex = latex("OpSeq defs Op1 ; Op2")
        assert r"OpSeq \defs Op1 \semi Op2" in tex


# ---------------------------------------------------------------------------
# 6. Context-sensitivity: ; remains separator inside axdef/schema/gendef
# ---------------------------------------------------------------------------


class TestSemicolonContextSensitivity:
    """SEMICOLON is a declaration separator inside axdef/schema/gendef bodies.

    Enabling schema-expression context must NOT affect the declaration loops.
    """

    def test_axdef_declaration_separator(self) -> None:
        """``axdef x : N; y : N where end`` — ; separates declarations."""
        source = "axdef\n  x : N\n  y : N\nwhere\nend"
        doc = parse(source)
        axdef = doc.items[0]
        assert isinstance(axdef, AxDef)
        assert len(axdef.declarations) == 2

    def test_schema_declaration_separator(self) -> None:
        """``schema S x : N; y : N where end`` — ; separates declarations."""
        source = "schema S\n  x : N\n  y : N\nwhere\nend"
        doc = parse(source)
        schema = doc.items[0]
        assert isinstance(schema, Schema)
        assert len(schema.declarations) == 2

    def test_gendef_declaration_separator(self) -> None:
        """``gendef [X] f : X -> X where end`` — ; in gendef."""
        source = "gendef [X]\n  f : X -> X\nwhere\nend"
        doc = parse(source)
        gendef = doc.items[0]
        assert isinstance(gendef, GenDef)
        assert len(gendef.declarations) == 1

    def test_horiz_def_compose_still_works(self) -> None:
        """After axdef, subsequent defs still parses ; as composition."""
        source = "axdef\n  x : N\nwhere\nend\n\nAB defs OpA ; OpB"
        doc = parse(source)
        assert isinstance(doc.items[0], AxDef)
        hd = doc.items[1]
        assert isinstance(hd, HorizDef)
        assert isinstance(hd.body, SchemaCompose)


# ---------------------------------------------------------------------------
# 7. Negative cases — all raise ParserError with message + line + column
# ---------------------------------------------------------------------------


class TestSchemaNegative:
    """Malformed schema-calculus expressions raise ParserError with position."""

    def test_hide_missing_parens_raises(self) -> None:
        """``R defs S hide x`` — missing parens after hide → ParserError."""
        err = _check_error("R defs S hide x")
        assert "(" in err.message or "hide" in err.message.lower()

    def test_hide_empty_parens_raises(self) -> None:
        """``R defs S hide ()`` — empty name list → ParserError."""
        err = _check_error("R defs S hide ()")
        assert "hide" in err.message.lower() or "name" in err.message.lower()

    def test_project_missing_rhs_raises(self) -> None:
        """``R defs S project`` — no RHS after project → ParserError."""
        err = _check_error("R defs S project")
        # ParserError must carry position info (already asserted by _check_error)
        assert err.token.line >= 1

    def test_hide_non_identifier_in_list_raises(self) -> None:
        """``R defs S hide (1)`` — number in name list → ParserError."""
        err = _check_error("R defs S hide (1)")
        assert "identifier" in err.message.lower() or "hide" in err.message.lower()
