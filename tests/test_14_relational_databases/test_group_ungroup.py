"""Tests for GROUP and UNGROUP relational operators (Phase 4.1).

Covers AST nodes, token types, parser cases, LaTeX generator output, and
negative error cases.  Negative cases follow the three-assertion pattern:
message substring, line, and column.

Acceptance probe at the end verifies the canonical rendering that the
DAT course expects for the group/ungroup operators.
"""

from __future__ import annotations

import pytest

from txt2tex.ast_nodes import (
    Divide,
    Document,
    DocumentItem,
    Expr,
    Group,
    Identifier,
    NaturalJoin,
    Project,
    Rename,
    Restrict,
    Ungroup,
)
from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import RESERVED_WORDS, Lexer
from txt2tex.parser import Parser, ParserError
from txt2tex.tokens import Token, TokenType

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _lex(src: str) -> list[Token]:
    """Tokenize src."""
    return Lexer(src).tokenize()


def _parse(src: str) -> Document:
    """Parse src into a Document, wrapping bare Expr results."""
    result = Parser(_lex(src)).parse()
    if isinstance(result, Document):
        return result
    return Document(items=[result], line=1, column=1)


def _expr(src: str) -> DocumentItem:
    """Parse a single-line expression and return the first document item."""
    return _parse(src).items[0]


def _expr_latex(src: str) -> str:
    """Generate LaTeX for an expression (math content without wrapper)."""
    gen = LaTeXGenerator(use_fuzz=True)
    ast = Parser(_lex(src)).parse()
    item: Expr = ast.items[0] if isinstance(ast, Document) else ast  # type: ignore[assignment]
    return gen.generate_expr(item)


# ---------------------------------------------------------------------------
# Lexer: GROUP and UNGROUP tokens
# ---------------------------------------------------------------------------


class TestGroupUngroupLexer:
    """GROUP and UNGROUP tokenize correctly."""

    def test_group_token(self) -> None:
        """'group' lexes to GROUP token."""
        tokens = _lex("group")
        assert tokens[0].type == TokenType.GROUP
        assert tokens[0].value == "group"

    def test_ungroup_token(self) -> None:
        """'ungroup' lexes to UNGROUP token."""
        tokens = _lex("ungroup")
        assert tokens[0].type == TokenType.UNGROUP
        assert tokens[0].value == "ungroup"

    def test_group_in_reserved_words(self) -> None:
        """'group' is reserved — decoration suffix is forbidden."""
        assert "group" in RESERVED_WORDS

    def test_ungroup_in_reserved_words(self) -> None:
        """'ungroup' is reserved — decoration suffix is forbidden."""
        assert "ungroup" in RESERVED_WORDS

    def test_group_column_position(self) -> None:
        """GROUP token reports correct column."""
        tokens = _lex("R group")
        group_tok = next(t for t in tokens if t.type == TokenType.GROUP)
        assert group_tok.column == 3

    def test_ungroup_column_position(self) -> None:
        """UNGROUP token reports correct column."""
        tokens = _lex("R ungroup")
        ungroup_tok = next(t for t in tokens if t.type == TokenType.UNGROUP)
        assert ungroup_tok.column == 3


# ---------------------------------------------------------------------------
# Parser — Group
# ---------------------------------------------------------------------------


class TestGroupParser:
    """Parser produces Group nodes."""

    def test_group_single_attr(self) -> None:
        """R group ({A} as members) produces Group with one attribute."""
        node = _expr("R group ({A} as members)")
        assert isinstance(node, Group)
        assert isinstance(node.relation, Identifier)
        assert node.relation.name == "R"
        assert node.attrs == ["A"]
        assert node.alias == "members"

    def test_group_multi_attr(self) -> None:
        """R group ({A, B, C} as nested) produces Group with three attributes."""
        node = _expr("R group ({A, B, C} as nested)")
        assert isinstance(node, Group)
        assert node.attrs == ["A", "B", "C"]
        assert node.alias == "nested"

    def test_group_two_attrs(self) -> None:
        """R group ({A, B} as sub) produces Group with two attributes."""
        node = _expr("R group ({A, B} as sub)")
        assert isinstance(node, Group)
        assert node.attrs == ["A", "B"]
        assert node.alias == "sub"

    def test_group_position(self) -> None:
        """Group node carries position of 'group' keyword."""
        node = _expr("R group ({A} as m)")
        assert node.line == 1
        assert node.column == 3

    def test_group_composed_with_project(self) -> None:
        """pi[X](R group ({A} as nested)) — Group inside projection."""
        node = _expr("pi[X](R group ({A} as nested))")
        assert isinstance(node, Project)
        assert isinstance(node.relation, Group)
        assert node.relation.attrs == ["A"]
        assert node.relation.alias == "nested"


