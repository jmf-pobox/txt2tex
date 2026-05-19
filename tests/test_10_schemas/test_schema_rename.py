"""Tests for schema renaming S[old/new, ...] per Z RM §3.11.

Phase 3.1 — ``S[a/b, c/d]`` renames schema components.

Disambiguation from Phase 1.1 generic instantiation (``S[X]``) uses a
depth-0 scan for ``/`` before the matching ``]``.

Coverage (~15 cases):
  - AST: SchemaRename node constructed with correct schema and pairs.
  - Parser: single pair, multiple pairs, decorated schema, decorated names.
  - Disambiguation: ``S[X]`` still parses as GenericInstantiation.
  - In a defs RHS: acceptance probe ``Op2 defs Counter[count'/count]``.
  - Inside an expression: ``f(S[a/b])``.
  - Generator: round-trips to expected LaTeX strings.
  - Negative (~5): missing source, missing slash, missing target, trailing
    slash, trailing comma — all raise ParserError with message + line + column.
"""

from __future__ import annotations

import pytest

from txt2tex.ast_nodes import (
    Document,
    FunctionApp,
    GenericInstantiation,
    HorizDef,
    Identifier,
    SchemaRename,
)
from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser, ParserError

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def parse(source: str) -> Document:
    """Parse source and assert the result is a Document."""
    tokens = Lexer(source).tokenize()
    ast = Parser(tokens).parse()
    assert isinstance(ast, Document)
    return ast


def parse_expr(source: str) -> object:
    """Parse a single-expression source."""
    tokens = Lexer(source).tokenize()
    return Parser(tokens).parse()


def latex(source: str) -> str:
    """Parse source and generate LaTeX (fuzz mode)."""
    doc = parse(source)
    return LaTeXGenerator(use_fuzz=True).generate_document(doc)


def first_item(source: str) -> object:
    """Return the first document item from parsed source."""
    doc = parse(source)
    assert doc.items, "document has no items"
    return doc.items[0]


# ---------------------------------------------------------------------------
# 1. AST construction — single pair
# ---------------------------------------------------------------------------


class TestSchemaRenameAST:
    """SchemaRename AST node construction."""

    def test_single_pair_schema(self) -> None:
        """``S defs Op[a/b]`` produces SchemaRename body with one pair."""
        item = first_item("S defs Op[a/b]")
        assert isinstance(item, HorizDef)
        body = item.body
        assert isinstance(body, SchemaRename)
        assert isinstance(body.schema, Identifier)
        assert body.schema.name == "Op"
        assert body.pairs == [("a", "b")]

    def test_multiple_pairs(self) -> None:
        """``S defs Op[a/b, c/d]`` produces two rename pairs."""
        item = first_item("S defs Op[a/b, c/d]")
        assert isinstance(item, HorizDef)
        body = item.body
        assert isinstance(body, SchemaRename)
        assert body.pairs == [("a", "b"), ("c", "d")]

    def test_three_pairs(self) -> None:
        """``S defs Op[a/b, c/d, e/f]`` produces three rename pairs."""
        item = first_item("S defs Op[a/b, c/d, e/f]")
        assert isinstance(item, HorizDef)
        body = item.body
        assert isinstance(body, SchemaRename)
        assert body.pairs == [("a", "b"), ("c", "d"), ("e", "f")]

    def test_schema_ref_is_identifier(self) -> None:
        """The schema field is an Identifier node."""
        item = first_item("R defs S[x/y]")
        assert isinstance(item, HorizDef)
        assert isinstance(item.body, SchemaRename)
        assert isinstance(item.body.schema, Identifier)

    def test_node_carries_position(self) -> None:
        """SchemaRename node has non-zero line and column."""
        item = first_item("R defs S[x/y]")
        assert isinstance(item, HorizDef)
        body = item.body
        assert isinstance(body, SchemaRename)
        assert body.line >= 1
        assert body.column >= 1


# ---------------------------------------------------------------------------
# 2. Decorated schema — S'[a/b]
# ---------------------------------------------------------------------------


