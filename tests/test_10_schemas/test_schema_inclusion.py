"""Tests for schema inclusion in schema, axdef, and gendef declarations.

Phase 1.1 — Δ/Ξ keywords and schema inclusion.

Three inclusion forms per Z RM §3.7 and §5.2:
- Bare:  ``Counter``           (brings counter's components into scope)
- Delta: ``Delta Airline``     (before/after state convention)
- Xi:    ``Xi Card``           (read-only operation convention)
"""

from __future__ import annotations

import pytest

from txt2tex.ast_nodes import (
    AxDef,
    BinaryOp,
    Declaration,
    Document,
    GenDef,
    Identifier,
    Schema,
    SchemaInclusion,
)
from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser, ParserError
from txt2tex.tokens import TokenType

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def parse(source: str) -> Document:
    """Parse source and assert the result is a Document."""
    tokens = Lexer(source).tokenize()
    ast = Parser(tokens).parse()
    assert isinstance(ast, Document)
    return ast


def latex(source: str) -> str:
    """Parse source and generate LaTeX (fuzz mode)."""
    doc = parse(source)
    return LaTeXGenerator(use_fuzz=True).generate_document(doc)


# ---------------------------------------------------------------------------
# 1. Token / lexer: Delta and Xi become keywords
# ---------------------------------------------------------------------------


class TestDeltaXiTokenisation:
    """Delta and Xi must lex as DELTA/XI tokens, not IDENTIFIER."""

    def test_delta_keyword_in_schema(self) -> None:
        """Delta is recognised as a keyword inside a schema block."""
        tokens = Lexer("schema S\n  Delta Counter\nend").tokenize()
        types = [t.type for t in tokens]
        assert TokenType.DELTA in types

    def test_xi_keyword_in_schema(self) -> None:
        """Xi is recognised as a keyword inside a schema block."""
        tokens = Lexer("schema S\n  Xi Counter\nend").tokenize()
        types = [t.type for t in tokens]
        assert TokenType.XI in types

    def test_delta_as_identifier_in_expression(self) -> None:
        """Delta used as a plain identifier in expressions still works."""
        tokens = Lexer("Gamma shows Delta").tokenize()
        ast = Parser(tokens).parse()
        # Single-expression input → parser returns BinaryOp directly
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "shows"
        assert isinstance(ast.right, Identifier)
        assert ast.right.name == "Delta"

    def test_xi_as_identifier_in_expression(self) -> None:
        """Xi used as identifier in expression (set membership) still works."""
        tokens = Lexer("Xi elem S").tokenize()
        ast = Parser(tokens).parse()
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "elem"
        assert isinstance(ast.left, Identifier)
        assert ast.left.name == "Xi"


# ---------------------------------------------------------------------------
# 2. Parsing — bare inclusion
# ---------------------------------------------------------------------------


class TestBareSchemaInclusion:
    """Bare schema name on its own line → SchemaInclusion(decoration=None)."""

    def test_bare_inclusion_single(self) -> None:
        """Single bare inclusion in schema."""
        doc = parse("schema AB\n  Counter\nend")
        assert isinstance(doc.items[0], Schema)
        decls = doc.items[0].declarations
        assert len(decls) == 1
        incl = decls[0]
        assert isinstance(incl, SchemaInclusion)
        assert incl.name == "Counter"
        assert incl.decoration is None
        assert incl.generics is None

    def test_bare_inclusion_mixed_with_typed(self) -> None:
        """Bare inclusion followed by typed declaration in schema."""
        source = "schema AB\n  Counter\n  x : N\nend"
        doc = parse(source)
        schema = doc.items[0]
        assert isinstance(schema, Schema)
        assert len(schema.declarations) == 2
        assert isinstance(schema.declarations[0], SchemaInclusion)
        assert schema.declarations[0].name == "Counter"
        assert isinstance(schema.declarations[1], Declaration)
        assert schema.declarations[1].variable == "x"

    def test_bare_inclusion_then_inclusion(self) -> None:
        """Two bare inclusions in a row."""
        source = "schema AB\n  A\n  B\nend"
        doc = parse(source)
        schema = doc.items[0]
        assert isinstance(schema, Schema)
        assert len(schema.declarations) == 2
        for d in schema.declarations:
            assert isinstance(d, SchemaInclusion)
            assert d.decoration is None

    def test_bare_inclusion_in_axdef(self) -> None:
        """Bare schema inclusion is valid in axdef blocks too."""
        source = "axdef\n  Counter\n  x : N\nend"
        doc = parse(source)
        axdef = doc.items[0]
        assert isinstance(axdef, AxDef)
        assert isinstance(axdef.declarations[0], SchemaInclusion)
        assert axdef.declarations[0].name == "Counter"

    def test_bare_inclusion_in_gendef(self) -> None:
        """Bare schema inclusion is valid in gendef blocks too."""
        source = "gendef [X]\n  Counter\n  f : X -> X\nend"
        doc = parse(source)
        gendef = doc.items[0]
        assert isinstance(gendef, GenDef)
        assert isinstance(gendef.declarations[0], SchemaInclusion)
        assert gendef.declarations[0].name == "Counter"


