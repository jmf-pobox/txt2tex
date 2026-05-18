"""Tests for the θ-expression (theta keyword) per Z RM §3.10.

Phase 1.2 — theta S constructs the binding whose components are the
in-scope variables matching schema S's signature.

Coverage (~12 cases):
- Atomic: theta S round-trips to \\theta S
- Decorated: theta S' round-trips to \\theta S'
- Equation: theta S = theta S'
- In a set literal: { theta S, theta T }
- In a maplet (acceptance probe context): bookingId? |-> theta Booking'
- Negative: theta alone raises ParserError (message + line + column)
- Negative: theta' raises LexerError (Phase 0 RESERVED_WORDS guard)
- Regression: existing schemas without theta produce identical output
- In schema-as-predicate position (where clause)
- Inside a quantifier body
- Inside a set comprehension expression
- Full acceptance probe: AddBooking with theta Booking'
"""

from __future__ import annotations

import pytest

from txt2tex.ast_nodes import (
    BinaryOp,
    Document,
    Expr,
    FunctionApp,
    Identifier,
    Schema,
    SchemaInclusion,
    SetLiteral,
    Theta,
)
from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer, LexerError
from txt2tex.parser import Parser, ParserError
from txt2tex.tokens import TokenType

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def parse(source: str) -> Document:
    """Parse source, assert the result is a Document, and return it."""
    tokens = Lexer(source).tokenize()
    ast = Parser(tokens).parse()
    assert isinstance(ast, Document)
    return ast


def parse_expr(source: str) -> object:
    """Parse source and return the raw AST (may be Expr or Document)."""
    tokens = Lexer(source).tokenize()
    return Parser(tokens).parse()


def latex(source: str) -> str:
    """Parse source and generate LaTeX (fuzz mode).

    Accepts single-expression inputs (which parse to an Expr, not a Document)
    as well as full document inputs.
    """
    tokens = Lexer(source).tokenize()
    ast = Parser(tokens).parse()
    return LaTeXGenerator(use_fuzz=True).generate_document(ast)


# ---------------------------------------------------------------------------
# 1. Token / lexer: theta becomes a keyword
# ---------------------------------------------------------------------------


class TestThetaTokenisation:
    """theta must lex as THETA, not IDENTIFIER."""

    def test_theta_keyword_recognized(self) -> None:
        """theta lexes as THETA token."""
        tokens = Lexer("theta S").tokenize()
        types = [t.type for t in tokens]
        assert TokenType.THETA in types

    def test_theta_not_identifier(self) -> None:
        """theta is not an IDENTIFIER token."""
        tokens = Lexer("theta S").tokenize()
        theta_tokens = [t for t in tokens if t.value == "theta"]
        assert len(theta_tokens) == 1
        assert theta_tokens[0].type == TokenType.THETA

    def test_theta_prime_raises_lexer_error(self) -> None:
        """theta' is forbidden: Phase 0 RESERVED_WORDS guard fires.

        The lexer emits the error at the position of the decoration character.
        """
        with pytest.raises(LexerError) as exc_info:
            Lexer("theta' S").tokenize()
        err = exc_info.value
        assert "theta" in err.message
        assert err.line == 1


# ---------------------------------------------------------------------------
# 2. AST: Theta node structure
# ---------------------------------------------------------------------------


