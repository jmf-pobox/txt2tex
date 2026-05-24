"""Tests for horizontal schema definitions (defs paragraph) per Z RM §3.8.

Phase 1.3 — ``Name [generics]? defs RHS`` renders as
``\\begin{zed} Name \\defs RHS \\end{zed}``.

Two RHS forms:
  1. Schema reference (possibly decorated, possibly generic):
     ``OpAlias defs Delta Counter``
  2. Inline schema text:
     ``NatPair defs [ x, y : N | x < y ]``

Coverage (~28 cases):
  - Token: DEFS lexed correctly; defs in RESERVED_WORDS; defs' rejected.
  - AST: HorizDef and SchemaText nodes constructed correctly.
  - Parser: both RHS forms, generic LHS, multi-predicate inline text.
  - Generator: round-trip to expected LaTeX strings.
  - Regressions: existing schema, axdef, gendef, abbreviation paragraphs unchanged.
  - Negatives: missing RHS, missing LHS, unclosed generic bracket.
"""

from __future__ import annotations

import pytest

from txt2tex.ast_nodes import (
    Document,
    GenericInstantiation,
    HorizDef,
    Identifier,
    SchemaInclusion,
    SchemaText,
)
from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import RESERVED_WORDS, Lexer, LexerError
from txt2tex.parser import Parser, ParserError
from txt2tex.tokens import TokenType

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def lex(source: str) -> list[TokenType]:
    """Return token types for source."""
    return [t.type for t in Lexer(source).tokenize()]


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


def first_item(source: str) -> object:
    """Return the first document item from parsed source."""
    doc = parse(source)
    assert doc.items, "document has no items"
    return doc.items[0]


# ---------------------------------------------------------------------------
# 1. Token / lexer
# ---------------------------------------------------------------------------


class TestDefsTokenisation:
    """``defs`` must lex as DEFS, be in RESERVED_WORDS, and reject decoration."""

    def test_defs_lexes_as_defs_token(self) -> None:
        """``defs`` is recognised as DEFS, not IDENTIFIER."""
        types = lex("OpAlias defs Delta Counter")
        assert TokenType.DEFS in types

    def test_defs_not_identifier(self) -> None:
        """No IDENTIFIER token has value 'defs' when defs is a keyword."""
        tokens = Lexer("OpAlias defs Delta Counter").tokenize()
        identifiers = [t.value for t in tokens if t.type == TokenType.IDENTIFIER]
        assert "defs" not in identifiers

    def test_defs_in_reserved_words(self) -> None:
        """``defs`` is in RESERVED_WORDS so decoration is forbidden."""
        assert "defs" in RESERVED_WORDS

    def test_defs_decorated_raises_lexer_error(self) -> None:
        """``defs'`` is a decorated reserved word and must raise LexerError."""
        with pytest.raises(LexerError):
            Lexer("defs'").tokenize()

    def test_defs_keyword_in_context(self) -> None:
        """DEFS token appears at the right position in a horiz def."""
        tokens = Lexer("S defs [ x : N | x > 0 ]").tokenize()
        defs_tokens = [t for t in tokens if t.type == TokenType.DEFS]
        assert len(defs_tokens) == 1
        assert defs_tokens[0].value == "defs"


# ---------------------------------------------------------------------------
# 2. Parser — schema reference RHS
# ---------------------------------------------------------------------------


