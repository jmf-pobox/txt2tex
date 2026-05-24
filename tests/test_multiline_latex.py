"""Tests for multi-line LATEX: block (LATEX:\\n...END verbatim passthrough)."""

from __future__ import annotations

import pytest

from txt2tex.ast_nodes import Document, LatexBlock, RawLatexBlock
from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer, LexerError
from txt2tex.parser import Parser


def _parse_and_generate(source: str) -> str:
    """Return the LaTeX output for source."""
    tokens = Lexer(source).tokenize()
    ast = Parser(tokens).parse()
    return LaTeXGenerator().generate_document(ast)


# ---------------------------------------------------------------------------
# Test 1: Basic multi-line block emits body verbatim
# ---------------------------------------------------------------------------


def test_basic_multiline_block_emits_body_verbatim():
    """Basic multi-line block emits body lines verbatim with no wrapping."""
    source = "LATEX:\n\\begin{center}\n  hello\n\\end{center}\nEND\n"
    tokens = Lexer(source).tokenize()
    ast = Parser(tokens).parse()
    assert isinstance(ast, Document)
    assert len(ast.items) == 1
    node = ast.items[0]
    assert isinstance(node, RawLatexBlock)
    assert node.body == "\\begin{center}\n  hello\n\\end{center}"

    latex = LaTeXGenerator().generate_document(ast)
    assert "\\begin{center}" in latex
    assert "  hello" in latex
    assert "\\end{center}" in latex
    # Must NOT wrap in verbatim environment
    assert "\\begin{verbatim}" not in latex


# ---------------------------------------------------------------------------
# Test 2: Leading whitespace preserved
# ---------------------------------------------------------------------------


def test_leading_whitespace_preserved():
    """Two-space indent in body appears unchanged in output."""
    source = "LATEX:\n  \\indented{line}\nEND\n"
    tokens = Lexer(source).tokenize()
    ast = Parser(tokens).parse()
    assert isinstance(ast, Document)
    node = ast.items[0]
    assert isinstance(node, RawLatexBlock)
    assert node.body == "  \\indented{line}"

    latex = _parse_and_generate(source)
    assert "  \\indented{line}" in latex


# ---------------------------------------------------------------------------
# Test 3: Internal blank lines preserved
# ---------------------------------------------------------------------------


def test_internal_blank_lines_preserved():
    """Blank lines inside the block body pass through to the AST and output."""
    source = "LATEX:\nfirst\n\nsecond\nEND\n"
    tokens = Lexer(source).tokenize()
    ast = Parser(tokens).parse()
    assert isinstance(ast, Document)
    node = ast.items[0]
    assert isinstance(node, RawLatexBlock)
    assert "\n\n" in node.body  # blank line preserved as two consecutive newlines

    latex = _parse_and_generate(source)
    assert "first\n\nsecond" in latex


# ---------------------------------------------------------------------------
# Test 4: Single-line LATEX: foo still works (regression)
# ---------------------------------------------------------------------------


def test_single_line_latex_still_works():
    """Existing single-line LATEX: content form is unaffected."""
    source = "LATEX: \\textbf{hello}\n"
    tokens = Lexer(source).tokenize()
    ast = Parser(tokens).parse()
    assert isinstance(ast, Document)
    node = ast.items[0]
    assert isinstance(node, LatexBlock)
    assert node.latex == "\\textbf{hello}"

    latex = _parse_and_generate(source)
    assert "\\textbf{hello}" in latex


# ---------------------------------------------------------------------------
# Test 5: Mixed single-line and multi-line in the same file
# ---------------------------------------------------------------------------


def test_mixed_single_and_multiline():
    """Single-line LATEX: and multi-line LATEX: block coexist correctly."""
    source = (
        "LATEX: \\noindent first line\n"
        "\n"
        "LATEX:\n"
        "\\begin{center}\n"
        "  body\n"
        "\\end{center}\n"
        "END\n"
    )
    tokens = Lexer(source).tokenize()
    ast = Parser(tokens).parse()
    assert isinstance(ast, Document)

    latex_nodes = [item for item in ast.items if isinstance(item, LatexBlock)]
    raw_nodes = [item for item in ast.items if isinstance(item, RawLatexBlock)]
    assert len(latex_nodes) == 1
    assert len(raw_nodes) == 1

    latex = _parse_and_generate(source)
    assert "\\noindent first line" in latex
    assert "\\begin{center}" in latex
    assert "  body" in latex


# ---------------------------------------------------------------------------
# Test 6: Unclosed block raises LexerError citing opener line
# ---------------------------------------------------------------------------


def test_unclosed_block_raises_lexer_error():
    """A LATEX: block with no closing END raises LexerError at the opener line."""
    source = "LATEX:\n\\begin{center}\n  body\n\\end{center}\n"
    with pytest.raises(LexerError) as exc_info:
        Lexer(source).tokenize()
    err = str(exc_info.value)
    # Must reference line 1 (where LATEX: was opened)
    assert "1" in err
    assert "END" in err


# ---------------------------------------------------------------------------
# Test 7: \\end{center} inside body does NOT close the block prematurely
# ---------------------------------------------------------------------------


def test_end_latex_env_inside_body_does_not_terminate():
    """\\end{center} in the body is not the column-0 END terminator."""
    source = "LATEX:\n\\begin{center}\n  text\n\\end{center}\nEND\n"
    tokens = Lexer(source).tokenize()
    ast = Parser(tokens).parse()
    assert isinstance(ast, Document)
    node = ast.items[0]
    assert isinstance(node, RawLatexBlock)
    # All four body lines must be present
    assert "\\begin{center}" in node.body
    assert "  text" in node.body
    assert "\\end{center}" in node.body


# ---------------------------------------------------------------------------
# Test 8: Empty body (LATEX:\nEND\n) emits a blank line
# ---------------------------------------------------------------------------


def test_empty_body_emits_blank():
    """Empty LATEX: block (LATEX:\\nEND\\n) produces only the trailing blank line."""
    source = "LATEX:\nEND\n"
    tokens = Lexer(source).tokenize()
    ast = Parser(tokens).parse()
    assert isinstance(ast, Document)
    node = ast.items[0]
    assert isinstance(node, RawLatexBlock)
    assert node.body == ""

    latex = _parse_and_generate(source)
    # Generator emits one trailing blank line for an empty body; no verbatim wrapping.
    assert "\\begin{verbatim}" not in latex


# ---------------------------------------------------------------------------
# Test 9: LATEX: with trailing whitespace before newline is multi-line
# ---------------------------------------------------------------------------


def test_trailing_whitespace_after_colon_is_multiline():
    """LATEX:    \\n (trailing spaces) is still recognised as multi-line opener."""
    source = "LATEX:    \n\\custom{cmd}\nEND\n"
    tokens = Lexer(source).tokenize()
    ast = Parser(tokens).parse()
    assert isinstance(ast, Document)
    node = ast.items[0]
    assert isinstance(node, RawLatexBlock)
    assert node.body == "\\custom{cmd}"
