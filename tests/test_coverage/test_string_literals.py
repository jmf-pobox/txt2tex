"""Tests for STRING token and StringLit AST node — Phase 0 coverage."""

from __future__ import annotations

import pytest

from txt2tex.ast_nodes import StringLit
from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer, LexerError
from txt2tex.parser import Parser
from txt2tex.tokens import TokenType

# ---------------------------------------------------------------------------
# Lexer: STRING token emission
# ---------------------------------------------------------------------------


def test_string_token_emitted() -> None:
    """Lexer emits a STRING token for a single-quoted literal."""
    tokens = Lexer("'hello'").tokenize()
    string_tokens = [t for t in tokens if t.type == TokenType.STRING]
    assert len(string_tokens) == 1


def test_string_token_value_extracted() -> None:
    """STRING token value contains the content between the quotes."""
    tokens = Lexer("'hello'").tokenize()
    tok = next(t for t in tokens if t.type == TokenType.STRING)
    assert tok.value == "hello"


def test_string_empty() -> None:
    """Empty string '' lexes to STRING token with empty value."""
    tokens = Lexer("''").tokenize()
    tok = next(t for t in tokens if t.type == TokenType.STRING)
    assert tok.value == ""


def test_string_with_spaces() -> None:
    """String literal with embedded spaces round-trips through the lexer."""
    tokens = Lexer("'hello world'").tokenize()
    tok = next(t for t in tokens if t.type == TokenType.STRING)
    assert tok.value == "hello world"


def test_string_escaped_apostrophe() -> None:
    """Escaped apostrophe \\' inside a string literal is preserved."""
    tokens = Lexer(r"'it\'s'").tokenize()
    tok = next(t for t in tokens if t.type == TokenType.STRING)
    assert tok.value == "it's"


def test_string_two_literals_in_sequence() -> None:
    """Two adjacent string literals both yield STRING tokens."""
    tokens = Lexer("'sunk' 'survived'").tokenize()
    string_tokens = [t for t in tokens if t.type == TokenType.STRING]
    assert len(string_tokens) == 2
    assert string_tokens[0].value == "sunk"
    assert string_tokens[1].value == "survived"


def test_string_unterminated_raises() -> None:
    """Unterminated string literal raises LexerError with position."""
    with pytest.raises(LexerError) as ei:
        Lexer("'unclosed").tokenize()
    assert "Unterminated string literal" in str(ei.value)
    assert ei.value.line == 1
    assert ei.value.column == 1


def test_string_unterminated_multiline_raises() -> None:
    """String literal that hits end-of-line raises LexerError with position."""
    with pytest.raises(LexerError) as ei:
        Lexer("'hello\nworld'").tokenize()
    assert "Unterminated string literal" in str(ei.value)
    assert ei.value.line == 1
    assert ei.value.column == 1


def test_string_token_position() -> None:
    """STRING token carries the correct line and column."""
    tokens = Lexer("x 'hi'").tokenize()
    tok = next(t for t in tokens if t.type == TokenType.STRING)
    assert tok.line == 1
    assert tok.column == 3


def test_string_with_operators_around_it() -> None:
    """String literal surrounded by operators lexes all three tokens."""
    tokens = Lexer("x = 'sunk'").tokenize()
    types = [t.type for t in tokens if t.type != TokenType.WHITESPACE]
    assert TokenType.STRING in types
    assert TokenType.EQUALS in types
    assert TokenType.IDENTIFIER in types


# ---------------------------------------------------------------------------
# Generator: StringLit → \text{`...'} LaTeX
# ---------------------------------------------------------------------------


def test_generator_string_lit_basic() -> None:
    """Generator emits \\text{`value'} for a StringLit node."""
    node = StringLit(value="sunk", line=1, column=1)
    gen = LaTeXGenerator()
    result = gen.generate_expr(node)
    assert result == r"\text{`sunk'}"


def test_generator_string_lit_empty() -> None:
    """Generator emits \\text{``'} for an empty StringLit."""
    node = StringLit(value="", line=1, column=1)
    gen = LaTeXGenerator()
    result = gen.generate_expr(node)
    assert result == r"\text{`'}"