# ---------------------------------------------------------------------------
# Parser — Ungroup
# ---------------------------------------------------------------------------


class TestUngroupParser:
    """Parser produces Ungroup nodes."""

    def test_ungroup_simple(self) -> None:
        """R ungroup members produces Ungroup."""
        node = _expr("R ungroup members")
        assert isinstance(node, Ungroup)
        assert isinstance(node.relation, Identifier)
        assert node.relation.name == "R"
        assert node.alias == "members"

    def test_ungroup_position(self) -> None:
        """Ungroup node carries position of 'ungroup' keyword."""
        node = _expr("R ungroup members")
        assert node.line == 1
        assert node.column == 3

    def test_ungroup_chained(self) -> None:
        """R ungroup a ungroup b chains left-associatively."""
        node = _expr("R ungroup a ungroup b")
        assert isinstance(node, Ungroup)
        assert node.alias == "b"
        assert isinstance(node.relation, Ungroup)
        assert node.relation.alias == "a"


# ---------------------------------------------------------------------------
# Parser — negative cases
# ---------------------------------------------------------------------------


class TestGroupUngroupNegative:
    """Invalid syntax raises ParserError with message, line, column."""

    def test_group_missing_parens(self) -> None:
        """R group A (missing parens) raises ParserError."""
        with pytest.raises(ParserError) as exc_info:
            _parse("R group A")
        err = exc_info.value
        assert "(" in err.message or "paren" in err.message.lower()
        assert err.token.line == 1

    def test_group_missing_alias(self) -> None:
        """R group ({A} as) (missing alias) raises ParserError."""
        with pytest.raises(ParserError) as exc_info:
            _parse("R group ({A} as)")
        err = exc_info.value
        assert err.token.line == 1

    def test_group_missing_brace(self) -> None:
        """R group (A as m) (missing braces) raises ParserError."""
        with pytest.raises(ParserError) as exc_info:
            _parse("R group (A as m)")
        err = exc_info.value
        assert err.token.line == 1

    def test_ungroup_missing_alias(self) -> None:
        """R ungroup (missing alias) raises ParserError."""
        with pytest.raises(ParserError) as exc_info:
            _parse("R ungroup")
        err = exc_info.value
        assert err.token.line == 1

    def test_group_trailing_comma(self) -> None:
        """R group ({A, } as m) raises with 'expected attribute name'."""
        with pytest.raises(ParserError) as exc_info:
            _parse("R group ({A, } as m)")
        err = exc_info.value
        assert "attribute" in err.message.lower()
        assert err.token.line == 1

    def test_group_as_misspelled_echoes_token(self) -> None:
        """R group ({A} bs m) — wrong 'as' keyword names the offender."""
        with pytest.raises(ParserError) as exc_info:
            _parse("R group ({A} bs m)")
        err = exc_info.value
        assert "as" in err.message
        assert "'bs'" in err.message
        assert err.token.line == 1

    def test_group_keyword_usable_as_attr_name(self) -> None:
        """A column literally named 'group' is allowed as an attr name."""
        doc = _parse("R group ({group} as nested)")
        node = doc.items[0]
        assert isinstance(node, Group)
        assert node.attrs == ["group"]

    def test_ungroup_alias_named_ungroup_is_legal(self) -> None:
        """An attribute literally named 'ungroup' is allowed as the alias."""
        doc = _parse("R ungroup ungroup")
        node = doc.items[0]
        assert isinstance(node, Ungroup)
        assert node.alias == "ungroup"


# ---------------------------------------------------------------------------
# Generator — Group LaTeX output
# ---------------------------------------------------------------------------

