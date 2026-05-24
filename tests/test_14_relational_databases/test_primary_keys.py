"""Tests for the pk declaration prefix (primary-key annotation).

pk is valid only in named schema bodies.  The parser rejects pk in axdef,
gendef, anonymous schemas, and inline schema text.

For fuzz compatibility the generator does not use \\underline{} inside the
schema box.  Instead it emits a plain-math PK statement after \\end{schema}:

    \\noindent$\\mathrm{PK}(\\mathrm{Name}) = \\{attr1, attr2\\}$

This sits outside any Z environment so fuzz ignores it; pdflatex renders it.
"""

from __future__ import annotations

import pytest

from txt2tex.ast_nodes import (
    Declaration,
    Document,
    Schema,
)
from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer, LexerError
from txt2tex.parser import Parser, ParserError
from txt2tex.tokens import Token, TokenType

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _lex(src: str) -> list[Token]:
    """Tokenize src."""
    return Lexer(src).tokenize()


def _parse(src: str) -> Document:
    """Parse src into a Document."""
    result = Parser(_lex(src)).parse()
    if isinstance(result, Document):
        return result
    return Document(items=[result], line=1, column=1)


def _fragment(src: str) -> str:
    """Generate LaTeX fragment (no preamble) from source."""
    gen = LaTeXGenerator(use_fuzz=True)
    ast = _parse(src)
    return gen.generate_fragment(ast)


# ---------------------------------------------------------------------------
# Lexer
# ---------------------------------------------------------------------------


class TestPKLexer:
    """PK token is produced correctly by the lexer."""

    def test_pk_keyword_produces_pk_token(self) -> None:
        """'pk' lexes to PK token type."""
        tokens = _lex("pk")
        assert tokens[0].type == TokenType.PK
        assert tokens[0].value == "pk"

    def test_pk_keyword_column_is_one(self) -> None:
        """PK token has correct line and column."""
        tokens = _lex("pk class : ClassName")
        tok = tokens[0]
        assert tok.line == 1
        assert tok.column == 1

    def test_pk_is_reserved_cannot_be_decorated(self) -> None:
        """pk' raises LexerError — reserved words cannot be decorated."""
        with pytest.raises(LexerError) as exc_info:
            Lexer("pk'").tokenize()
        err = exc_info.value
        assert "pk" in err.message


# ---------------------------------------------------------------------------
# Parser — AST field (schema body only)
# ---------------------------------------------------------------------------


class TestPKParser:
    """Parser sets is_primary_key=True on pk-prefixed declarations in schemas."""

    def test_single_pk_declaration(self) -> None:
        """schema S\\n  pk a : T\\nend → Declaration with is_primary_key=True."""
        doc = _parse("schema S\n  pk a : T\nend")
        schema = doc.items[0]
        assert isinstance(schema, Schema)
        assert len(schema.declarations) == 1
        decl = schema.declarations[0]
        assert isinstance(decl, Declaration)
        assert decl.variable == "a"
        assert decl.is_primary_key is True

    def test_non_pk_declaration_is_false(self) -> None:
        """Plain declaration has is_primary_key=False (default)."""
        doc = _parse("schema S\n  b : U\nend")
        schema = doc.items[0]
        assert isinstance(schema, Schema)
        decl = schema.declarations[0]
        assert isinstance(decl, Declaration)
        assert decl.is_primary_key is False

    def test_pk_and_plain_mixed(self) -> None:
        """schema with pk and plain declarations."""
        doc = _parse("schema S\n  pk a : T\n  b : U\nend")
        schema = doc.items[0]
        assert isinstance(schema, Schema)
        assert len(schema.declarations) == 2
        pk_decl = schema.declarations[0]
        plain_decl = schema.declarations[1]
        assert isinstance(pk_decl, Declaration)
        assert isinstance(plain_decl, Declaration)
        assert pk_decl.is_primary_key is True
        assert plain_decl.is_primary_key is False

    def test_composite_pk_two_lines(self) -> None:
        """Two pk lines both get is_primary_key=True."""
        src = (
            "schema CentreStaff\n  pk centreId : CentreID\n  pk staffId : PersonID\nend"
        )
        doc = _parse(src)
        schema = doc.items[0]
        assert isinstance(schema, Schema)
        assert len(schema.declarations) == 2
        for decl in schema.declarations:
            assert isinstance(decl, Declaration)
            assert decl.is_primary_key is True

    def test_pk_comma_separated(self) -> None:
        """pk a, b : T → two declarations, both is_primary_key=True."""
        doc = _parse("schema S\n  pk a, b : T\nend")
        schema = doc.items[0]
        assert isinstance(schema, Schema)
        assert len(schema.declarations) == 2
        for decl in schema.declarations:
            assert isinstance(decl, Declaration)
            assert decl.is_primary_key is True

    def test_pk_with_prime_decoration(self) -> None:
        """pk count' : N — decorated name is accepted."""
        doc = _parse("schema S\n  pk count' : N\nend")
        schema = doc.items[0]
        assert isinstance(schema, Schema)
        decl = schema.declarations[0]
        assert isinstance(decl, Declaration)
        assert decl.variable == "count'"
        assert decl.is_primary_key is True