class TestThetaAST:
    """Parser produces Theta nodes with correct structure."""

    def test_theta_atom_produces_theta_node(self) -> None:
        """theta S in expression context produces Theta(expr=Identifier('S'))."""
        ast = parse_expr("theta S")
        assert isinstance(ast, Theta)
        assert isinstance(ast.expr, Identifier)
        assert ast.expr.name == "S"

    def test_theta_decorated_schema_ref(self) -> None:
        """theta S' produces Theta(expr=Identifier(\"S'\"))."""
        ast = parse_expr("theta S'")
        assert isinstance(ast, Theta)
        assert isinstance(ast.expr, Identifier)
        assert ast.expr.name == "S'"

    def test_theta_carries_source_position(self) -> None:
        """Theta node line/column track the theta keyword, not the schema name."""
        ast = parse_expr("theta Booking")
        assert isinstance(ast, Theta)
        assert ast.line == 1
        assert ast.column == 1

    def test_theta_equation(self) -> None:
        """theta S = theta S' parses as BinaryOp('=', Theta, Theta)."""
        ast = parse_expr("theta S = theta S'")
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "="
        assert isinstance(ast.left, Theta)
        assert isinstance(ast.right, Theta)
        assert isinstance(ast.right.expr, Identifier)
        assert ast.right.expr.name == "S'"

    def test_theta_no_schema_eof_raises_parser_error(self) -> None:
        """theta at end-of-input raises ParserError with end-of-input message."""
        with pytest.raises(ParserError) as exc_info:
            Parser(Lexer("theta").tokenize()).parse()
        err = exc_info.value
        assert "end of input" in err.message
        assert "theta" in err.message
        assert err.token.line == 1

    def test_theta_followed_by_number_raises(self) -> None:
        """theta 5 — number is not a valid schema name; token value in message."""
        with pytest.raises(ParserError) as exc_info:
            Parser(Lexer("theta 5").tokenize()).parse()
        err = exc_info.value
        assert "Expected schema name after theta" in err.message
        assert "NUMBER" in err.message
        assert "'5'" in err.message  # value included in (value) form
        assert err.token.line == 1
        assert err.token.column == 7  # column of '5'

    def test_theta_followed_by_keyword_raises(self) -> None:
        """theta where — keyword is not a valid schema name; token value in message."""
        source = "schema S\n  x : N\nwhere\n  theta where\nend"
        with pytest.raises(ParserError) as exc_info:
            Parser(Lexer(source).tokenize()).parse()
        err = exc_info.value
        assert "Expected schema name after theta" in err.message
        assert "WHERE" in err.message
        assert "'where'" in err.message  # value included in (value) form

    def test_theta_followed_by_newline_then_end_raises(self) -> None:
        """theta on its own line inside where clause raises ParserError.

        Guards against the newline-skip-then-consume-end silent regression:
        the parser must not skip the newline and consume 'end' as the schema ref.
        """
        source = "schema S\n  x : N\nwhere\n  theta\nend"
        with pytest.raises(ParserError) as exc_info:
            Parser(Lexer(source).tokenize()).parse()
        err = exc_info.value
        # Message must mention theta and either missing schema name or end of input
        assert "theta" in err.message
        assert ("schema name" in err.message) or ("end of input" in err.message)
        # The offending token is the NEWLINE on line 4 (after theta) —
        # the parser catches it before consuming 'end' on line 5.
        assert err.token.line == 4


# ---------------------------------------------------------------------------
# 3. LaTeX generation
# ---------------------------------------------------------------------------


class TestThetaLatex:
    r"""Generator emits \theta SchemaRef correctly."""

    def test_atomic_theta_emits_theta_macro(self) -> None:
        r"""theta S round-trips to \theta S."""
        out = latex("theta S")
        assert r"\theta S" in out

    def test_decorated_theta_emits_primed_ref(self) -> None:
        r"""theta S' round-trips to \theta S'."""
        out = latex("theta S'")
        assert r"\theta S'" in out

    def test_theta_in_set_literal(self) -> None:
        r"""{ theta S, theta T } round-trips with both \theta calls."""
        out = latex("{ theta S, theta T }")
        assert r"\theta S" in out
        assert r"\theta T" in out

    def test_theta_in_maplet(self) -> None:
        r"""bookingId? |-> theta Booking' emits \mapsto \theta Booking'."""
        out = latex("bookingId? |-> theta Booking'")
        assert r"\theta Booking'" in out
        assert r"\mapsto" in out

    def test_theta_in_where_clause(self) -> None:
        r"""theta in a where clause emits \theta inside \where block."""
        source = "schema S\n  x : N\nwhere\n  x = theta T\nend"
        out = latex(source)
        assert r"\theta T" in out
        assert r"\where" in out

    def test_theta_in_quantifier_body(self) -> None:
        r"""forall S : seq Booking | theta S emits \forall with \theta."""
        out = latex("forall S : seq Booking | theta S")
        assert r"\theta S" in out
        assert r"\forall" in out

    def test_theta_in_set_comprehension_expression(self) -> None:
        r"""{ s : Stack | s = theta t . theta s } emits \theta in expression."""
        out = latex("{ s : Stack | s = theta t . theta s }")
        assert r"\theta" in out

    def test_theta_equation_latex(self) -> None:
        r"""theta S = theta S' emits = with both \theta S and \theta S'."""
        out = latex("theta S = theta S'")
        assert r"\theta S" in out
        assert r"\theta S'" in out


# ---------------------------------------------------------------------------
# 4. Acceptance probe: AddBooking with theta Booking'
# ---------------------------------------------------------------------------