class TestSchemaRenameDecorated:
    """Decoration interaction: Phase-0 lexer bakes prime into identifier."""

    def test_primed_schema(self) -> None:
        """``R defs S'[a/b]`` renames the primed schema S'."""
        item = first_item("R defs S'[a/b]")
        assert isinstance(item, HorizDef)
        body = item.body
        assert isinstance(body, SchemaRename)
        assert isinstance(body.schema, Identifier)
        assert body.schema.name == "S'"
        assert body.pairs == [("a", "b")]

    def test_decorated_source_name(self) -> None:
        """``R defs S[a'/b]`` — primed source name in pair."""
        item = first_item("R defs S[a'/b]")
        assert isinstance(item, HorizDef)
        body = item.body
        assert isinstance(body, SchemaRename)
        assert body.pairs == [("a'", "b")]

    def test_decorated_target_name(self) -> None:
        """``R defs S[a/b']`` — primed target name in pair."""
        item = first_item("R defs S[a/b']")
        assert isinstance(item, HorizDef)
        body = item.body
        assert isinstance(body, SchemaRename)
        assert body.pairs == [("a", "b'")]


# ---------------------------------------------------------------------------
# 3. Disambiguation from generic instantiation
# ---------------------------------------------------------------------------


class TestSchemaRenameDisambiguation:
    """``S[X]`` must still parse as GenericInstantiation, not SchemaRename."""

    def test_generic_still_generic(self) -> None:
        """``S defs Stack[N]`` — no slash → GenericInstantiation body."""
        item = first_item("S defs Stack[N]")
        assert isinstance(item, HorizDef)
        assert isinstance(item.body, GenericInstantiation)

    def test_generic_two_params(self) -> None:
        """``S defs Map[K, V]`` — no slash → GenericInstantiation."""
        item = first_item("S defs Map[K, V]")
        assert isinstance(item, HorizDef)
        assert isinstance(item.body, GenericInstantiation)

    def test_rename_not_generic(self) -> None:
        """``S defs Op[a/b]`` — slash present → SchemaRename, not generic."""
        item = first_item("S defs Op[a/b]")
        assert isinstance(item, HorizDef)
        assert isinstance(item.body, SchemaRename)
        assert not isinstance(item.body, GenericInstantiation)


# ---------------------------------------------------------------------------
# 4. Acceptance probe — Op2 defs Counter[count'/count]
# ---------------------------------------------------------------------------


class TestSchemaRenameAcceptanceProbe:
    """Acceptance probe from the mission spec."""

    def test_acceptance_probe_ast(self) -> None:
        """``Op2 defs Counter[count'/count]`` produces correct AST."""
        source = "schema Counter\n  count : N\nend\n\nOp2 defs Counter[count'/count]"
        doc = parse(source)
        hd = doc.items[1]
        assert isinstance(hd, HorizDef)
        assert hd.name == "Op2"
        body = hd.body
        assert isinstance(body, SchemaRename)
        assert isinstance(body.schema, Identifier)
        assert body.schema.name == "Counter"
        assert body.pairs == [("count'", "count")]

    def test_acceptance_probe_latex(self) -> None:
        """``Op2 defs Counter[count'/count]`` round-trips to correct LaTeX."""
        source = "schema Counter\n  count : N\nend\n\nOp2 defs Counter[count'/count]"
        tex = latex(source)
        assert "Op2 \\defs Counter[count'/count]" in tex
        assert "\\begin{zed}" in tex
        assert "\\end{zed}" in tex


# ---------------------------------------------------------------------------
# 5. Inside an expression — f(S[a/b])
# ---------------------------------------------------------------------------


class TestSchemaRenameInExpr:
    """SchemaRename can appear inside larger expression contexts."""

    def test_in_function_arg(self) -> None:
        """``f(S[a/b])`` parses with SchemaRename as function argument."""
        # This is an expression context; parse as expr
        source = "f(S[a/b])"
        tokens = Lexer(source).tokenize()
        result = Parser(tokens).parse()
        # Result may be a Document with one Expr item or an Expr directly
        expr = result.items[0] if isinstance(result, Document) else result
        assert isinstance(expr, FunctionApp)
        assert len(expr.args) == 1
        assert isinstance(expr.args[0], SchemaRename)
        assert expr.args[0].pairs == [("a", "b")]


# ---------------------------------------------------------------------------
# 6. Generator — LaTeX output
# ---------------------------------------------------------------------------