class TestHorizDefSchemaRef:
    """Horizontal definitions with a schema reference on the RHS."""

    def test_simple_alias(self) -> None:
        """``OpAlias defs Op`` produces HorizDef with Identifier body."""
        item = first_item("OpAlias defs Op")
        assert isinstance(item, HorizDef)
        assert item.name == "OpAlias"
        assert item.generics is None
        assert isinstance(item.body, Identifier)
        assert item.body.name == "Op"

    def test_delta_decorated_reference(self) -> None:
        """``OpDeltaCounter defs Delta Counter`` produces SchemaInclusion body."""
        item = first_item("OpDeltaCounter defs Delta Counter")
        assert isinstance(item, HorizDef)
        assert item.name == "OpDeltaCounter"
        assert isinstance(item.body, SchemaInclusion)
        assert item.body.decoration == "delta"
        assert item.body.name == "Counter"

    def test_xi_decorated_reference(self) -> None:
        """``ReadCounter defs Xi Counter`` produces SchemaInclusion(xi) body."""
        item = first_item("ReadCounter defs Xi Counter")
        assert isinstance(item, HorizDef)
        assert isinstance(item.body, SchemaInclusion)
        assert item.body.decoration == "xi"
        assert item.body.name == "Counter"

    def test_primed_reference(self) -> None:
        """``OpPrimed defs Op'`` yields Identifier with primed name."""
        item = first_item("OpPrimed defs Op'")
        assert isinstance(item, HorizDef)
        assert isinstance(item.body, Identifier)
        assert item.body.name == "Op'"

    def test_generic_instantiation_rhs(self) -> None:
        """``StackOp defs Stack[N]`` yields GenericInstantiation body."""
        item = first_item("StackOp defs Stack[N]")
        assert isinstance(item, HorizDef)
        assert isinstance(item.body, GenericInstantiation)

    def test_generic_lhs(self) -> None:
        """``Stack[X] defs Op`` carries generics=["X"] on the node."""
        item = first_item("Stack[X] defs Op")
        assert isinstance(item, HorizDef)
        assert item.name == "Stack"
        assert item.generics == ["X"]

    def test_generic_lhs_multi_param(self) -> None:
        """``Map[K, V] defs Op`` carries generics=["K", "V"]."""
        item = first_item("Map[K, V] defs Op")
        assert isinstance(item, HorizDef)
        assert item.generics == ["K", "V"]


# ---------------------------------------------------------------------------
# 3. Parser — inline schema text RHS
# ---------------------------------------------------------------------------


class TestHorizDefSchemaText:
    """Horizontal definitions with inline schema text on the RHS."""

    def test_simple_inline(self) -> None:
        """``S defs [ x, y : N | x < y ]`` produces SchemaText body."""
        item = first_item("S defs [ x, y : N | x < y ]")
        assert isinstance(item, HorizDef)
        assert isinstance(item.body, SchemaText)

    def test_schema_text_declarations(self) -> None:
        """Inline schema text has the correct number of declarations."""
        item = first_item("NatPair defs [ x, y : N | x < y ]")
        assert isinstance(item, HorizDef)
        body = item.body
        assert isinstance(body, SchemaText)
        # x and y expanded from "x, y : N" → two Declaration nodes
        assert len(body.declarations) == 2

    def test_schema_text_predicates(self) -> None:
        """Inline schema text carries the predicate expressions as a flat list."""
        item = first_item("NatPair defs [ x, y : N | x < y ]")
        assert isinstance(item, HorizDef)
        body = item.body
        assert isinstance(body, SchemaText)
        # predicates is a flat list[Expr], not a list[list[Expr]]
        assert len(body.predicates) == 1

    def test_multi_pred_inline(self) -> None:
        """``S defs [x : N | x > 0; x < 100]`` has two predicates in the flat list."""
        item = first_item("S defs [x : N | x > 0; x < 100]")
        assert isinstance(item, HorizDef)
        body = item.body
        assert isinstance(body, SchemaText)
        # predicates is a flat list[Expr]; semicolons are separators, not groupers
        assert len(body.predicates) == 2

    def test_generic_lhs_inline_text(self) -> None:
        """``Stack[X] defs [s : seq X | true]`` combines generic LHS and inline text."""
        item = first_item("Stack[X] defs [s : seq X | true]")
        assert isinstance(item, HorizDef)
        assert item.generics == ["X"]
        assert isinstance(item.body, SchemaText)


# ---------------------------------------------------------------------------
# 4. LaTeX generator — schema reference RHS
# ---------------------------------------------------------------------------


