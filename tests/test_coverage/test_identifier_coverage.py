"""Tests for identifier underscore handling and decoration coverage."""

from __future__ import annotations

import pytest

from txt2tex.ast_nodes import Identifier
from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer, LexerError
from txt2tex.parser import Parser
from txt2tex.tokens import TokenType


def test_multi_word_identifier_long_prefix() -> None:
    """Test multi-word identifier with long prefix (>3 chars)."""
    node = Identifier(name="cumulative_total", line=1, column=1)
    gen = LaTeXGenerator()
    latex = gen._generate_identifier(node)

    # Should use mathit with escaped underscore
    assert latex == r"\mathit{cumulative\_total}"


def test_multi_word_identifier_long_suffix() -> None:
    """Test multi-word identifier with long suffix (>3 chars)."""
    node = Identifier(name="max_value", line=1, column=1)
    gen = LaTeXGenerator()
    latex = gen._generate_identifier(node)

    # Should use mathit with escaped underscore
    assert latex == r"\mathit{max\_value}"


def test_single_char_subscript() -> None:
    """Test subscript with single character after underscore."""
    node = Identifier(name="x_1", line=1, column=1)
    gen = LaTeXGenerator()
    latex = gen._generate_identifier(node)

    # Should use subscript notation without braces
    assert latex == "x_1"


def test_multi_char_subscript() -> None:
    """Test subscript with multiple characters after underscore."""
    node = Identifier(name="state_init", line=1, column=1)
    gen = LaTeXGenerator()
    latex = gen._generate_identifier(node)

    # Could be subscript with braces or mathit depending on length
    assert "state_{init}" in latex or r"\mathit{state\_init}" in latex


def test_three_part_identifier() -> None:
    """Test identifier with multiple underscores (fallback case)."""
    node = Identifier(name="a_b_c", line=1, column=1)
    gen = LaTeXGenerator()
    latex = gen._generate_identifier(node)

    # Should use fallback: mathit with escaped underscores
    assert latex == r"\mathit{a\_b\_c}"


def test_identifier_no_underscore() -> None:
    """Test identifier without underscore."""
    node = Identifier(name="simple", line=1, column=1)
    gen = LaTeXGenerator()
    latex = gen._generate_identifier(node)

    # Should return as-is
    assert latex == "simple"


# ---------------------------------------------------------------------------
# Phase 0: Identifier decoration — lexer tokenises suffix correctly
# ---------------------------------------------------------------------------


def _ident_value(source: str) -> str:
    """Return the IDENTIFIER token value from a single-token source."""
    tokens = [t for t in Lexer(source).tokenize() if t.type == TokenType.IDENTIFIER]
    assert len(tokens) == 1, f"Expected 1 IDENTIFIER token, got {tokens}"
    return tokens[0].value


def test_prime_suffix() -> None:
    """s' lexes as a single IDENTIFIER with name 's'."""
    assert _ident_value("s'") == "s'"


def test_double_prime_suffix() -> None:
    """s'' lexes as a single IDENTIFIER with name 's''."""
    assert _ident_value("s''") == "s''"


def test_question_suffix() -> None:
    """x? lexes as a single IDENTIFIER with name 'x?'."""
    assert _ident_value("x?") == "x?"


def test_bang_suffix() -> None:
    """y! lexes as a single IDENTIFIER with name 'y!'."""
    assert _ident_value("y!") == "y!"


def test_mixed_prime_question_suffix() -> None:
    """x?' lexes as a single IDENTIFIER with name 'x?'."""
    assert _ident_value("x?'") == "x?'"


def test_mixed_question_prime_suffix() -> None:
    """x'? lexes as a single IDENTIFIER with name 'x'?'."""
    assert _ident_value("x'?") == "x'?"


def test_multi_char_base_with_prime() -> None:
    """count' lexes as IDENTIFIER count'."""
    assert _ident_value("count'") == "count'"


def test_multi_char_base_with_bang() -> None:
    """out! lexes as IDENTIFIER out!."""
    assert _ident_value("out!") == "out!"


def test_multi_char_base_with_question() -> None:
    """in? lexes as IDENTIFIER in?."""
    assert _ident_value("in?") == "in?"