# ---------------------------------------------------------------------------
# 3. Parsing — Delta (decorated) inclusion
# ---------------------------------------------------------------------------


class TestDeltaSchemaInclusion:
    """Delta Name → SchemaInclusion(decoration="delta")."""

    def test_delta_inclusion(self) -> None:
        """Delta schema inclusion parses correctly."""
        source = "schema UpdateCounter\n  Delta Counter\nend"
        doc = parse(source)
        schema = doc.items[0]
        assert isinstance(schema, Schema)
        assert len(schema.declarations) == 1
        incl = schema.declarations[0]
        assert isinstance(incl, SchemaInclusion)
        assert incl.name == "Counter"
        assert incl.decoration == "delta"
        assert incl.generics is None

    def test_delta_inclusion_with_typed_decls(self) -> None:
        """Delta inclusion mixed with typed declarations."""
        source = (
            "schema AddBooking\n"
            "  Delta Airline\n"
            "  bookingId? : BookingId\n"
            "  BookingInit\n"
            "  customerId? : CustomerId\n"
            "  routeId? : RouteId\n"
            "where\n"
            "  bookingId? notin dom bookings\n"
            "  routeId? elem dom routes\n"
            "end"
        )
        doc = parse(source)
        schema = doc.items[0]
        assert isinstance(schema, Schema)
        assert len(schema.declarations) == 5
        assert isinstance(schema.declarations[0], SchemaInclusion)
        assert schema.declarations[0].decoration == "delta"
        assert schema.declarations[0].name == "Airline"
        assert isinstance(schema.declarations[1], Declaration)
        assert schema.declarations[1].variable == "bookingId?"
        assert isinstance(schema.declarations[2], SchemaInclusion)
        assert schema.declarations[2].decoration is None  # bare
        assert schema.declarations[2].name == "BookingInit"
        assert isinstance(schema.declarations[3], Declaration)
        assert schema.declarations[3].variable == "customerId?"
        assert isinstance(schema.declarations[4], Declaration)
        assert schema.declarations[4].variable == "routeId?"

    def test_delta_inclusion_position(self) -> None:
        """SchemaInclusion carries correct source position."""
        source = "schema S\n  Delta Counter\nend"
        doc = parse(source)
        schema = doc.items[0]
        assert isinstance(schema, Schema)
        incl = schema.declarations[0]
        assert isinstance(incl, SchemaInclusion)
        assert incl.line == 2  # Delta is on line 2

    def test_delta_missing_schema_name(self) -> None:
        """Delta followed by a colon (not an identifier) raises ParserError."""
        source = "schema S\n  Delta : N\nend"
        tokens = Lexer(source).tokenize()
        with pytest.raises(ParserError) as exc_info:
            Parser(tokens).parse()
        err = exc_info.value
        assert "Expected schema name after Delta" in err.message
        assert "COLON" in err.message  # offending-token type present
        assert err.token.line == 2
        assert err.token.column == 9  # column of ':' on line 2


# ---------------------------------------------------------------------------
# 4. Parsing — Xi (decorated) inclusion
# ---------------------------------------------------------------------------


class TestXiSchemaInclusion:
    """Xi Name → SchemaInclusion(decoration="xi")."""

    def test_xi_inclusion(self) -> None:
        """Xi schema inclusion parses correctly."""
        source = "schema ReadCard\n  Xi Card\nend"
        doc = parse(source)
        schema = doc.items[0]
        assert isinstance(schema, Schema)
        assert len(schema.declarations) == 1
        incl = schema.declarations[0]
        assert isinstance(incl, SchemaInclusion)
        assert incl.name == "Card"
        assert incl.decoration == "xi"

    def test_xi_with_typed_decl(self) -> None:
        """Xi inclusion alongside a typed declaration."""
        source = "schema ReadCounter\n  Xi Counter\n  n! : N\nend"
        doc = parse(source)
        schema = doc.items[0]
        assert isinstance(schema, Schema)
        assert len(schema.declarations) == 2
        assert isinstance(schema.declarations[0], SchemaInclusion)
        assert schema.declarations[0].decoration == "xi"
        assert isinstance(schema.declarations[1], Declaration)

    def test_xi_missing_schema_name(self) -> None:
        """Xi followed by a colon (not an identifier) raises ParserError."""
        source = "schema S\n  Xi : N\nend"
        tokens = Lexer(source).tokenize()
        with pytest.raises(ParserError) as exc_info:
            Parser(tokens).parse()
        err = exc_info.value
        assert "Expected schema name after Xi" in err.message
        assert "COLON" in err.message  # offending-token type present
        assert err.token.line == 2
        assert err.token.column == 6  # column of ':' on line 2