# ---------------------------------------------------------------------------
# Generator — LaTeX emission (PK line after schema box)
# ---------------------------------------------------------------------------


class TestPKGenerator:
    """Generator emits a PK line after the schema box for pk-marked attributes."""

    def test_single_pk_produces_pk_line(self) -> None:
        r"""pk a : T → PK line after \end{schema}."""
        frag = _fragment("schema S\n  pk a : T\n  b : U\nend")
        assert r"\mathrm{PK}(\mathrm{S}) = \{a\}" in frag

    def test_plain_declaration_no_pk_line(self) -> None:
        """Schema without pk produces no PK line."""
        frag = _fragment("schema S\n  b : U\nend")
        assert r"\mathrm{PK}" not in frag

    def test_composite_pk_lists_all_attrs(self) -> None:
        r"""Two pk lines → exactly one PK line listing both attributes."""
        frag = _fragment(
            "schema CentreStaff\n  pk centreId : CentreID\n  pk staffId : PersonID\nend"
        )
        # Composite PK: one line, both attributes in the set.
        assert r"\mathrm{PK}(\mathrm{CentreStaff}) = \{centreId, staffId\}" in frag
        # Exactly one PK statement — not one per attribute.
        assert frag.count(r"\mathrm{PK}") == 1

    def test_schema_begin_has_plain_name(self) -> None:
        r"""\begin{schema}{Class} — schema title is plain (not underlined)."""
        frag = _fragment("schema Class\n  pk class : ClassName\n  type : TypeName\nend")
        assert r"\begin{schema}{Class}" in frag

    def test_pk_line_contains_only_pk_attrs(self) -> None:
        """PK set contains only pk-marked attributes, not plain ones."""
        frag = _fragment("schema S\n  pk a : T\n  b : U\nend")
        assert "b" not in frag.split(r"\mathrm{PK}")[-1].split(r"\}")[0]

    def test_pk_line_after_end_schema(self) -> None:
        r"""PK line appears after \end{schema}, not inside the box."""
        frag = _fragment("schema S\n  pk a : T\nend")
        end_pos = frag.find(r"\end{schema}")
        pk_pos = frag.find(r"\mathrm{PK}")
        assert end_pos >= 0
        assert pk_pos > end_pos

    def test_declaration_body_is_plain(self) -> None:
        r"""pk attribute inside the schema box is plain (no \underline)."""
        frag = _fragment("schema S\n  pk a : T\nend")
        assert r"\underline" not in frag

    def test_probe_a_class_schema(self) -> None:
        r"""Probe A: Class schema with pk class — PK line emitted, no \underline."""
        src = (
            "given ClassName, TypeName, CountryName\n"
            "\n"
            "schema Class\n"
            "  pk class : ClassName\n"
            "  type : TypeName\n"
            "  country : CountryName\n"
            "  numGuns : N\n"
            "  bore : N\n"
            "  displacement : N\n"
            "end"
        )
        frag = _fragment(src)
        assert r"\mathrm{PK}(\mathrm{Class}) = \{class\}" in frag
        assert r"\underline" not in frag

    def test_probe_a_ship_schema(self) -> None:
        r"""Probe A: Ship schema with pk name — PK line lists 'name' only."""
        src = (
            "given ShipName, ClassName\n"
            "\n"
            "schema Ship\n"
            "  pk name : ShipName\n"
            "  class : ClassName\n"
            "  launched : N\n"
            "end"
        )
        frag = _fragment(src)
        assert r"\mathrm{PK}(\mathrm{Ship}) = \{name\}" in frag

    def test_probe_b_composite_pk(self) -> None:
        r"""Probe B: CentreStaff with two pk attributes — both in PK line."""
        src = (
            "given CentreID, PersonID\n"
            "\n"
            "schema CentreStaff\n"
            "  pk centreId : CentreID\n"
            "  pk staffId : PersonID\n"
            "end"
        )
        frag = _fragment(src)
        assert r"\mathrm{PK}(\mathrm{CentreStaff}) = \{centreId, staffId\}" in frag

    def test_probe_d_pk_fk_as_z_predicates(self) -> None:
        """Probe D: PK/FK as standard Z predicates parse without error."""
        src = "given ClassName\n\naxdef\n  PK : P ClassName\nwhere\n  PK = {class}\nend"
        frag = _fragment(src)
        assert "PK" in frag

    def test_two_schemas_each_get_own_pk_line(self) -> None:
        """Two pk-annotated schemas each get their own PK line."""
        src = "schema A\n  pk x : N\nend\nschema B\n  pk y : N\nend"
        frag = _fragment(src)
        assert r"\mathrm{PK}(\mathrm{A}) = \{x\}" in frag
        assert r"\mathrm{PK}(\mathrm{B}) = \{y\}" in frag


