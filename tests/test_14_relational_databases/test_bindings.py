"""Tests for Z binding brackets (Phase 2.3 — Z RM §3.7).

Covers lexer tokens (LBIND, RBIND), the Binding AST node, parser dispatch
at expression-atom level, and LaTeX generation with ``\\lblot ... \\rblot``.

Negative cases follow the three-assertion pattern: message + line + column.

Acceptance probes at the end verify relational-calculus queries.
"""

from __future__ import annotations

import pytest

from txt2tex.ast_nodes import (
    Binding,
    Document,
    Expr,
    Identifier,
    RelationalImage,
    SetComprehension,
    TupleProjection,
)
from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser, ParserError
from txt2tex.tokens import Token, TokenType

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _lex(src: str) -> list[Token]:
    """Tokenize src."""
    return Lexer(src).tokenize()


def _parse_expr(src: str) -> Expr:
    """Parse a single expression from src."""
    result = Parser(_lex(src)).parse()
    if isinstance(result, Document):
        item = result.items[0]
        assert isinstance(
            item,
            (
                Binding,
                SetComprehension,
                Identifier,
                TupleProjection,
            ),
        )
        return item
    return result


def _expr_latex(src: str) -> str:
    """Generate LaTeX for a single expression."""
    gen = LaTeXGenerator(use_fuzz=True)
    result = Parser(_lex(src)).parse()
    item: Expr = result.items[0] if isinstance(result, Document) else result  # type: ignore[assignment]
    return gen.generate_expr(item)


# ---------------------------------------------------------------------------
# Lexer: LBIND and RBIND tokens
# ---------------------------------------------------------------------------


class TestBindingLexer:
    """LBIND and RBIND two-char tokens tokenize correctly."""

    def test_lbind_token(self) -> None:
        """{| lexes to LBIND."""
        tokens = _lex("{|")
        assert tokens[0].type == TokenType.LBIND
        assert tokens[0].value == "{|"

    def test_rbind_token(self) -> None:
        """|} inside an open {| lexes to RBIND."""
        # |} alone (no open {|) falls through to PIPE + RBRACE.
        # Inside a balanced {| ... |} the closing |} is RBIND.
        tokens = _lex("{| a == 1 |}")
        rbind = next(t for t in tokens if t.value == "|}")
        assert rbind.type == TokenType.RBIND

    def test_rbind_alone_is_pipe_then_rbrace(self) -> None:
        """|} with no open {| lexes as PIPE then RBRACE, not RBIND."""
        tokens = _lex("|}")
        assert tokens[0].type == TokenType.PIPE
        assert tokens[0].value == "|"
        assert tokens[1].type == TokenType.RBRACE
        assert tokens[1].value == "}"

    def test_lbind_position(self) -> None:
        """{| token records correct line and column."""
        tokens = _lex("{| a |}")
        tok = tokens[0]
        assert tok.line == 1
        assert tok.column == 1

    def test_lbind_does_not_eat_bare_lbrace(self) -> None:
        """Bare { still produces LBRACE, not LBIND."""
        tokens = _lex("{ a }")
        assert tokens[0].type == TokenType.LBRACE

    def test_rbind_does_not_eat_bare_pipe(self) -> None:
        """Bare | still produces PIPE, not RBIND."""
        tokens = _lex("x | y")
        pipe = next(t for t in tokens if t.value == "|")
        assert pipe.type == TokenType.PIPE

    def test_lbind_distinct_from_limg(self) -> None:
        """(| produces LIMG, not LBIND."""
        tokens = _lex("(|")
        assert tokens[0].type == TokenType.LIMG

    def test_rbind_distinct_from_rimg(self) -> None:
        """|) produces RIMG, not RBIND."""
        tokens = _lex("|)")
        assert tokens[0].type == TokenType.RIMG

    def test_lbind_before_maplet_chain(self) -> None:
        """Inside {| ... |}, |-> still produces MAPLET."""
        tokens = _lex("{| a == x |-> y |}")
        types = [t.type for t in tokens]
        assert TokenType.LBIND in types
        assert TokenType.MAPLET in types
        assert TokenType.RBIND in types

    def test_rbind_distinct_from_rres(self) -> None:
        """|> produces RRES, not RBIND."""
        tokens = _lex("|>")
        assert tokens[0].type == TokenType.RRES

    def test_rbind_distinct_from_nrres(self) -> None:
        """|>> produces NRRES, not RBIND."""
        tokens = _lex("|>>")
        assert tokens[0].type == TokenType.NRRES