def test_undecorated_identifier_unchanged() -> None:
    """Undecorated identifiers emit byte-identical output before and after."""
    assert _ident_value("count") == "count"
    assert _ident_value("Person") == "Person"


def test_decorated_identifier_generator_verbatim() -> None:
    """Generator emits decorated identifier name verbatim."""
    gen = LaTeXGenerator()
    for decorated in ("s'", "x?", "y!", "count'", "out!", "in?"):
        node = Identifier(name=decorated, line=1, column=1)
        result = gen._generate_identifier(node)
        assert result == decorated, f"Expected {decorated!r}, got {result!r}"


def _roundtrip(source: str) -> str:
    """Lex → parse → generate for a complete document fragment."""
    tokens = Lexer(source).tokenize()
    ast = Parser(tokens).parse()
    return LaTeXGenerator().generate_document(ast)


def test_decorated_identifiers_in_schema() -> None:
    """Schema with decorated identifiers round-trips through parser and generator."""
    source = (
        "schema StateOp\n"
        "  count, count' : N\n"
        "  in? : N\n"
        "  out! : N\n"
        "where\n"
        "  count' = count + in?\n"
        "  out! = count\n"
        "end"
    )
    latex = _roundtrip(source)
    # All decorated identifiers must appear in the output
    assert "count'" in latex
    assert "in?" in latex
    assert "out!" in latex


def test_prime_in_schema_where_clause() -> None:
    """Primed identifier in schema where clause round-trips."""
    source = "schema S\n  x, x' : N\nwhere\n  x' = x + 1\nend"
    latex = _roundtrip(source)
    assert "x'" in latex


def test_not_equal_not_confused_with_bang_suffix() -> None:
    """'!=' is still NOT_EQUAL, not an identifier suffix."""
    tokens = [
        t for t in Lexer("x != y").tokenize() if t.type not in (TokenType.WHITESPACE,)
    ]
    types = [t.type for t in tokens]
    assert TokenType.NOT_EQUAL in types
    # x should be an undecorated identifier
    ident = next(t for t in tokens if t.type == TokenType.IDENTIFIER and t.value == "x")
    assert ident.value == "x"


# ---------------------------------------------------------------------------
# Fix 2: cap ? and ! to one each per identifier
# ---------------------------------------------------------------------------


def test_double_question_raises() -> None:
    """x?? raises LexerError — ? may appear at most once per identifier."""
    with pytest.raises(LexerError) as ei:
        Lexer("x??").tokenize()
    assert "Multiple '?' decorators" in str(ei.value)
    # Error should point at the second ?, which is column 3 (1-indexed).
    assert ei.value.line == 1
    assert ei.value.column == 3


def test_double_bang_raises() -> None:
    """y!! raises LexerError — ! may appear at most once per identifier."""
    with pytest.raises(LexerError) as ei:
        Lexer("y!!").tokenize()
    assert "Multiple '!' decorators" in str(ei.value)
    assert ei.value.line == 1
    assert ei.value.column == 3


def test_question_bang_question_raises() -> None:
    """z?!? raises LexerError — second ? after consuming z?! is rejected."""
    with pytest.raises(LexerError) as ei:
        Lexer("z?!?").tokenize()
    assert "Multiple '?' decorators" in str(ei.value)
    # Second ? is at column 4 (z=1, ?=2, !=3, ?=4).
    assert ei.value.line == 1
    assert ei.value.column == 4


def test_single_question_and_bang_ok() -> None:
    """x?! is a valid decorated identifier (one ? and one !)."""
    assert _ident_value("x?!") == "x?!"


def test_question_then_prime_ok() -> None:
    """x?' is valid — ? once, then unlimited primes."""
    assert _ident_value("x?'") == "x?'"


# ---------------------------------------------------------------------------
# Fix 3: reject decoration on reserved keywords
# ---------------------------------------------------------------------------


def test_forall_prime_raises() -> None:
    """forall' raises LexerError — cannot decorate reserved keyword."""
    with pytest.raises(LexerError) as ei:
        Lexer("forall'").tokenize()
    assert "Cannot decorate reserved keyword 'forall'" in str(ei.value)
    # ' is at column 7 (f=1…l=6, '=7).
    assert ei.value.line == 1
    assert ei.value.column == 7