# ---------------------------------------------------------------------------
# Negative cases — invalid pk positions
# ---------------------------------------------------------------------------


class TestPKNegative:
    """pk in invalid positions raises ParserError with position info."""

    def test_pk_before_delta_rejected(self) -> None:
        """pk Delta S raises ParserError — no attribute name to underline."""
        with pytest.raises(ParserError) as exc_info:
            Parser(_lex("schema Op\n  pk Delta S\nend")).parse()
        err = exc_info.value
        assert "Delta" in err.message or "pk" in err.message
        assert err.token.line >= 1

    def test_pk_before_xi_rejected(self) -> None:
        """pk Xi S raises ParserError — no attribute name to underline."""
        with pytest.raises(ParserError) as exc_info:
            Parser(_lex("schema Op\n  pk Xi S\nend")).parse()
        err = exc_info.value
        assert "Xi" in err.message or "pk" in err.message
        assert err.token.line >= 1

    def test_pk_alone_raises(self) -> None:
        """pk followed by newline (no declaration) raises ParserError."""
        with pytest.raises(ParserError):
            Parser(_lex("schema S\n  pk\nend")).parse()

    def test_pk_no_type_annotation_raises(self) -> None:
        """pk name without colon raises ParserError."""
        with pytest.raises(ParserError):
            Parser(_lex("schema S\n  pk noType\nend")).parse()

    def test_pk_leading_comma_raises(self) -> None:
        """pk ,b : T raises ParserError — no attribute name before comma."""
        with pytest.raises(ParserError):
            Parser(_lex("schema S\n  pk ,b : T\nend")).parse()

    def test_pk_trailing_comma_raises(self) -> None:
        """pk a, : T raises ParserError — trailing comma with no second name."""
        with pytest.raises(ParserError):
            Parser(_lex("schema S\n  pk a, : T\nend")).parse()

    def test_pk_double_comma_raises(self) -> None:
        """pk a,,b : T raises ParserError — double comma."""
        with pytest.raises(ParserError):
            Parser(_lex("schema S\n  pk a,,b : T\nend")).parse()

    def test_pk_in_axdef_raises(self) -> None:
        """pk inside axdef raises ParserError — pk is schema-only."""
        with pytest.raises(ParserError) as exc_info:
            Parser(_lex("axdef\n  pk key : N\nend")).parse()
        err = exc_info.value
        assert "schema" in err.message.lower() or "axdef" in err.message.lower()

    def test_pk_in_gendef_raises(self) -> None:
        """pk inside gendef raises ParserError — pk is schema-only."""
        with pytest.raises(ParserError) as exc_info:
            Parser(_lex("gendef [X]\n  pk key : X\nend")).parse()
        err = exc_info.value
        assert "schema" in err.message.lower() or "gendef" in err.message.lower()

    def test_pk_in_anonymous_schema_raises(self) -> None:
        """pk inside anonymous schema raises ParserError — no name for PK line."""
        with pytest.raises(ParserError) as exc_info:
            Parser(_lex("schema\n  pk a : T\nend")).parse()
        err = exc_info.value
        assert "anonymous" in err.message.lower() or "named" in err.message.lower()

    def test_pk_in_schema_text_raises(self) -> None:
        """pk inside inline schema text raises ParserError — anonymous context."""
        with pytest.raises(ParserError) as exc_info:
            Parser(_lex("S defs [ pk a : T ]")).parse()
        err = exc_info.value
        assert "anonymous" in err.message.lower() or "named" in err.message.lower()