# ---------------------------------------------------------------------------
# Parser — positive cases
# ---------------------------------------------------------------------------


class TestBindingParserPositive:
    """Parser builds correct Binding AST nodes for valid binding literals."""

    def test_single_component(self) -> None:
        """{| name == x |} → Binding with one pair."""
        node = _parse_expr("{| name == x |}")
        assert isinstance(node, Binding)
        assert len(node.pairs) == 1
        label, value = node.pairs[0]
        assert label == "name"
        assert isinstance(value, Identifier)
        assert value.name == "x"

    def test_two_components(self) -> None:
        """{| a == 1, b == 2 |} → Binding with two pairs."""
        node = _parse_expr("{| a == 1, b == 2 |}")
        assert isinstance(node, Binding)
        assert len(node.pairs) == 2
        assert node.pairs[0][0] == "a"
        assert node.pairs[1][0] == "b"

    def test_three_components(self) -> None:
        """{| a == 1, b == 2, c == 3 |} → Binding with three pairs."""
        node = _parse_expr("{| a == 1, b == 2, c == 3 |}")
        assert isinstance(node, Binding)
        assert len(node.pairs) == 3
        labels = [p[0] for p in node.pairs]
        assert labels == ["a", "b", "c"]

    def test_empty_binding(self) -> None:
        """{| |} → Binding with no pairs (Z RM permits it)."""
        node = _parse_expr("{| |}")
        assert isinstance(node, Binding)
        assert node.pairs == []

    def test_field_projection_as_value(self) -> None:
        """{| name == s.name |} has TupleProjection as value."""
        node = _parse_expr("{| name == s.name |}")
        assert isinstance(node, Binding)
        _, value = node.pairs[0]
        assert isinstance(value, TupleProjection)
        assert isinstance(value.base, Identifier)
        assert value.base.name == "s"
        assert value.index == "name"

    def test_binding_position_recorded(self) -> None:
        """Binding node records the line and column of {|."""
        node = _parse_expr("{| a == 1 |}")
        assert isinstance(node, Binding)
        assert node.line == 1
        assert node.column == 1

    def test_decorated_value(self) -> None:
        """{| name == s.name', x == y? |} parses correctly."""
        node = _parse_expr("{| name == s.name', x == y? |}")
        assert isinstance(node, Binding)
        assert len(node.pairs) == 2

    def test_multiline_binding(self) -> None:
        """Binding spanning two lines parses correctly."""
        src = "{| name == s.name,\n  displacement == c.displacement |}"
        node = _parse_expr(src)
        assert isinstance(node, Binding)
        assert len(node.pairs) == 2


# ---------------------------------------------------------------------------
# Parser — binding inside larger expressions
# ---------------------------------------------------------------------------


class TestBindingInContext:
    """Binding literals work correctly in set comprehensions and quantifiers."""

    def test_binding_in_set_comprehension(self) -> None:
        """{ s : Ship | s.launched < 1921 . {| name == s.name |} } parses."""
        src = "{ s : Ship | s.launched < 1921 . {| name == s.name |} }"
        node = _parse_expr(src)
        assert isinstance(node, SetComprehension)
        assert isinstance(node.expression, Binding)
        assert node.expression.pairs[0][0] == "name"

    def test_binding_in_quantifier_body(self) -> None:
        """forall s : Ship | {| name == s.name |} parses (binding as body)."""
        src = "forall s : Ship | {| name == s.name |}"
        result = Parser(_lex(src)).parse()
        # Parse succeeds without error
        assert result is not None


# ---------------------------------------------------------------------------
# Generator — LaTeX output
# ---------------------------------------------------------------------------