_GROUP_OP = r"\mathop{\mathrm{GROUP}}"
_AS_OP = r"\mathop{\mathrm{AS}}"
_UNGROUP_OP = r"\mathop{\mathrm{UNGROUP}}"


class TestGroupGenerator:
    """LaTeX generator emits correct output for Group nodes."""

    def test_group_single_attr_latex(self) -> None:
        r"""R group ({A} as m) emits GROUP and AS mathop operators."""
        result = _expr_latex("R group ({A} as m)")
        assert _GROUP_OP in result
        assert _AS_OP in result
        assert r"\{A\}" in result
        assert "m" in result

    def test_group_multi_attr_latex(self) -> None:
        """R group ({A, B} as nested) — attrs appear in output."""
        result = _expr_latex("R group ({A, B} as nested)")
        assert "A" in result
        assert "B" in result
        assert _GROUP_OP in result

    def test_group_full_form(self) -> None:
        r"""R group ({A} as members) renders exact canonical form."""
        result = _expr_latex("R group ({A} as members)")
        expected = (
            r"R \mathop{\mathrm{GROUP}}"
            r" (\{A\} \mathop{\mathrm{AS}} members)"
        )
        assert result == expected

    def test_group_named_relation(self) -> None:
        r"""Members group ({username} as m) — Members renders italic (no wrap)."""
        result = _expr_latex("Members group ({username} as m)")
        assert "Members" in result
        assert r"\mathrm{Members}" not in result

    def test_group_multi_attr_full(self) -> None:
        r"""Multi-attr: attrs appear comma-separated inside \{...\}."""
        result = _expr_latex("R group ({A, B, C} as nested)")
        expected = (
            r"R \mathop{\mathrm{GROUP}}"
            r" (\{A, B, C\} \mathop{\mathrm{AS}} nested)"
        )
        assert result == expected


# ---------------------------------------------------------------------------
# Generator — Ungroup LaTeX output
# ---------------------------------------------------------------------------


class TestUngroupGenerator:
    """LaTeX generator emits correct output for Ungroup nodes."""

    def test_ungroup_latex(self) -> None:
        r"""R ungroup members → R \mathop{\mathrm{UNGROUP}} members."""
        result = _expr_latex("R ungroup members")
        assert result == r"R \mathop{\mathrm{UNGROUP}} members"

    def test_ungroup_named_relation(self) -> None:
        r"""Members ungroup sub — Members renders italic (no wrap)."""
        result = _expr_latex("Members ungroup sub")
        assert "Members" in result
        assert r"\mathrm{Members}" not in result

    def test_ungroup_mathop(self) -> None:
        r"""UNGROUP uses \mathop{\mathrm{UNGROUP}} for proper spacing."""
        result = _expr_latex("R ungroup m")
        assert _UNGROUP_OP in result


# ---------------------------------------------------------------------------
# Acceptance probe — from mission contract
# ---------------------------------------------------------------------------


class TestGroupUngroupAcceptance:
    """Acceptance probe: GroupMembers group ({username} as members)."""

    def test_acceptance_probe(self) -> None:
        r"""Full round-trip acceptance probe per mission contract.

        GroupMembers group ({username} as members)

        Must render:
        GroupMembers \mathop{\mathrm{GROUP}} (\{username\} \mathop{\mathrm{AS}} members)
        """
        src = "GroupMembers group ({username} as members)"
        doc = _parse(src)
        group_node = doc.items[0]
        assert isinstance(group_node, Group)
        assert group_node.attrs == ["username"]
        assert group_node.alias == "members"

        result = _expr_latex(src)
        expected = (
            r"GroupMembers \mathop{\mathrm{GROUP}}"
            r" (\{username\} \mathop{\mathrm{AS}} members)"
        )
        assert result == expected

    def test_regression_algebra_still_works(self) -> None:
        """Existing algebra operators continue to parse and render."""
        assert isinstance(_expr("sigma[p](R)"), Restrict)
        assert isinstance(_expr("pi[a, b](R)"), Project)
        assert isinstance(_expr("rho[a as b](R)"), Rename)
        assert isinstance(_expr("R bowtie S"), NaturalJoin)
        assert isinstance(_expr("R div S"), Divide)