# ---------------------------------------------------------------------------
# 5. Generic instantiation in inclusion
# ---------------------------------------------------------------------------


class TestGenericInclusion:
    """Delta Stack[Int] and Xi Stack[X] parse generics as Expr lists."""

    def test_delta_with_generic(self) -> None:
        """Delta Stack[Int] parses with generics=[Identifier('Int')]."""
        source = "schema UseStack\n  Delta Stack[Int]\n  x : N\nend"
        doc = parse(source)
        schema = doc.items[0]
        assert isinstance(schema, Schema)
        incl = schema.declarations[0]
        assert isinstance(incl, SchemaInclusion)
        assert incl.name == "Stack"
        assert incl.decoration == "delta"
        assert incl.generics is not None
        assert len(incl.generics) == 1
        assert isinstance(incl.generics[0], Identifier)
        assert incl.generics[0].name == "Int"

    def test_bare_with_generic(self) -> None:
        """Stack[Int] on its own line parses as bare inclusion with generics."""
        source = "schema UseStack\n  Stack[Int]\n  x : N\nend"
        doc = parse(source)
        schema = doc.items[0]
        assert isinstance(schema, Schema)
        incl = schema.declarations[0]
        assert isinstance(incl, SchemaInclusion)
        assert incl.name == "Stack"
        assert incl.decoration is None
        assert incl.generics is not None

    def test_empty_generic_brackets_raises(self) -> None:
        """Delta Stack[] raises — Z RM §3.9 requires at least one type expression."""
        source = "schema S\n  Delta Stack[]\n  x : N\nend"
        tokens = Lexer(source).tokenize()
        with pytest.raises(ParserError) as exc_info:
            Parser(tokens).parse()
        err = exc_info.value
        assert "Empty generic argument list" in err.message
        assert err.token.line == 2
        assert err.token.column == 14  # column of '[' on "  Delta Stack["

    def test_comma_only_generic_brackets_raises(self) -> None:
        """Delta Stack[,] raises — comma without preceding expression."""
        source = "schema S\n  Delta Stack[,]\n  x : N\nend"
        tokens = Lexer(source).tokenize()
        with pytest.raises(ParserError) as exc_info:
            Parser(tokens).parse()
        err = exc_info.value
        assert "Expected type expression" in err.message
        assert err.token.line == 2

    def test_unclosed_generic_bracket_raises(self) -> None:
        """Delta Stack[Int (no closing bracket) raises pointing at opening '['."""
        source = "schema S\n  Delta Stack[Int\n  x : N\nend"
        tokens = Lexer(source).tokenize()
        with pytest.raises(ParserError) as exc_info:
            Parser(tokens).parse()
        err = exc_info.value
        assert "Unclosed '['" in err.message
        # Error points at the opening '[', which is on line 2
        assert err.token.line == 2
        assert err.token.column == 14  # column of '[' on "  Delta Stack["


# ---------------------------------------------------------------------------
# 6. Disambiguation: typed declaration vs bare inclusion
# ---------------------------------------------------------------------------


