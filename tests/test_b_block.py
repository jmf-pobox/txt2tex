"""Tests for B: block (B-machine verbatim passthrough)."""

from __future__ import annotations

import pytest

from txt2tex.ast_nodes import BMachine, Document
from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer, LexerError
from txt2tex.parser import Parser


def _parse_and_generate(source: str) -> str:
    """Return the LaTeX output for source."""
    tokens = Lexer(source).tokenize()
    ast = Parser(tokens).parse()
    return LaTeXGenerator().generate_document(ast)


# ---------------------------------------------------------------------------
# AST structure tests
# ---------------------------------------------------------------------------


def test_minimal_b_machine_ast():
    """Minimal B machine produces a BMachine AST node with correct body."""
    source = "B:\nMACHINE Foo\nEND\n"
    tokens = Lexer(source).tokenize()
    ast = Parser(tokens).parse()
    assert isinstance(ast, Document)
    assert len(ast.items) == 1
    node = ast.items[0]
    assert isinstance(node, BMachine)
    assert node.body == "MACHINE Foo\nEND"


def test_minimal_b_machine_latex():
    """Minimal B machine emits a single verbatim block containing body lines."""
    source = "B:\nMACHINE Foo\nEND\n"
    latex = _parse_and_generate(source)
    assert r"\begin{verbatim}" in latex
    assert r"\end{verbatim}" in latex
    # Body inside verbatim — END is present
    assert "MACHINE Foo" in latex
    assert "END" in latex


def test_verbatim_wrapping_order():
    """\\begin{verbatim} appears before body, \\end{verbatim} after."""
    source = "B:\nMACHINE Foo\nEND\n"
    latex = _parse_and_generate(source)
    begin_pos = latex.index(r"\begin{verbatim}")
    end_pos = latex.index(r"\end{verbatim}")
    body_pos = latex.index("MACHINE Foo")
    assert begin_pos < body_pos < end_pos


# ---------------------------------------------------------------------------
# Multi-clause machine: indentation and blank lines preserved
# ---------------------------------------------------------------------------


def test_multi_clause_machine_preserves_indentation():
    """A full multi-clause machine preserves leading whitespace on each line."""
    source = (
        "B:\n"
        "MACHINE Trains\n"
        "SETS\n"
        "   PLACE\n"
        "VARIABLES\n"
        "   trains\n"
        "INVARIANT\n"
        "   trains : iseq(PLACE * PLACE)\n"
        "INITIALISATION\n"
        "   trains := []\n"
        "END\n"
    )
    latex = _parse_and_generate(source)
    # Three-space indent must be preserved verbatim
    assert "   PLACE" in latex
    assert "   trains" in latex
    assert "   trains : iseq(PLACE * PLACE)" in latex
    assert "   trains := []" in latex


def test_multi_clause_machine_no_double_spacing():
    """Body lines must not be separated by blank lines in the output."""
    source = "B:\nMACHINE Trains\nSETS\n   PLACE\nEND\n"
    latex = _parse_and_generate(source)
    # The body appears as a single contiguous string between the verbatim tags.
    begin_pos = latex.index(r"\begin{verbatim}")
    end_pos = latex.index(r"\end{verbatim}")
    body_region = latex[begin_pos:end_pos]
    # No double blank lines (which would indicate paragraph breaks)
    assert "\n\n\n" not in body_region


def test_blank_line_inside_body_preserved():
    """Blank lines inside the B body (before END) are passed through verbatim."""
    source = "B:\nMACHINE Foo\n\nSETS\n   X\nEND\n"
    tokens = Lexer(source).tokenize()
    ast = Parser(tokens).parse()
    assert isinstance(ast, Document)
    node = ast.items[0]
    assert isinstance(node, BMachine)
    # The body should contain the blank line between MACHINE and SETS
    assert "\n\nSETS" in node.body


def test_end_line_is_last_body_line():
    """The literal END line must be the last line inside the verbatim block."""
    source = "B:\nMACHINE Foo\nEND\n"
    latex = _parse_and_generate(source)
    begin_pos = latex.index(r"\begin{verbatim}")
    end_verb_pos = latex.index(r"\end{verbatim}")
    body_region = latex[begin_pos + len(r"\begin{verbatim}") : end_verb_pos].strip()
    assert body_region.endswith("END")


# ---------------------------------------------------------------------------
# Two independent B blocks in the same file
# ---------------------------------------------------------------------------


def test_two_b_blocks_independent():
    """Two B: blocks in one file each produce their own verbatim environment."""
    source = "B:\nMACHINE Alpha\nEND\n\nB:\nMACHINE Beta\nEND\n"
    tokens = Lexer(source).tokenize()
    ast = Parser(tokens).parse()
    assert isinstance(ast, Document)
    b_nodes = [item for item in ast.items if isinstance(item, BMachine)]
    assert len(b_nodes) == 2
    assert "Alpha" in b_nodes[0].body
    assert "Beta" in b_nodes[1].body

    latex = LaTeXGenerator().generate_document(ast)
    assert latex.count(r"\begin{verbatim}") == 2
    assert latex.count(r"\end{verbatim}") == 2


# ---------------------------------------------------------------------------
# Coexistence with surrounding TEXT prose
# ---------------------------------------------------------------------------


def test_b_block_surrounded_by_text_prose():
    """B block coexists with surrounding TEXT: prose paragraphs."""
    source = (
        "TEXT: Below is the B machine.\n"
        "\n"
        "B:\n"
        "MACHINE Foo\n"
        "END\n"
        "\n"
        "TEXT: Discussion below.\n"
    )
    tokens = Lexer(source).tokenize()
    ast = Parser(tokens).parse()
    assert isinstance(ast, Document)

    item_types = [type(item).__name__ for item in ast.items]
    assert "Paragraph" in item_types
    assert "BMachine" in item_types

    latex = _parse_and_generate(source)
    assert "Below is the B machine" in latex
    assert r"\begin{verbatim}" in latex
    assert "Discussion below" in latex


# ---------------------------------------------------------------------------
# Error case: missing END terminator
# ---------------------------------------------------------------------------


def test_missing_end_raises_lexer_error():
    """A B: block without a closing END raises LexerError citing the opener line."""
    source = "B:\nMACHINE Foo\nSETS\n   X\n"
    with pytest.raises(LexerError) as exc_info:
        Lexer(source).tokenize()
    # Error message must reference line 1 where B: was opened
    assert "1" in str(exc_info.value)
    assert "END" in str(exc_info.value)


def test_missing_end_at_eof_raises_lexer_error():
    """B: block at EOF with no newline after last line also raises LexerError."""
    source = "B:\nMACHINE Foo"  # No trailing newline, no END
    with pytest.raises(LexerError):
        Lexer(source).tokenize()


# ---------------------------------------------------------------------------
# Security: reject literal \end{verbatim} in body (djb 2026-05-22)
# ---------------------------------------------------------------------------


def test_body_with_literal_end_verbatim_is_rejected():
    """A B: body containing \\end{verbatim} would escape the verbatim env."""
    source = "B:\nMACHINE Demo\n\\end{verbatim}\n\\write18{anything}\nEND\n"
    with pytest.raises(LexerError) as exc_info:
        Lexer(source).tokenize()
    assert "\\end{verbatim}" in str(exc_info.value)