class TestBindingGenerator:
    """Generator emits correct \\lblot ... \\rblot LaTeX."""

    def test_single_component_latex(self) -> None:
        r"""{| name == x |} → \lblot name == x \rblot."""
        out = _expr_latex("{| name == x |}")
        assert out == r"\lblot name == x \rblot"

    def test_two_components_latex(self) -> None:
        r"""{| a == 1, b == 2 |} → \lblot a == 1, b == 2 \rblot."""
        out = _expr_latex("{| a == 1, b == 2 |}")
        assert out == r"\lblot a == 1, b == 2 \rblot"

    def test_three_components_latex(self) -> None:
        r"""{| a == 1, b == 2, c == 3 |} → \lblot a == 1, b == 2, c == 3 \rblot."""
        out = _expr_latex("{| a == 1, b == 2, c == 3 |}")
        assert out == r"\lblot a == 1, b == 2, c == 3 \rblot"

    def test_empty_binding_latex(self) -> None:
        r"""{| |} → \lblot \rblot."""
        out = _expr_latex("{| |}")
        assert out == r"\lblot \rblot"

    def test_identifier_in_value(self) -> None:
        r"""{| r == Ship |} → \lblot r == Ship \rblot (no wrapping)."""
        out = _expr_latex("{| r == Ship |}")
        assert out == r"\lblot r == Ship \rblot"

    def test_identifier_label(self) -> None:
        r"""{| Ship == x |} → \lblot Ship == x \rblot (label passes through)."""
        out = _expr_latex("{| Ship == x |}")
        assert out == r"\lblot Ship == x \rblot"

    def test_field_projection_value_latex(self) -> None:
        r"""{| name == s.name |} → \lblot name == s.name \rblot."""
        out = _expr_latex("{| name == s.name |}")
        assert out == r"\lblot name == s.name \rblot"

    def test_decorated_value_latex(self) -> None:
        r"""{| x == y' |} emits the prime decoration."""
        out = _expr_latex("{| x == y' |}")
        assert r"y'" in out


# ---------------------------------------------------------------------------
# Generator — acceptance probes (relational-calculus style)
# ---------------------------------------------------------------------------


class TestBindingAcceptanceProbes:
    """Full relational-calculus query round-trips per mission acceptance criteria."""

    def test_q2a_single_component(self) -> None:
        r"""Q2(a): single-component binding in set comprehension.

        { s : Ship | s.launched < 1921 . {| name == s.name |} }
        must render the comprehension body as \lblot name == s.name \rblot.
        """
        src = "{ s : Ship | s.launched < 1921 . {| name == s.name |} }"
        out = _expr_latex(src)
        assert r"\lblot" in out
        assert r"\rblot" in out
        assert "name == " in out
        assert "Ship" in out

    def test_q2d_multi_component(self) -> None:
        r"""Q2(d): multi-component binding in multi-variable comprehension.

        { s : Ship; c : Class | s.class = c.class .
          {| name == s.name, displacement == c.displacement,
             numGuns == c.numGuns |}
        }
        Must produce well-formed LaTeX with all three labels and comma
        separators.
        """
        src = (
            "{ s : Ship; c : Class | s.class = c.class .\n"
            "  {| name == s.name, displacement == c.displacement,"
            " numGuns == c.numGuns |}\n"
            "}"
        )
        out = _expr_latex(src)
        assert r"\lblot" in out
        assert r"\rblot" in out
        assert "name ==" in out
        assert "displacement ==" in out
        assert "numGuns ==" in out
        # Comma separators (not semicolons) between components
        assert ", " in out
        assert ";" not in out.split(r"\lblot")[1].split(r"\rblot")[0]


# ---------------------------------------------------------------------------
# Negative cases — three-assertion pattern (message + line + column)
# ---------------------------------------------------------------------------


