"""Failing tests for the lambda paren-wrap gap.

Fuzz requires ``(\\lambda S @ E)`` around every lambda expression —
mirroring its ``(\\mu S @ E)`` requirement.  The generator currently
wraps only when ``parent is not None``, so lambdas as the RHS of ``==``
or inside certain container expressions are emitted bare and fuzz rejects
them with::

    Opening parenthesis expected at symbol \\lambda

Each failing test is marked ``xfail(strict=True)`` so CI stays green
while the bug is open but the test will *promote* to a pass once the
fix lands.  Tests 1, 2, 8, and 9 are controls — they already produce
wrapped output and must stay green.

Tests 1 and 2 replace the original invalid-Z bare-lambda paragraphs.
They exercise ``_generate_zed:4723`` (top-level predicate path) via a
Z-valid equality predicate whose RHS is a lambda.  BinaryOp threads
``parent=node``, so these currently pass — they are control tests
verifying the predicate path works end-to-end.

Pass/xfail summary:

+----+---------------------------------------------------+--------+
| T  | Construct                                         | Status |
+----+---------------------------------------------------+--------+
|  1 | ``f = lambda x : N . x + 1`` (zed predicate)     | PASS   |
|  2 | ``g = lambda x : N; y : N | x = y . x`` (zed)    | PASS   |
|  3 | ``f == lambda x : N . x + 1`` (zed abbreviation) | xfail  |
|  4 | ``g == lambda x : N; y : N | x = y . x`` (zed)   | xfail  |
|  5 | ``{lambda x : N . x + 1}`` (set literal)         | xfail  |
|  6 | nested lambda body (outer bare at top of zed)     | xfail  |
|  7 | fuzz round-trip: top-level lambda in zed          | xfail  |
|  8 | ``f = lambda`` in axdef where clause              | PASS   |
|  9 | lambda in quantifier body                         | PASS   |
| 10 | ``S == f(lambda x : N . x + 1)`` (func-app arg)  | xfail  |
| 11 | ``S == (lambda x : N . x + 1, 0)`` (tuple)       | xfail  |
| 12 | ``S == dom (lambda x : N . x + 1)`` (dom arg)    | xfail  |
| 13 | ``S == <lambda x : N . x + 1>`` (seq display)    | xfail  |
+----+---------------------------------------------------+--------+

Bug locations:

- ``latex_gen.py:1529`` — ``_generate_lambda``: ``parent is not None`` guard
- ``latex_gen.py:1356`` — ``_generate_lambda_quantifier``: same guard
- ``latex_gen.py:4704`` — ``_generate_zed``: no parent passed to abbreviation RHS
- ``latex_gen.py:4723`` — ``_generate_zed``: no parent passed to top-level predicates

The mu generator wraps unconditionally — that is the correct model.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from txt2tex.ast_nodes import Document
from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _gen(src: str) -> str:
    """Parse txt2tex source and return the full generated LaTeX document."""
    tokens = Lexer(src).tokenize()
    ast = Parser(tokens).parse()
    assert isinstance(ast, Document)
    return LaTeXGenerator(use_fuzz=True).generate_document(ast)


def _extract_env(tex: str, env: str) -> str:
    """Return the content between \\begin{env} and \\end{env} (inclusive)."""
    start_marker = rf"\begin{{{env}}}"
    end_marker = rf"\end{{{env}}}"
    start = tex.find(start_marker)
    end = tex.find(end_marker) + len(end_marker)
    assert start != -1, f"\\begin{{{env}}} not found in generated LaTeX"
    return tex[start:end]


def _fuzz_available() -> bool:
    """Return True if the fuzz binary is on PATH."""
    return shutil.which("fuzz") is not None


def _run_fuzz(tex: str, tmp_path: Path) -> subprocess.CompletedProcess[str]:
    """Write tex to a temp file and run fuzz on it; return the completed process."""
    fuzz_bin = shutil.which("fuzz")
    assert fuzz_bin is not None, "fuzz binary not found on PATH"
    tex_file = tmp_path / "test.tex"
    tex_file.write_text(tex, encoding="utf-8")
    return subprocess.run(  # noqa: S603
        [fuzz_bin, str(tex_file)],
        capture_output=True,
        text=True,
        check=False,
    )


# ---------------------------------------------------------------------------
# Control tests — T1 and T2 (pass, exercise _generate_zed:4723)
# ---------------------------------------------------------------------------
#
# These replace the original T1/T2 which used bare lambda at the top of a
# zed paragraph (invalid Z: lambda has type X -> Y, not predicate type).
# The replacement uses an equality predicate at top of zed, which is Z-valid
# (Z RM §3.10) and exercises the same _generate_zed:4723 code path.
# BinaryOp already threads parent=node, so the lambda IS wrapped — these
# are passing control tests that verify the predicate path works correctly.
#
# Actual output:
#   T1: \begin{zed}\nf = (\lambda x : \nat @ x + 1)\n\end{zed}
#   T2: \begin{zed}\ng = (\lambda x : \nat; y : \nat | x = y.x)\n\end{zed}


def test_single_decl_lambda_in_zed_equality_predicate_paren_wrapped() -> None:
    """Single-decl lambda as RHS of = predicate at top of zed is wrapped.

    Exercises ``_generate_zed:4723`` (top-level Expr path) via an equality
    predicate.  BinaryOp threads ``parent=node``, so the lambda is wrapped.
    This is Z-valid (Z RM §3.10 abbreviation and equality forms).

    Expected and actual: ``f = (\\lambda x : \\nat @ x + 1)``
    """
    src = "zed\n  f = lambda x : N . x + 1\nend"
    zed_block = _extract_env(_gen(src), "zed")
    assert r"f = (\lambda x : \nat @ x + 1)" in zed_block


def test_multi_decl_lambda_in_zed_equality_predicate_paren_wrapped() -> None:
    """Multi-decl lambda as RHS of = predicate at top of zed is wrapped.

    Exercises ``_generate_zed:4723`` with a multi-declaration lambda expression
    (Z RM §3.12, two bindings with ``|`` predicate).  BinaryOp threads
    ``parent=node``, so the enclosing lambda is wrapped.

    The outer ``=`` makes this a Z-valid predicate at the top of the zed
    paragraph.  The ``. x`` is the bullet separator followed by the body ``x``
    (Z RM §3.12); the parser now correctly emits ``x = y @ x``.

    Expected: ``h = (\\lambda x : \\nat; y : \\nat | x = y @ x)``
    """
    src = "zed\n  h = lambda x : N; y : N | x = y . x\nend"
    zed_block = _extract_env(_gen(src), "zed")
    assert r"h = (\lambda x : \nat; y : \nat | x = y @ x)" in zed_block


# ---------------------------------------------------------------------------
# Failing tests (xfail strict=True) — T3 through T7
# ---------------------------------------------------------------------------

# Actual output recorded at time of writing (2026-05-19):
#
#   T3: \begin{zed}\nf == \lambda x : \nat @ x + 1\n\end{zed}
#   T4: \begin{zed}\ng == \lambda x : \nat; y : \nat | x = y.x\n\end{zed}
#   T5: \begin{zed}\nfns == \{\lambda x : \nat @ x + 1\}\n\end{zed}
#   T6: \begin{zed}\n\lambda x : \nat @ \lambda y : \nat @ x + y\n\end{zed}


def test_lambda_rhs_of_abbreviation_paren_wrapped() -> None:
    """Lambda as the RHS of an abbreviation (==) must be wrapped in parens.

    Unconditional fuzz wrap in ``_generate_lambda`` covers this path regardless
    of ``parent``; ``_generate_zed`` does not need to thread a parent for the
    wrapping to take effect.

    Expected: ``f == (\\lambda x : \\nat @ x + 1)``
    """
    src = "zed\n  f == lambda x : N . x + 1\nend"
    zed_block = _extract_env(_gen(src), "zed")
    assert r"f == (\lambda x : \nat @ x + 1)" in zed_block


def test_multi_decl_lambda_rhs_of_abbreviation_paren_wrapped() -> None:
    """Multi-decl lambda as == RHS must be wrapped in parens.

    The ``. x`` is the bullet separator followed by body ``x`` (Z RM §3.12);
    the parser now correctly emits ``x = y @ x`` instead of ``x = y.x``.
    Unconditional fuzz wrap in ``_generate_lambda_quantifier`` covers this path.

    Expected: ``g == (\\lambda x : \\nat; y : \\nat | x = y @ x)``
    """
    src = "zed\n  g == lambda x : N; y : N | x = y . x\nend"
    zed_block = _extract_env(_gen(src), "zed")
    assert r"g == (\lambda x : \nat; y : \nat | x = y @ x)" in zed_block


def test_lambda_inside_set_paren_wrapped() -> None:
    """Lambda inside a set literal must be wrapped in parens.

    Expected: ``fns == \\{(\\lambda x : \\nat @ x + 1)\\}``
    """
    src = "zed\n  fns == {lambda x : N . x + 1}\nend"
    zed_block = _extract_env(_gen(src), "zed")
    assert r"fns == \{(\lambda x : \nat @ x + 1)\}" in zed_block


def test_lambda_inside_lambda_body_paren_wrapped() -> None:
    """Inner lambda in a nested lambda body must be wrapped in parens.

    In fuzz mode both the outer and the inner lambda must be wrapped:
    ``(\\lambda x : \\nat @ (\\lambda y : \\nat @ x + y))``
    """
    src = "zed\n  lambda x : N . lambda y : N . x + y\nend"
    zed_block = _extract_env(_gen(src), "zed")
    # Both the outer and inner must be wrapped
    assert r"(\lambda x : \nat @ (\lambda y : \nat @ x + y))" in zed_block


@pytest.mark.skipif(not _fuzz_available(), reason="fuzz binary not on PATH")
def test_fuzz_accepts_lambda_abbreviation(tmp_path: Path) -> None:
    """Fuzz accepts a parenthesized lambda as the RHS of an abbreviation.

    ``f == (\\lambda x : \\nat @ x + 1)`` is Z-valid (zed abbreviation form).
    This exercises the wrapping fix end-to-end via the fuzz type checker.
    """
    src = "zed\n  f == lambda x : N . x + 1\nend"
    full_tex = _gen(src)
    result = _run_fuzz(full_tex, tmp_path)
    assert result.returncode == 0, (
        f"fuzz rejected lambda abbreviation in zed block\n"
        f"tex:\n{full_tex}\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )


# ---------------------------------------------------------------------------
# Control tests — T8 and T9 (must currently PASS)
# ---------------------------------------------------------------------------


def test_lambda_rhs_of_equality_in_axdef_paren_wrapped() -> None:
    """Lambda as RHS of = in axdef where clause is correctly wrapped.

    This already passes: BinaryOp._generate_binary_op calls
    ``generate_expr(node.right, parent=node)`` so parent is not None.

    Expected and actual: ``f = (\\lambda x : \\nat @ x + 1)``
    """
    src = "axdef\n  f : N -> N\nwhere\n  f = lambda x : N . x + 1\nend"
    axdef_block = _extract_env(_gen(src), "axdef")
    assert r"f = (\lambda x : \nat @ x + 1)" in axdef_block


def test_lambda_inside_quantifier_paren_wrapped() -> None:
    """Lambda as RHS of = inside a quantifier body is correctly wrapped.

    The quantifier generator passes ``parent=node`` when generating
    sub-expressions, so the lambda sees a non-None parent and is wrapped.

    Input: ``forall f : N -> N | f = lambda x : N . x + 1``
    The = sub-expression passes parent down to the lambda.
    """
    src = (
        "axdef\n  f : N -> N\nwhere\n"
        "  forall g : N -> N | g = lambda x : N . x + 1\nend"
    )
    axdef_block = _extract_env(_gen(src), "axdef")
    assert r"(\lambda x : \nat @ x + 1)" in axdef_block


# ---------------------------------------------------------------------------
# Coverage gap tests — T10 through T13 (xfail strict=True)
# ---------------------------------------------------------------------------
#
# All four are Z-valid contexts for lambda expressions.  All currently emit
# bare ``\lambda`` because the relevant generator does not pass parent=node.
#
# Actual output recorded at time of writing (2026-05-19):
#
#   T10: \begin{zed}\nS == f(\lambda x : \nat @ x + 1)\n\end{zed}
#   T11: \begin{zed}\nS == (\lambda x : \nat @ x + 1, 0)\n\end{zed}
#   T12: \begin{zed}\nS == \dom \lambda x : \nat @ x + 1\n\end{zed}
#   T13: \begin{zed}\nS == \langle \lambda x : \nat @ x + 1 \rangle\n\end{zed}


def test_lambda_as_function_argument_paren_wrapped() -> None:
    """Lambda passed as argument to a function must be wrapped in parens.

    Expected: ``S == f((\\lambda x : \\nat @ x + 1))``
    """
    src = "zed\n  S == f (lambda x : N . x + 1)\nend"
    zed_block = _extract_env(_gen(src), "zed")
    assert r"S == f((\lambda x : \nat @ x + 1))" in zed_block


def test_lambda_in_tuple_paren_wrapped() -> None:
    """Lambda as first component of a tuple must be wrapped in parens.

    Expected: ``S == ((\\lambda x : \\nat @ x + 1), 0)``
    """
    src = "zed\n  S == (lambda x : N . x + 1, 0)\nend"
    zed_block = _extract_env(_gen(src), "zed")
    assert r"S == ((\lambda x : \nat @ x + 1), 0)" in zed_block


def test_lambda_in_dom_application_paren_wrapped() -> None:
    r"""Lambda as argument to ``\dom`` must be wrapped in parens.

    Expected: ``S == \\dom (\\lambda x : \\nat @ x + 1)``
    """
    src = "zed\n  S == dom (lambda x : N . x + 1)\nend"
    zed_block = _extract_env(_gen(src), "zed")
    assert r"S == \dom (\lambda x : \nat @ x + 1)" in zed_block


def test_lambda_in_sequence_display_paren_wrapped() -> None:
    r"""Lambda inside a sequence display ``\langle ... \rangle`` must be wrapped.

    Expected: ``S == \\langle (\\lambda x : \\nat @ x + 1) \\rangle``
    """
    src = "zed\n  S == <lambda x : N . x + 1>\nend"
    zed_block = _extract_env(_gen(src), "zed")
    assert r"S == \langle (\lambda x : \nat @ x + 1) \rangle" in zed_block