class TestHorizDefGeneratorRef:
    """Generator produces correct \\begin{zed} ... \\defs ... \\end{zed} output."""

    def test_acceptance_probe(self) -> None:
        r"""Acceptance probe: ``OpAlias defs Delta Counter`` round-trips."""
        tex = latex("OpAlias defs Delta Counter")
        assert "\\begin{zed}" in tex
        assert "OpAlias \\defs \\Delta Counter" in tex
        assert "\\end{zed}" in tex

    def test_simple_alias_latex(self) -> None:
        r"""``A defs B`` emits ``A \defs B``."""
        tex = latex("A defs B")
        assert "A \\defs B" in tex

    def test_xi_reference_latex(self) -> None:
        r"""``ReadOp defs Xi Counter`` emits ``ReadOp \defs \Xi Counter``."""
        tex = latex("ReadOp defs Xi Counter")
        assert "ReadOp \\defs \\Xi Counter" in tex

    def test_primed_reference_latex(self) -> None:
        r"""``OpP defs Op'`` emits ``OpP \defs Op'``."""
        tex = latex("OpP defs Op'")
        assert "OpP \\defs" in tex
        assert "Op'" in tex

    def test_generic_lhs_latex(self) -> None:
        r"""``Stack[X] defs Op`` emits ``Stack[X] \defs Op``."""
        tex = latex("Stack[X] defs Op")
        assert "Stack[X] \\defs Op" in tex

    def test_generic_lhs_multi_param_latex(self) -> None:
        r"""``Map[K, V] defs Op`` emits ``Map[K, V] \defs Op``."""
        tex = latex("Map[K, V] defs Op")
        assert "Map[K, V] \\defs Op" in tex

    def test_zed_environment_wrapping(self) -> None:
        r"""Every HorizDef is wrapped in ``\begin{zed}...\end{zed}``."""
        tex = latex("X defs Y")
        assert tex.count("\\begin{zed}") == 1
        assert tex.count("\\end{zed}") == 1

    def test_bare_reference_no_delta_xi(self) -> None:
        r"""Plain reference: ``A defs B`` emits just ``B``, not ``\Delta B``."""
        tex = latex("A defs B")
        assert "\\Delta" not in tex
        assert "\\Xi" not in tex


# ---------------------------------------------------------------------------
# 5. LaTeX generator — inline schema text RHS
# ---------------------------------------------------------------------------


class TestHorizDefGeneratorText:
    """Generator for inline schema text RHS."""

    def test_simple_inline_latex(self) -> None:
        r"""``S defs [ x, y : N | x < y ]`` emits bracket form."""
        tex = latex("S defs [ x, y : N | x < y ]")
        assert "\\defs" in tex
        # Declarations joined by ;
        assert ";" in tex
        # Predicate separator |
        assert "|" in tex

    def test_multi_pred_uses_land(self) -> None:
        r"""Multiple predicates are joined with ``\land``."""
        tex = latex("S defs [x : N | x > 0; x < 100]")
        assert "\\land" in tex

    def test_generic_lhs_inline_latex(self) -> None:
        r"""``Stack[X] defs [s : seq X | true]`` emits ``Stack[X] \defs [...]``."""
        tex = latex("Stack[X] defs [s : seq X | true]")
        assert "Stack[X] \\defs" in tex
        assert "[" in tex


# ---------------------------------------------------------------------------
# 6. Multiple definitions in a document
# ---------------------------------------------------------------------------


class TestHorizDefMultiple:
    """Multiple HorizDef paragraphs in one document parse correctly."""

    def test_two_horiz_defs(self) -> None:
        """Two sequential horizontal definitions parse as two items."""
        source = "A defs B\nC defs D"
        doc = parse(source)
        assert len(doc.items) == 2
        assert all(isinstance(item, HorizDef) for item in doc.items)

    def test_horiz_def_followed_by_schema(self) -> None:
        """HorizDef followed by a schema block parses correctly."""
        source = "MyOp defs Delta State\nschema State\n  x : N\nend"
        doc = parse(source)
        assert len(doc.items) == 2
        assert isinstance(doc.items[0], HorizDef)

    def test_latex_two_defs(self) -> None:
        """Two horizontal defs generate two zed environments."""
        tex = latex("A defs B\nC defs D")
        assert tex.count("\\begin{zed}") == 2


# ---------------------------------------------------------------------------
# 7. Regression — existing paragraphs unaffected
# ---------------------------------------------------------------------------


class TestHorizDefRegression:
    """Existing paragraph types still parse and generate identically."""

    def test_schema_unaffected(self) -> None:
        """A schema block is not mistaken for a horizontal definition."""
        tex = latex("schema S\n  x : N\nend")
        assert "\\begin{schema}{S}" in tex
        assert "\\defs" not in tex

    def test_axdef_unaffected(self) -> None:
        """An axdef block is not affected."""
        tex = latex("axdef\n  f : N -> N\nend")
        assert "\\begin{axdef}" in tex
        assert "\\defs" not in tex

    def test_abbreviation_unaffected(self) -> None:
        """An abbreviation (==) is not confused with defs."""
        tex = latex("MyAbbrev == N cross N")
        assert "==" in tex or "\\defs" not in tex
        assert "\\defs" not in tex

    def test_given_type_unaffected(self) -> None:
        """A given type block is not affected."""
        tex = latex("given NAME, AGE")
        assert "[NAME, AGE]" in tex