def test_schema_prime_raises() -> None:
    """schema' raises LexerError — cannot decorate reserved keyword."""
    with pytest.raises(LexerError) as ei:
        Lexer("schema'").tokenize()
    assert "Cannot decorate reserved keyword 'schema'" in str(ei.value)
    assert ei.value.line == 1
    assert ei.value.column == 7


def test_end_bang_raises() -> None:
    """end! raises LexerError — cannot decorate reserved keyword."""
    with pytest.raises(LexerError) as ei:
        Lexer("end!").tokenize()
    assert "Cannot decorate reserved keyword 'end'" in str(ei.value)
    # ! is at column 4 (e=1, n=2, d=3, !=4).
    assert ei.value.line == 1
    assert ei.value.column == 4


def test_where_question_raises() -> None:
    """where? raises LexerError — cannot decorate reserved keyword."""
    with pytest.raises(LexerError) as ei:
        Lexer("where?").tokenize()
    assert "Cannot decorate reserved keyword 'where'" in str(ei.value)
    # ? is at column 6 (w=1…e=5, ?=6).
    assert ei.value.line == 1
    assert ei.value.column == 6


def test_keyword_like_identifier_not_rejected() -> None:
    """forall_x is a user identifier, not the forall keyword — decoration OK."""
    assert _ident_value("forall_x'") == "forall_x'"


def test_count_prime_still_works() -> None:
    """count' is a user identifier (not a keyword) — must not raise."""
    assert _ident_value("count'") == "count'"


# ---------------------------------------------------------------------------
# Fix 3 extension: pseudo-keyword decoration bypass (CRITICAL)
#
# The original Fix 3 only checked KEYWORD_TO_TOKEN | KEYWORD_ALIASES.
# Colon-postfix pseudo-keywords (ARGUE, PROOF, TEXT, TRUTH, …) were not
# covered because they are matched by explicit string comparison in
# _scan_identifier, not through the KEYWORD_TO_TOKEN table.
# RESERVED_WORDS now includes all of these.
# ---------------------------------------------------------------------------


def test_proof_prime_raises() -> None:
    """PROOF' raises LexerError — PROOF is a colon-postfix pseudo-keyword."""
    with pytest.raises(LexerError) as ei:
        Lexer("PROOF'").tokenize()
    assert "Cannot decorate reserved keyword 'PROOF'" in str(ei.value)
    assert ei.value.line == 1
    assert ei.value.column == 6


def test_argue_question_raises() -> None:
    """ARGUE? raises LexerError — ARGUE is a colon-postfix pseudo-keyword."""
    with pytest.raises(LexerError) as ei:
        Lexer("ARGUE?").tokenize()
    assert "Cannot decorate reserved keyword 'ARGUE'" in str(ei.value)
    assert ei.value.line == 1
    assert ei.value.column == 6


def test_truth_bang_raises() -> None:
    """TRUTH! raises LexerError — TRUTH is a colon-postfix pseudo-keyword."""
    with pytest.raises(LexerError) as ei:
        Lexer("TRUTH!").tokenize()
    assert "Cannot decorate reserved keyword 'TRUTH'" in str(ei.value)
    assert ei.value.line == 1
    assert ei.value.column == 6


def test_equal_question_raises() -> None:
    """EQUAL? raises LexerError — EQUAL is a colon-postfix pseudo-keyword."""
    with pytest.raises(LexerError) as ei:
        Lexer("EQUAL?").tokenize()
    assert "Cannot decorate reserved keyword 'EQUAL'" in str(ei.value)
    assert ei.value.line == 1
    assert ei.value.column == 6


def test_infrule_prime_raises() -> None:
    """INFRULE' raises LexerError — INFRULE is a colon-postfix pseudo-keyword."""
    with pytest.raises(LexerError) as ei:
        Lexer("INFRULE'").tokenize()
    assert "Cannot decorate reserved keyword 'INFRULE'" in str(ei.value)
    assert ei.value.line == 1
    assert ei.value.column == 8


def test_text_question_raises() -> None:
    """TEXT? raises LexerError — TEXT is a colon-postfix pseudo-keyword."""
    with pytest.raises(LexerError) as ei:
        Lexer("TEXT?").tokenize()
    assert "Cannot decorate reserved keyword 'TEXT'" in str(ei.value)
    assert ei.value.line == 1
    assert ei.value.column == 5