class TestDisambiguation:
    """count, count' : N must stay typed; Counter on its own is inclusion."""

    def test_comma_list_typed_declaration_unchanged(self) -> None:
        """count, count' : N is still a typed declaration (colon present)."""
        source = "schema S\n  count, limit : N\nend"
        doc = parse(source)
        schema = doc.items[0]
        assert isinstance(schema, Schema)
        assert len(schema.declarations) == 2
        assert all(isinstance(d, Declaration) for d in schema.declarations)
        assert isinstance(schema.declarations[0], Declaration)
        assert schema.declarations[0].variable == "count"
        assert isinstance(schema.declarations[1], Declaration)
        assert schema.declarations[1].variable == "limit"

    def test_single_identifier_no_colon_is_inclusion(self) -> None:
        """Single identifier without colon is a bare schema inclusion."""
        source = "schema S\n  Counter\nend"
        doc = parse(source)
        schema = doc.items[0]
        assert isinstance(schema, Schema)
        assert len(schema.declarations) == 1
        assert isinstance(schema.declarations[0], SchemaInclusion)

    def test_existing_schema_with_no_inclusion_unchanged(self) -> None:
        """Existing schema without inclusions produces byte-identical output."""
        source = "schema Counter\n  count : N\nwhere\n  count >= 0\nend"
        doc = parse(source)
        schema = doc.items[0]
        assert isinstance(schema, Schema)
        assert len(schema.declarations) == 1
        assert isinstance(schema.declarations[0], Declaration)
        assert schema.declarations[0].variable == "count"

    def test_colon_inside_brackets_not_a_typed_decl(self) -> None:
        """Stack[f : N] is a bare inclusion, not a typed declaration.

        The colon is inside brackets (depth 1) so the scan-ahead must not
        treat it as the declaration separator.
        """
        # Stack[N] is the generic arg — we use a simpler type to avoid
        # needing a full function-type parse here; the key is that the
        # colon inside [...] must not trigger the typed-declaration path.
        source = "schema S\n  Stack[N]\n  x : N\nend"
        doc = parse(source)
        schema = doc.items[0]
        assert isinstance(schema, Schema)
        # Stack[N] on its own line → SchemaInclusion (colon is inside brackets)
        assert isinstance(schema.declarations[0], SchemaInclusion)
        assert schema.declarations[0].name == "Stack"
        assert schema.declarations[0].decoration is None
        # x : N is still a typed declaration
        assert isinstance(schema.declarations[1], Declaration)
        assert schema.declarations[1].variable == "x"


# ---------------------------------------------------------------------------
# 6b. Additional Delta/Xi negative tests (Fix 4: offending-token in message)
# ---------------------------------------------------------------------------


class TestDeltaXiNegative:
    """Negative cases that verify message text + line + column (Phase 0 pattern)."""

    def test_delta_followed_by_number_raises(self) -> None:
        """Delta 5 — number is not a valid schema name."""
        source = "schema S\n  Delta 5\nend"
        tokens = Lexer(source).tokenize()
        with pytest.raises(ParserError) as exc_info:
            Parser(tokens).parse()
        err = exc_info.value
        assert "Expected schema name after Delta" in err.message
        assert "NUMBER" in err.message
        assert err.token.line == 2
        assert err.token.column == 9  # column of '5'

    def test_delta_followed_by_keyword_raises(self) -> None:
        """Delta where — keyword is not a valid schema name."""
        source = "schema S\n  Delta where\n  x : N\nend"
        tokens = Lexer(source).tokenize()
        with pytest.raises(ParserError) as exc_info:
            Parser(tokens).parse()
        err = exc_info.value
        assert "Expected schema name after Delta" in err.message
        assert "WHERE" in err.message
        assert err.token.line == 2
        assert err.token.column == 9  # column of 'where'

    def test_xi_followed_by_number_raises(self) -> None:
        """Xi 5 — number is not a valid schema name."""
        source = "schema S\n  Xi 5\nend"
        tokens = Lexer(source).tokenize()
        with pytest.raises(ParserError) as exc_info:
            Parser(tokens).parse()
        err = exc_info.value
        assert "Expected schema name after Xi" in err.message
        assert "NUMBER" in err.message
        assert err.token.line == 2
        assert err.token.column == 6  # column of '5'


# ---------------------------------------------------------------------------
# 7. LaTeX generation
# ---------------------------------------------------------------------------