# ---------------------------------------------------------------------------
# 8. Negative tests
# ---------------------------------------------------------------------------


class TestHorizDefNegative:
    """Negative cases raise ParserError with position information."""

    def test_no_rhs_raises(self) -> None:
        """``Name defs`` with no RHS raises ParserError."""
        with pytest.raises(ParserError) as exc_info:
            parse("Name defs")
        err = exc_info.value
        assert err.message  # non-empty message
        assert err.token.line >= 1
        assert err.token.column >= 1

    def test_no_rhs_message_content(self) -> None:
        """Error message mentions the missing RHS expectation."""
        with pytest.raises(ParserError) as exc_info:
            parse("Name defs")
        msg = exc_info.value.message.lower()
        assert "defs" in msg or "rhs" in msg

    def test_defs_without_lhs_is_not_top_level(self) -> None:
        """``defs Op`` with no LHS does not start a horizontal definition.

        ``defs`` is a keyword and cannot be an identifier, so the parser
        fails trying to parse the token in expression context.
        """
        with pytest.raises((ParserError, LexerError)):
            parse("defs Op")

    def test_unclosed_generic_bracket_raises(self) -> None:
        """``Stack[X defs Op`` (missing ']') raises ParserError."""
        with pytest.raises(ParserError) as exc_info:
            parse("Stack[X defs Op")
        err = exc_info.value
        assert err.token.line >= 1
        assert err.token.column >= 1

    def test_unclosed_generic_bracket_position(self) -> None:
        """Error for ``Stack[X defs Op`` points at the DEFS token (col 9)."""
        with pytest.raises(ParserError) as exc_info:
            parse("Stack[X defs Op")
        err = exc_info.value
        # _scan_for_defs_after_brackets returns False (NEWLINE not present but
        # bracket is unclosed), so _parse_postfix parses the generic arg list
        # and fails at the DEFS token.
        assert err.token.line == 1
        assert err.token.column == 9

    def test_unclosed_schema_text_bracket_raises(self) -> None:
        """``S defs [ x : N | x > 0`` (missing ']') raises ParserError at col 8."""
        with pytest.raises(ParserError) as exc_info:
            parse("S defs [ x : N | x > 0")
        err = exc_info.value
        # The open '[' is at column 8; _parse_schema_text pins the error there.
        assert err.token.line == 1
        assert err.token.column == 8

    # --- FIX 2: empty inline schema text ---

    def test_empty_brackets_raises(self) -> None:
        """``S defs [ ]`` raises ParserError — at least one declaration required."""
        with pytest.raises(ParserError) as exc_info:
            parse("S defs [ ]")
        assert "declaration" in exc_info.value.message.lower()

    def test_tight_empty_brackets_raises(self) -> None:
        """``S defs []`` raises ParserError — no space makes no difference."""
        with pytest.raises(ParserError) as exc_info:
            parse("S defs []")
        assert "declaration" in exc_info.value.message.lower()

    def test_pipe_only_raises(self) -> None:
        """``S defs [ | ]`` raises ParserError — pipe with no decls is invalid."""
        with pytest.raises(ParserError) as exc_info:
            parse("S defs [ | ]")
        assert "declaration" in exc_info.value.message.lower()

    def test_pred_without_decl_raises(self) -> None:
        """``S defs [ | x > 0 ]`` raises ParserError — predicate needs a declaration."""
        with pytest.raises(ParserError) as exc_info:
            parse("S defs [ | x > 0 ]")
        assert "declaration" in exc_info.value.message.lower()

    # --- FIX 1: NEWLINE in generic bracket terminates defs scan ---

    def test_newline_in_generic_bracket_not_a_horiz_def(self) -> None:
        """``Stack[X`` on one line, ``defs Op`` on the next, is NOT a HorizDef.

        The NEWLINE inside the bracket causes _scan_for_defs_after_brackets
        to return False, so the parser does not interpret this as a horizontal
        definition.  It will raise rather than silently misparse.
        """
        with pytest.raises((ParserError, LexerError)):
            parse("Stack[X\ndefs Op")
