"""Regression tests: single-line GROUP must not emit a spurious line break.

A bare NEWLINE after a GROUP's closing ')' is just the end of the line —
it is not a continuation marker.  Treating it as one sets line_break_after=True
on the AST node and the codegen appends ' \\\\\n\\quad ' into inline math,
producing invalid LaTeX.

See: expressions.py GROUP branch, ~line 1936.
"""

from __future__ import annotations

from txt2tex.ast_nodes import Document, Expr, GroupAggregate
from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser
from txt2tex.tokens import Token

# ---------------------------------------------------------------------------
# Helpers (mirror the pattern in test_group_aggregators.py)
# ---------------------------------------------------------------------------


def _lex(src: str) -> list[Token]:
    return Lexer(src).tokenize()


def _expr(src: str) -> Expr:
    result = Parser(_lex(src)).parse()
    item: Expr = result.items[0] if isinstance(result, Document) else result  # type: ignore[assignment]
    return item


def _expr_latex(src: str) -> str:
    """Generate LaTeX for a standalone expression (no document wrapper)."""
    gen = LaTeXGenerator(use_fuzz=True)
    return gen.generate_expr(_expr(src))


def _doc_latex(src: str) -> str:
    """Generate the full document LaTeX for a complete document source."""
    tokens = Lexer(src).tokenize()
    ast = Parser(tokens).parse()
    return LaTeXGenerator().generate_document(ast)


# ---------------------------------------------------------------------------
# Bug: single-line group with trailing newline must NOT emit \\ or \quad
# ---------------------------------------------------------------------------


def test_single_line_group_aggregate_no_line_break() -> None:
    r"""R group (Sum(a) as b) followed by \n must not emit \\ or \quad.

    The trailing newline is a statement terminator, not a continuation.
    """
    src = "R group (Sum(a) as b)\n"
    result = _expr_latex(src)
    assert r"\mathop{\mathrm{Group}}" in result
    assert r"\\" not in result
    assert r"\quad" not in result


def test_abbreviation_group_aggregate_no_line_break_in_inline_math() -> None:
    r"""X == R group (Sum(a) as b) in a document must emit $…$ with no \\ inside.

    This is the exact reproduction case from the bug report.
    """
    src = "TITLE: probe\n\nX == R group (Sum(a) as b)\n"
    latex = _doc_latex(src)
    # The inline-math span must contain the Group operator
    assert r"$X == R \mathop{\mathrm{Group}}" in latex
    # A \\ inside inline math is invalid — must not appear
    assert r"\\" not in latex
    assert r"\quad" not in latex


def test_two_aggregate_single_line_no_line_break() -> None:
    r"""R group (Sum(a) as b, Sum(c) as d) on one line must not emit \\."""
    src = "R group (Sum(a) as b, Sum(c) as d)\n"
    result = _expr_latex(src)
    assert r"\mathop{\mathrm{Group}}" in result
    assert r"\\" not in result
    assert r"\quad" not in result


def test_regroup_form_single_line_no_line_break() -> None:
    r"""R group ({a, b} as g) on one line must not emit \\."""
    src = "R group ({a, b} as g)\n"
    result = _expr_latex(src)
    assert r"\mathop{\mathrm{GROUP}}" in result
    assert r"\\" not in result
    assert r"\quad" not in result


# ---------------------------------------------------------------------------
# AST: line_break_after must be False for plain single-line group
# ---------------------------------------------------------------------------


def test_single_line_group_aggregate_ast_no_line_break_flag() -> None:
    """Parsing a single-line group sets line_break_after=False on the AST node."""
    src = "R group (Sum(a) as b)\n"
    node = _expr(src)
    assert isinstance(node, GroupAggregate)
    assert node.line_break_after is False


# ---------------------------------------------------------------------------
# Regression: explicit CONTINUATION token after ) still sets the break
# ---------------------------------------------------------------------------


def test_explicit_continuation_after_group_still_breaks() -> None:
    r"""An explicit backslash continuation after GROUP's ')' still sets \\."""
    # Source: "R group (Sum(a) as b) \<newline>"  — the \ is the CONTINUATION token
    src = "R group (Sum(a) as b) \\\n"
    result = _expr_latex(src)
    assert r"\mathop{\mathrm{Group}}" in result
    assert r"\\" in result


def test_explicit_continuation_ast_line_break_flag_true() -> None:
    r"""Explicit \ continuation after GROUP sets line_break_after=True on the AST."""
    src = "R group (Sum(a) as b) \\\n"
    node = _expr(src)
    assert isinstance(node, GroupAggregate)
    assert node.line_break_after is True


# ---------------------------------------------------------------------------
# Non-group regressions: join and project are unaffected
# ---------------------------------------------------------------------------


def test_join_single_line_unaffected() -> None:
    r"""R join S on a single line: no spurious \\ added by this fix."""
    src = "R join S\n"
    result = _expr_latex(src)
    assert r"\mathrm{Join}" in result
    # A single-line join should not have a line break injected
    assert r"\\" not in result


def test_project_single_line_unaffected() -> None:
    r"""pi [a, b] R on a single line: no spurious \\ added by this fix."""
    src = "pi [a, b] R\n"
    result = _expr_latex(src)
    # Project emits \pi or \Pi; confirm no stray line break
    assert r"\\" not in result