class TestAddBookingAcceptanceProbe:
    """Full Phase 0 + 1.1 + 1.2 acceptance probe per mission spec."""

    _source = (
        "schema AddBooking\n"
        "  Delta Airline\n"
        "  bookingId? : BookingId\n"
        "  Booking\n"
        "where\n"
        "  bookings' = bookings oplus { bookingId? |-> theta Booking' }\n"
        "end"
    )

    def test_schema_structure_parses(self) -> None:
        """AddBooking schema parses without error."""
        doc = parse(self._source)
        assert len(doc.items) == 1
        schema = doc.items[0]
        assert isinstance(schema, Schema)
        assert schema.name == "AddBooking"

    def test_delta_inclusion_present(self) -> None:
        """Delta Airline inclusion is in the declaration list."""
        doc = parse(self._source)
        schema = doc.items[0]
        assert isinstance(schema, Schema)
        delta_incls = [
            d
            for d in schema.declarations
            if isinstance(d, SchemaInclusion) and d.decoration == "delta"
        ]
        assert len(delta_incls) == 1
        assert delta_incls[0].name == "Airline"

    def test_bare_inclusion_booking_present(self) -> None:
        """Bare Booking inclusion is in the declaration list."""
        doc = parse(self._source)
        schema = doc.items[0]
        assert isinstance(schema, Schema)
        bare_incls = [
            d
            for d in schema.declarations
            if isinstance(d, SchemaInclusion) and d.decoration is None
        ]
        assert len(bare_incls) == 1
        assert bare_incls[0].name == "Booking"

    def test_theta_in_predicate(self) -> None:
        """theta Booking' appears in the where-clause predicate tree."""
        doc = parse(self._source)
        schema = doc.items[0]
        assert isinstance(schema, Schema)
        # Collect all AST nodes in the predicate groups
        theta_nodes = _find_theta_nodes(schema.predicates)
        assert len(theta_nodes) >= 1
        assert isinstance(theta_nodes[0].expr, Identifier)
        assert theta_nodes[0].expr.name == "Booking'"

    def test_latex_output_contains_required_macros(self) -> None:
        r"""Generated LaTeX contains \Delta, bookingId?, \theta Booking'."""
        out = latex(self._source)
        assert r"\begin{schema}{AddBooking}" in out
        assert r"\Delta Airline" in out
        assert "bookingId?" in out
        assert "Booking" in out
        assert r"\where" in out
        assert r"\theta Booking'" in out
        assert r"\end{schema}" in out


# ---------------------------------------------------------------------------
# 5. Regression: existing schemas without theta are unchanged
# ---------------------------------------------------------------------------


class TestRegressionNoTheta:
    """Schemas that do not use theta must produce identical LaTeX output."""

    def test_simple_schema_unchanged(self) -> None:
        """Schema with only typed declarations is unaffected."""
        source = "schema Counter\n  count : N\nwhere\n  count >= 0\nend"
        out = latex(source)
        assert r"\begin{schema}{Counter}" in out
        assert r"\where" in out
        assert r"\end{schema}" in out
        # No theta in output
        assert r"\theta" not in out

    def test_delta_xi_schema_unchanged(self) -> None:
        """Delta/Xi schema without theta is unaffected."""
        source = "schema ReadCard\n  Xi Card\n  result! : N\nwhere\n  result! = 1\nend"
        out = latex(source)
        assert r"\Xi Card" in out
        assert r"\theta" not in out


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _find_theta_nodes(predicate_groups: list[list[Expr]]) -> list[Theta]:
    """Recursively collect Theta nodes from predicate groups."""
    result: list[Theta] = []
    for group in predicate_groups:
        for pred in group:
            result.extend(_walk_theta(pred))
    return result


def _walk_theta(node: object) -> list[Theta]:
    """Walk an expression tree and return all Theta nodes."""
    if isinstance(node, Theta):
        return [node, *_walk_theta(node.expr)]
    if isinstance(node, BinaryOp):
        return [*_walk_theta(node.left), *_walk_theta(node.right)]
    if isinstance(node, FunctionApp):
        result = [*_walk_theta(node.function)]
        for arg in node.args:
            result.extend(_walk_theta(arg))
        return result
    if isinstance(node, SetLiteral):
        result2: list[Theta] = []
        for elem in node.elements:
            result2.extend(_walk_theta(elem))
        return result2
    return []
