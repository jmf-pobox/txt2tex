"""Tests for CODE: block (general verbatim code fence).

CODE: shares its lexing, AST node (BMachine), and rendering with B:, the
B-machine verbatim block. The one behavioral difference: B:'s terminating
END is B-Method's own keyword and is rendered; CODE:'s terminating END is
a pure delimiter and is consumed, never rendered. See lexer.py's shared
`_scan_verbatim_block` helper.
"""

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
# Terminating END is consumed, not rendered
# ---------------------------------------------------------------------------


def test_code_block_end_terminator_consumed() -> None:
    """The bare CODE: terminator is dropped from the rendered verbatim body."""
    source = "CODE:\nSELECT 1;\nEND;\nEND\n"
    latex = _parse_and_generate(source)
    begin_pos = latex.index(r"\begin{verbatim}")
    end_pos = latex.index(r"\end{verbatim}")
    body_lines = (
        latex[begin_pos + len(r"\begin{verbatim}") : end_pos].strip("\n").splitlines()
    )
    assert body_lines == ["SELECT 1;", "END;"]


def test_code_block_full_rendered_latex() -> None:
    """Exact rendered LaTeX for a minimal SQL CODE: block."""
    source = "CODE:\nSELECT 1;\nEND;\nEND\n"
    latex = _parse_and_generate(source)
    begin_pos = latex.index(r"\begin{verbatim}")
    end_pos = latex.index(r"\end{verbatim}") + len(r"\end{verbatim}")
    rendered = latex[begin_pos:end_pos]
    assert rendered == "\\begin{verbatim}\nSELECT 1;\nEND;\n\\end{verbatim}"


def test_code_block_ast_body_excludes_terminator() -> None:
    """The BMachine AST body for a CODE: block excludes the bare END line."""
    source = "CODE:\nSELECT 1;\nEND;\nEND\n"
    tokens = Lexer(source).tokenize()
    ast = Parser(tokens).parse()
    assert isinstance(ast, Document)
    node = ast.items[0]
    assert isinstance(node, BMachine)
    assert node.body == "SELECT 1;\nEND;"


# ---------------------------------------------------------------------------
# Lines merely starting with END are code, not terminators
# ---------------------------------------------------------------------------


def test_end_if_and_end_loop_preserved_inside_code_block() -> None:
    """END IF; and END LOOP; are PL/pgSQL code, not CODE: terminators."""
    source = "CODE:\nBEGIN\n  IF x > 0 THEN\n    NULL;\n  END IF;\nEND LOOP;\nEND\n"
    latex = _parse_and_generate(source)
    assert "END IF;" in latex
    assert "END LOOP;" in latex
    # Only one closing \end{verbatim} — the bare terminator was consumed,
    # not left behind as trailing body text.
    assert latex.count(r"\end{verbatim}") == 1


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------


def test_code_block_missing_end_raises_lexer_error_naming_code() -> None:
    """A CODE: block without a closing END raises LexerError naming CODE:."""
    source = "CODE:\nSELECT 1;\n"
    with pytest.raises(LexerError) as exc_info:
        Lexer(source).tokenize()
    assert "CODE:" in str(exc_info.value)
    assert "1" in str(exc_info.value)
    assert "END" in str(exc_info.value)


def test_code_block_with_literal_end_verbatim_is_rejected() -> None:
    """A CODE: body containing \\end{verbatim} would escape the verbatim env."""
    source = "CODE:\nSELECT 1;\n\\end{verbatim}\n\\write18{anything}\nEND\n"
    with pytest.raises(LexerError) as exc_info:
        Lexer(source).tokenize()
    assert "\\end{verbatim}" in str(exc_info.value)
    assert "CODE:" in str(exc_info.value)


# ---------------------------------------------------------------------------
# Regression guard: B: is unaffected by the shared-helper refactor
# ---------------------------------------------------------------------------


def test_b_block_end_terminator_still_rendered() -> None:
    """B: keeps rendering its terminating END — CODE:'s behavior must not leak."""
    source = "B:\nMACHINE Foo\nEND\n"
    latex = _parse_and_generate(source)
    begin_pos = latex.index(r"\begin{verbatim}")
    end_pos = latex.index(r"\end{verbatim}")
    body_region = latex[begin_pos + len(r"\begin{verbatim}") : end_pos].strip()
    assert body_region.endswith("END")