class TestSchemaRenameGenerator:
    """LaTeX generator emits correct schema rename notation."""

    def test_single_pair_latex(self) -> None:
        """``R defs S[a/b]`` emits ``S[a/b]``."""
        tex = latex("R defs S[a/b]")
        assert "S[a/b]" in tex

    def test_multiple_pairs_latex(self) -> None:
        """``R defs S[a/b, c/d]`` emits ``S[a/b, c/d]``."""
        tex = latex("R defs S[a/b, c/d]")
        assert "S[a/b, c/d]" in tex

    def test_primed_schema_latex(self) -> None:
        """``R defs S'[a/b]`` emits ``S'[a/b]``."""
        tex = latex("R defs S'[a/b]")
        assert "S'[a/b]" in tex

    def test_decorated_source_latex(self) -> None:
        """``R defs S[a'/b]`` emits ``S[a'/b]``."""
        tex = latex("R defs S[a'/b]")
        assert "S[a'/b]" in tex

    def test_wrapped_in_defs(self) -> None:
        """SchemaRename RHS appears after ``\\defs`` in zed environment."""
        tex = latex("R defs S[a/b]")
        assert "R \\defs S[a/b]" in tex

    def test_wrapped_in_zed(self) -> None:
        """Output is wrapped in ``\\begin{zed}...\\end{zed}``."""
        tex = latex("R defs S[a/b]")
        assert "\\begin{zed}" in tex
        assert "\\end{zed}" in tex


# ---------------------------------------------------------------------------
# 7. Negative cases — all raise ParserError with message + line + column
# ---------------------------------------------------------------------------


class TestSchemaRenameNegative:
    """Malformed rename brackets raise ParserError with position."""

    def _check_error(self, source: str) -> ParserError:
        """Assert parse raises ParserError and return the exception."""
        with pytest.raises(ParserError) as exc_info:
            parse(source)
        err = exc_info.value
        assert err.message, "error message must be non-empty"
        assert err.token.line >= 1, "line must be >= 1"
        assert err.token.column >= 1, "column must be >= 1"
        return err

    def test_missing_target_raises(self) -> None:
        """``S defs Op[a/]`` — no target after slash → ParserError."""
        err = self._check_error("S defs Op[a/]")
        assert "/" in err.message or "identifier" in err.message.lower()

    def test_missing_source_raises(self) -> None:
        """``S defs Op[/b]`` — slash before any source name → ParserError."""
        err = self._check_error("S defs Op[/b]")
        assert "identifier" in err.message.lower() or "/" in err.message

    def test_trailing_slash_raises(self) -> None:
        """``S defs Op[a/b/]`` — trailing slash after pair → ParserError."""
        self._check_error("S defs Op[a/b/]")

    def test_trailing_comma_raises(self) -> None:
        """``S defs Op[a/b,]`` — trailing comma with no following pair → ParserError."""
        self._check_error("S defs Op[a/b,]")

    def test_double_slash_raises(self) -> None:
        """``S defs Op[a / b /]`` — trailing slash after complete pair → ParserError."""
        # Has a slash → detected as rename; second slash after 'b' has no target.
        self._check_error("S defs Op[a / b /]")

    def test_missing_slash_between_names_raises(self) -> None:
        """``S defs Op[a/b c/d]`` — missing comma between pairs → ParserError."""
        # After parsing pair (a, b), next is IDENTIFIER 'c', not ',' or ']'.
        err = self._check_error("S defs Op[a/b c/d]")
        msg = err.message.lower()
        assert "," in err.message or "]" in err.message or "rename" in msg

    def test_stray_slash_in_expression_raises(self) -> None:
        """Bare '/' outside rename brackets raises ParserError with clear message."""
        # Before Phase 3.1, bare '/' raised LexerError immediately.
        # Now the lexer emits SLASH but the parser must reject it in expr context.
        tokens = Lexer("a / b").tokenize()
        with pytest.raises(ParserError) as exc_info:
            Parser(tokens).parse()
        err = exc_info.value
        assert err.message, "error message must be non-empty"
        assert err.token.line >= 1
        assert err.token.column >= 1
        # Message must mention rename context so the user understands
        assert "rename" in err.message.lower() or "S[a/b]" in err.message