class TestBindingNegative:
    """Invalid binding syntax raises ParserError with message + line + column."""

    def test_missing_equals_equals(self) -> None:
        """{| a |} raises at the RBIND token (col 6): missing == after label."""
        # Position: {|(1-2) (3)a(4) (5)|} starts at col 6
        with pytest.raises(ParserError) as exc_info:
            Parser(_lex("{| a |}")).parse()
        err = exc_info.value
        assert "==" in err.message
        assert err.token.line == 1
        assert err.token.column == 6

    def test_missing_label(self) -> None:
        """{| == e |} raises at the ABBREV token (col 4): == with no label."""
        # Position: {|(1-2) (3)==(4-5) — error reported at col 4
        with pytest.raises(ParserError) as exc_info:
            Parser(_lex("{| == e |}")).parse()
        err = exc_info.value
        assert "label" in err.message.lower() or "==" in err.message
        assert err.token.line == 1
        assert err.token.column == 4

    def test_missing_value(self) -> None:
        """{| a == |} raises at the RBIND token (col 9): value expected after ==."""
        # Position: {|(1-2) (3)a(4) (5)==(6-7) (8)|}(9-10) — error at col 9
        with pytest.raises(ParserError) as exc_info:
            Parser(_lex("{| a == |}")).parse()
        err = exc_info.value
        assert "expression" in err.message.lower() or "==" in err.message
        assert err.token.line == 1
        assert err.token.column == 9

    def test_unclosed_binding(self) -> None:
        """{| a == 1 raises at EOF (col 10): missing closing |}."""
        # Position: {|(1-2) (3)a(4) (5)==(6-7) (8)1(9) EOF at col 10
        with pytest.raises(ParserError) as exc_info:
            Parser(_lex("{| a == 1")).parse()
        err = exc_info.value
        assert "|}" in err.message or "unclosed" in err.message.lower()
        assert err.token.line == 1
        assert err.token.column == 10

    def test_semicolon_between_components(self) -> None:
        """{| a == 1; b == 2 |} raises at the SEMICOLON (col 10): commas only."""
        # Position: {|(1-2) (3)a(4) (5)==(6-7) (8)1(9);(10)
        with pytest.raises(ParserError) as exc_info:
            Parser(_lex("{| a == 1; b == 2 |}")).parse()
        err = exc_info.value
        assert "comma" in err.message.lower() or "semicolon" in err.message.lower()
        assert err.token.line == 1
        assert err.token.column == 10


# ---------------------------------------------------------------------------
# Regression: existing nested sequence syntax still works
# ---------------------------------------------------------------------------


class TestBindingRegression:
    """Phase 0 nested sequence <<a, b>> is unaffected by Phase 2.3 changes."""

    def test_nested_sequence_still_works(self) -> None:
        """<<a, b>> parses as nested sequence, not binding."""
        src = "<<a, b>>"
        result = Parser(_lex(src)).parse()
        assert result is not None

    def test_relational_image_still_works(self) -> None:
        """R(| S |) parses as RelationalImage, not Binding."""
        src = "R(| S |)"
        result = Parser(_lex(src)).parse()
        item = result.items[0] if isinstance(result, Document) else result
        assert isinstance(item, RelationalImage)

    def test_set_comprehension_with_pipe_still_works(self) -> None:
        """{ x : N | x > 0 } still produces SetComprehension."""
        src = "{ x : N | x > 0 }"
        result = Parser(_lex(src)).parse()
        item = result.items[0] if isinstance(result, Document) else result
        assert isinstance(item, SetComprehension)

    def test_adjacent_pipe_brace_outside_binding_is_pipe_then_rbrace(self) -> None:
        """{ x : N | x > 0|} with no open {| lexes as PIPE then RBRACE, not RBIND.

        This is the FIX 1 regression: the lexer must track bind_depth and only
        emit RBIND when there is an open {| on the stack.
        """
        tokens = _lex("{ x : N | x > 0|}")
        types = [t.type for t in tokens]
        # RBIND must not appear — there is no open {|
        assert TokenType.RBIND not in types
        # The trailing |} falls through to two separate tokens: PIPE and RBRACE.
        # There are two PIPE tokens total: the comprehension | and the stray |.
        pipe_count = sum(1 for t in tokens if t.type == TokenType.PIPE)
        assert pipe_count == 2
        # RBRACE must be present (from the stray })
        assert TokenType.RBRACE in types

    def test_bind_depth_resets_after_close(self) -> None:
        """After {| |} closes, a subsequent |} is not RBIND."""
        # Two bindings in sequence; the second |} must not leak depth
        tokens = _lex("{| a == 1 |} |}")
        # Only the first |} (inside the open {|) should be RBIND
        rbind_count = sum(1 for t in tokens if t.type == TokenType.RBIND)
        assert rbind_count == 1

    def test_chained_field_projection_in_binding(self) -> None:
        """{| a == x.f.g |} — RBIND in safe_followers handles chained projections."""
        node = _parse_expr("{| a == x.f.g |}")
        assert isinstance(node, Binding)
        label, value = node.pairs[0]
        assert label == "a"
        # x.f.g → TupleProjection(TupleProjection(x, "f"), "g")
        assert isinstance(value, TupleProjection)
        assert value.index == "g"
        inner = value.base
        assert isinstance(inner, TupleProjection)
        assert inner.index == "f"
        assert isinstance(inner.base, Identifier)
        assert inner.base.name == "x"