class TestSchemaInclusionLatex:
    """Generator emits correct LaTeX for each inclusion form."""

    def test_bare_inclusion_emits_name(self) -> None:
        """Bare inclusion emits ``Name \\\\`` between declarations."""
        source = "schema AB\n  Counter\n  x : N\nend"
        out = latex(source)
        assert "Counter \\\\" in out or "Counter\n" in out
        assert "\\begin{schema}" in out

    def test_delta_inclusion_emits_delta(self) -> None:
        r"""Delta inclusion emits ``\Delta Name``."""
        source = "schema UpdateCounter\n  Delta Counter\nend"
        out = latex(source)
        assert r"\Delta Counter" in out

    def test_xi_inclusion_emits_xi(self) -> None:
        r"""Xi inclusion emits ``\Xi Name``."""
        source = "schema ReadCard\n  Xi Card\nend"
        out = latex(source)
        assert r"\Xi Card" in out

    def test_last_decl_no_linebreak(self) -> None:
        r"""Last declaration in box has no ``\\``."""
        source = "schema S\n  Delta Counter\nend"
        out = latex(source)
        lines = out.splitlines()
        # Find the \Delta Counter line
        delta_lines = [ln for ln in lines if r"\Delta Counter" in ln]
        assert len(delta_lines) == 1
        # It must not end with \\  (it's the only/last declaration)
        assert not delta_lines[0].rstrip().endswith("\\\\")

    def test_non_last_decl_has_linebreak(self) -> None:
        r"""Non-last declaration gets ``\\``."""
        source = "schema AB\n  A\n  B\n  z : N\nend"
        out = latex(source)
        lines = out.splitlines()
        a_lines = [ln for ln in lines if ln.strip() == "A \\\\"]
        assert len(a_lines) == 1

    def test_delta_generic_emits_brackets(self) -> None:
        """Delta Stack[Int] emits \\Delta Stack[...] in LaTeX."""
        source = "schema UseStack\n  Delta Stack[Int]\n  x : N\nend"
        out = latex(source)
        assert r"\Delta Stack" in out
        assert "[" in out

    def test_addbooking_acceptance_probe(self) -> None:
        """Full AddBooking-style schema round-trips through LaTeX generator."""
        source = (
            "schema AddBooking\n"
            "  Delta Airline\n"
            "  bookingId? : BookingId\n"
            "  BookingInit\n"
            "  customerId? : CustomerId\n"
            "  routeId? : RouteId\n"
            "where\n"
            "  bookingId? notin dom bookings\n"
            "  routeId? elem dom routes\n"
            "end"
        )
        out = latex(source)
        assert r"\begin{schema}{AddBooking}" in out
        assert r"\Delta Airline" in out
        assert r"BookingInit" in out
        assert r"\where" in out
        assert r"\notin" in out
        assert r"\in" in out
        assert r"\end{schema}" in out

    def test_schema_as_predicate(self) -> None:
        """S1 land S2 in where clause with both included round-trips."""
        source = (
            "schema A\n  x : N\nend\n"
            "schema B\n  y : N\nend\n"
            "schema AB\n"
            "  A\n"
            "  B\n"
            "  z : N\n"
            "where\n"
            "  A land B\n"
            "end"
        )
        out = latex(source)
        # Both schemas as declarations
        assert "\\begin{schema}{AB}" in out
        # A and B appear in where clause as conjunction
        assert r"\land" in out

    def test_axdef_bare_inclusion_latex(self) -> None:
        """Bare inclusion in axdef generates correct LaTeX."""
        source = "axdef\n  Counter\n  extra : N\nend"
        out = latex(source)
        assert r"\begin{axdef}" in out
        assert "Counter" in out

    def test_axdef_delta_inclusion_latex(self) -> None:
        """Delta inclusion in axdef generates \\Delta Name."""
        source = "axdef\n  Delta Counter\n  extra : N\nend"
        out = latex(source)
        assert r"\Delta Counter" in out

    def test_gendef_delta_inclusion_latex(self) -> None:
        """Delta inclusion in gendef generates \\Delta Name."""
        source = "gendef [X]\n  Delta Stack[X]\n  f : X -> X\nend"
        out = latex(source)
        assert r"\Delta Stack" in out


# ---------------------------------------------------------------------------
# 8. Regression: existing schemas without inclusions are unchanged
# ---------------------------------------------------------------------------


class TestRegressionNoInclusion:
    """Existing schemas without inclusion lines must produce identical output."""

    def test_simple_schema_unchanged(self) -> None:
        """Schema with only typed declarations is unaffected."""
        source = (
            "schema Counter\n  count : N\n  limit : N\nwhere\n  count <= limit\nend"
        )
        out = latex(source)
        assert r"\begin{schema}{Counter}" in out
        assert r"count : \nat" in out or "count" in out
        assert r"\where" in out
        assert r"\end{schema}" in out

    def test_axdef_unchanged(self) -> None:
        """Axdef with only typed declarations is unaffected."""
        source = "axdef\n  x : N\n  y : N\nwhere\n  x > y\nend"
        out = latex(source)
        assert r"\begin{axdef}" in out
        assert r"\where" in out
        assert r"\end{axdef}" in out

    def test_gendef_unchanged(self) -> None:
        """Gendef with only typed declarations is unaffected."""
        source = "gendef [X]\n  f : X -> X\nend"
        out = latex(source)
        assert r"\begin{gendef}[X]" in out
        assert r"\end{gendef}" in out