def test_generator_string_lit_with_spaces() -> None:
    """Generator emits spaces inside \\text{`...'} verbatim."""
    node = StringLit(value="hello world", line=1, column=1)
    gen = LaTeXGenerator()
    result = gen.generate_expr(node)
    assert result == r"\text{`hello world'}"


def test_generator_string_survived() -> None:
    """Generator renders 'survived' correctly."""
    node = StringLit(value="survived", line=1, column=1)
    gen = LaTeXGenerator()
    result = gen.generate_expr(node)
    assert result == r"\text{`survived'}"


# ---------------------------------------------------------------------------
# Integration: round-trip through parser and generator
# ---------------------------------------------------------------------------


def _roundtrip(source: str) -> str:
    """Lex → parse → generate for a complete document fragment."""
    tokens = Lexer(source).tokenize()
    ast = Parser(tokens).parse()
    return LaTeXGenerator().generate_document(ast)


def test_text_block_with_string_literal_passes_through() -> None:
    """TEXT blocks pass single-quoted prose through unchanged (raw capture).

    TEXT: lines are captured raw by the lexer — apostrophes inside TEXT
    blocks are never tokenised as STRING.  The prose renders with straight
    quotes, not the Z-convention \\text{`...'} form.
    """
    source = "TEXT: The status field can be 'sunk' or 'survived'."
    latex = _roundtrip(source)
    # TEXT blocks are raw — apostrophes pass through as straight quotes
    assert "'sunk'" in latex
    assert "'survived'" in latex


def test_text_block_preserves_surrounding_prose() -> None:
    """Prose around string literals is preserved in TEXT output."""
    source = "TEXT: The status can be 'active' or 'inactive'."
    latex = _roundtrip(source)
    assert "The status can be" in latex
    assert "or" in latex


def test_string_in_schema_predicate() -> None:
    """STRING literal in schema where-clause renders as \\text{`...'}.

    When 'ok' appears as a lexed expression token (not in a TEXT block),
    the parser produces StringLit and the generator emits Z-convention quoting.
    """
    source = "schema S\n  x : N\nwhere\n  x = 'ok'\nend"
    latex = _roundtrip(source)
    assert r"\text{`ok'}" in latex


def test_string_literal_in_zed_block() -> None:
    """STRING literal in a zed block (expression context) renders correctly."""
    source = "zed\n  status = 'active'\nend"
    latex = _roundtrip(source)
    assert r"\text{`active'}" in latex


# ---------------------------------------------------------------------------
# Fix 1: LaTeX special-character escaping in string literal values
# ---------------------------------------------------------------------------


def test_generator_string_lit_curly_braces_escaped() -> None:
    """Curly braces in string value are escaped to prevent malformed LaTeX."""
    node = StringLit(value="f{x}", line=1, column=1)
    gen = LaTeXGenerator()
    result = gen.generate_expr(node)
    # {x} must not pass through raw — \{ and \} are safe in text mode
    assert r"\{" in result
    assert r"\}" in result
    # Full expected form
    assert result == r"\text{`f\{x\}'}"


def test_generator_string_lit_backslash_escaped() -> None:
    """Backslash in string value is escaped to \\textbackslash\\{\\}.

    _escape_latex converts \\ → \\textbackslash{} first, then { } → \\{ \\}.
    So a bare backslash in the value produces \\textbackslash\\{\\} in output.
    """
    node = StringLit(value="a\\b", line=1, column=1)
    gen = LaTeXGenerator()
    result = gen.generate_expr(node)
    # The backslash is converted; the output must not contain a raw backslash
    # as the second character of the value (would cause LaTeX errors).
    assert r"\textbackslash" in result


def test_generator_string_lit_hash_escaped() -> None:
    """Hash in string value is escaped."""
    node = StringLit(value="a#b", line=1, column=1)
    gen = LaTeXGenerator()
    result = gen.generate_expr(node)
    assert r"\#" in result


def test_generator_string_lit_percent_escaped() -> None:
    """Percent in string value is escaped."""
    node = StringLit(value="50%", line=1, column=1)
    gen = LaTeXGenerator()
    result = gen.generate_expr(node)
    assert r"\%" in result


def test_generator_string_lit_dollar_escaped() -> None:
    """Dollar sign in string value is escaped."""
    node = StringLit(value="$100", line=1, column=1)
    gen = LaTeXGenerator()
    result = gen.generate_expr(node)
    assert r"\$" in result


def test_generator_string_lit_ampersand_escaped() -> None:
    """Ampersand in string value is escaped."""
    node = StringLit(value="a&b", line=1, column=1)
    gen = LaTeXGenerator()
    result = gen.generate_expr(node)
    assert r"\&" in result


def test_generator_string_lit_fuzz_mode_escapes_too() -> None:
    """Fuzz mode also escapes LaTeX special characters."""
    node = StringLit(value="f{x}", line=1, column=1)
    gen = LaTeXGenerator(use_fuzz=True)
    result = gen.generate_expr(node)
    assert r"\{" in result
    assert r"\}" in result


def test_string_literal_round_trip_with_brace() -> None:
    """String literal with braces round-trips through lexer and generator cleanly."""
    # The lexer stores the raw value; the generator escapes on output
    tokens = Lexer("'f{x}'").tokenize()
    tok = next(t for t in tokens if t.type == TokenType.STRING)
    assert tok.value == "f{x}"  # lexer stores raw
    node = StringLit(value=tok.value, line=1, column=1)
    gen = LaTeXGenerator()
    result = gen.generate_expr(node)
    assert result == r"\text{`f\{x\}'}"  # generator escapes


# ---------------------------------------------------------------------------
# Adjacency: string literal followed immediately by a decorated identifier
# ---------------------------------------------------------------------------


def test_string_literal_then_decorated_identifier() -> None:
    """'sunk' s' adjacent: STRING then decorated IDENTIFIER, no confusion."""
    tokens = [
        t
        for t in Lexer("'sunk' s'").tokenize()
        if t.type not in (TokenType.WHITESPACE,)
    ]
    types = [t.type for t in tokens]
    assert TokenType.STRING in types
    assert TokenType.IDENTIFIER in types
    string_tok = next(t for t in tokens if t.type == TokenType.STRING)
    ident_tok = next(t for t in tokens if t.type == TokenType.IDENTIFIER)
    assert string_tok.value == "sunk"
    assert ident_tok.value == "s'"


# ---------------------------------------------------------------------------
# Low: round-trip test for \' escape inside string with adjacent decoration
# ---------------------------------------------------------------------------


def test_escaped_apostrophe_round_trip_with_adjacent_decoration() -> None:
    r"""\'  inside a string followed by a decorated identifier is unambiguous.

    Input:  'it\'s' s'
    Lex:    STRING("it's")  IDENTIFIER("s'")
    The escaped apostrophe inside the string must not be confused with the
    closing quote, and the decoration suffix on s' must still apply.
    """
    tokens = [
        t
        for t in Lexer(r"'it\'s' s'").tokenize()
        if t.type not in (TokenType.WHITESPACE,)
    ]
    types = [t.type for t in tokens]
    assert TokenType.STRING in types
    assert TokenType.IDENTIFIER in types

    string_tok = next(t for t in tokens if t.type == TokenType.STRING)
    ident_tok = next(t for t in tokens if t.type == TokenType.IDENTIFIER)

    # Escape sequence resolved: internal apostrophe survives
    assert string_tok.value == "it's"
    # Adjacent decorated identifier unaffected
    assert ident_tok.value == "s'"

    # Generator round-trip: the apostrophe in the string value is not a special
    # LaTeX character, so the output contains it literally inside \text{`...'}.
    node = StringLit(value=string_tok.value, line=1, column=1)
    gen = LaTeXGenerator()
    result = gen.generate_expr(node)
    # The closing ' inside \text{`it's'} is from the Z string convention, not
    # an escape issue — LaTeX handles this correctly in text mode.
    assert result == r"\text{`it's'}"
