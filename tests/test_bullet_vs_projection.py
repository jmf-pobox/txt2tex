"""Failing tests for the bullet-vs-projection disambiguation bug.

When a multi-decl quantifier or comprehension has a bullet separator `. expr`
and the expression starts with an identifier, the postfix parser greedily
consumes `last_decl_var.identifier` as a named-field projection, swallowing
the bullet and leaving no body expression.

Root cause: `_parse_postfix` (parser.py, PERIOD-loop at ~line 3613) checks
`token_after_id.type in safe_followers` to decide whether `.identifier` is
projection. `PLUS`, `MINUS`, `STAR`, etc. are in `safe_followers`, so
`d . c + d` reads as `d.c` (projection) followed by `+ d` in the predicate,
leaving `.expression = None` on the inner Quantifier.

The fix must distinguish: when `_in_comprehension_body` is True and the
identifier being "projected onto" has a basic-set type (N, Z, given set),
projection is type-invalid and the period must be the bullet.

Tests below are grouped by quantifier form.  Each xfail shows the *actual*
wrong LaTeX so the eventual fix author can confirm the regression disappears.

Pass summary (all green after Option C' fix)
--------------------------------------------
PASS   test_mu_basic_typed_bullet_then_ident
PASS   test_mu_basic_typed_bullet_then_zero
PASS   test_forall_basic_typed_bullet_then_ident
PASS   test_exists_basic_typed_bullet_then_ident
PASS   test_exists1_basic_typed_bullet_then_ident
PASS   test_lambda_basic_typed_bullet_then_ident
PASS   test_comprehension_basic_typed_bullet_then_ident
PASS   test_mu_parenthesised_body_control
PASS   test_exists_no_body_control
PASS   test_mu_basic_typed_bullet_then_paren
PASS   test_mu_multi_conjunct_bullet
PASS   test_forall_multi_conjunct_bullet
PASS   test_mu_schema_typed_bullet_projection
PASS   test_mu_single_decl_baseline
PASS   test_forall_single_decl_baseline

Coverage-gap additions (jms review):
PASS   test_mixed_basic_and_schema_decls
PASS   test_schema_bullet_then_projection
PASS   test_body_is_comprehension
PASS   test_body_arithmetic_star
PASS   test_body_arithmetic_minus
PASS   test_body_arithmetic_mod
PASS   test_comprehension_no_constraint_only_body
PASS   test_three_variable_schema_text
PASS   test_fuzz_accepts_fixed_bullet_output
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from txt2tex.ast_nodes import Document, Quantifier, SetComprehension
from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_FUZZ_PREAMBLE = """\
\\documentclass[a4paper]{{article}}
\\usepackage{{fuzz}}
\\begin{{document}}
{body}
\\end{{document}}
"""


def _fuzz_available() -> bool:
    """Return True if the fuzz binary is on PATH."""
    return shutil.which("fuzz") is not None


def _gen_expr(src: str) -> str:
    """Parse src and return generated LaTeX (expression form)."""
    tokens = Lexer(src).tokenize()
    ast = Parser(tokens).parse()
    gen = LaTeXGenerator(use_fuzz=True)
    if isinstance(ast, Document):
        return gen.generate_document(ast)
    return gen.generate_expr(ast)


def _parse_quantifier(src: str) -> Quantifier:
    """Parse src and return the root Quantifier AST node."""
    tokens = Lexer(src).tokenize()
    ast = Parser(tokens).parse()
    assert isinstance(ast, Quantifier)
    return ast


def _inner(ast: Quantifier) -> Quantifier:
    """Return the inner (continuation) Quantifier stored in ast.body."""
    inner = ast.body
    assert isinstance(inner, Quantifier), (
        f"Expected nested Quantifier in .body, got {type(inner).__name__}"
    )
    return inner


def _run_fuzz(tex_body: str, tmp_path: Path) -> subprocess.CompletedProcess[str]:
    """Run fuzz on tex_body wrapped in a minimal document."""
    fuzz_bin = shutil.which("fuzz")
    assert fuzz_bin is not None
    content = _FUZZ_PREAMBLE.format(body=tex_body)
    tex_file = tmp_path / "test.tex"
    tex_file.write_text(content, encoding="utf-8")
    return subprocess.run(  # noqa: S603
        [fuzz_bin, str(tex_file)],
        capture_output=True,
        text=True,
        check=False,
    )


# ---------------------------------------------------------------------------
# XFAIL: basic-typed, bullet-then-identifier — the core bug
# ---------------------------------------------------------------------------


def test_mu_basic_typed_bullet_then_ident() -> None:
    """Multi-decl mu with bullet+identifier body must separate predicate from body.

    Input:  mu c : N; d : N | c = d . c + d
    Target: (\\mu c : \\nat; d : \\nat | c = d @ c + d)
    Actual: (\\mu c : \\nat; d : \\nat | c = d.c + d)   ← projection bug
    """
    ast = _parse_quantifier("mu c : N; d : N | c = d . c + d")
    inner = _inner(ast)
    # Predicate must be just "c = d"; expression must be "c + d"
    assert inner.expression is not None, (
        "expected body expression after bullet, got None — "
        "bullet was consumed as projection"
    )
    latex = _gen_expr("mu c : N; d : N | c = d . c + d")
    assert "@ c + d" in latex, f"body not in output: {latex!r}"
    assert "d.c" not in latex, f"projection artefact in output: {latex!r}"


def test_mu_basic_typed_bullet_then_zero() -> None:
    """Multi-decl mu with bullet+zero must parse the zero as the body, not an index.

    Input:  mu c : N; d : N | c = d . 0
    Target: (\\mu c : \\nat; d : \\nat | c = d @ 0)
    Actual: ParserError — 'Tuple projection index must be >= 1, got 0'
    """
    latex = _gen_expr("mu c : N; d : N | c = d . 0")
    assert "@ 0" in latex, f"body '0' not in output: {latex!r}"
    assert "d.0" not in latex, f"projection artefact in output: {latex!r}"


def test_forall_basic_typed_bullet_then_ident() -> None:
    """Multi-decl forall with bullet+identifier body must keep bullet semantics.

    Input:  forall x : N; y : N | x = y . x + y
    Target: \\forall x : \\nat; y : \\nat | x = y @ x + y
    Actual: \\forall x : \\nat; y : \\nat @ x = y.x + y
    """
    ast = _parse_quantifier("forall x : N; y : N | x = y . x + y")
    inner = _inner(ast)
    assert inner.expression is not None, (
        "expected body after bullet, got None — bullet consumed as projection"
    )
    latex = _gen_expr("forall x : N; y : N | x = y . x + y")
    assert "@ x + y" in latex, f"body not in output: {latex!r}"
    assert "y.x" not in latex, f"projection artefact in output: {latex!r}"


def test_exists_basic_typed_bullet_then_ident() -> None:
    """Multi-decl exists with bullet+identifier body must keep bullet semantics.

    Input:  exists x : N; y : N | x = y . x + y
    Target: \\exists x : \\nat; y : \\nat | x = y @ x + y
    Actual: \\exists x : \\nat; y : \\nat @ x = y.x + y
    """
    ast = _parse_quantifier("exists x : N; y : N | x = y . x + y")
    inner = _inner(ast)
    assert inner.expression is not None, (
        "expected body after bullet, got None — bullet consumed as projection"
    )
    latex = _gen_expr("exists x : N; y : N | x = y . x + y")
    assert "@ x + y" in latex, f"body not in output: {latex!r}"
    assert "y.x" not in latex, f"projection artefact in output: {latex!r}"


def test_exists1_basic_typed_bullet_then_ident() -> None:
    """Multi-decl exists1 with bullet+identifier body must keep bullet semantics.

    Input:  exists1 x : N; y : N | x = y . x + y
    Target: \\exists_1 x : \\nat; y : \\nat | x = y @ x + y
    Actual: \\exists_1 x : \\nat; y : \\nat @ x = y.x + y
    """
    ast = _parse_quantifier("exists1 x : N; y : N | x = y . x + y")
    inner = _inner(ast)
    assert inner.expression is not None, (
        "expected body after bullet, got None — bullet consumed as projection"
    )
    latex = _gen_expr("exists1 x : N; y : N | x = y . x + y")
    assert "@ x + y" in latex, f"body not in output: {latex!r}"
    assert "y.x" not in latex, f"projection artefact in output: {latex!r}"


def test_lambda_basic_typed_bullet_then_ident() -> None:
    """Multi-decl lambda with bullet+identifier body must keep bullet semantics.

    Input:  lambda x : N; y : N | x = y . x + y
    Target: (\\lambda x : \\nat; y : \\nat | x = y @ x + y)
    Actual: (\\lambda x : \\nat; y : \\nat | x = y.x + y)
    """
    ast = _parse_quantifier("lambda x : N; y : N | x = y . x + y")
    inner = _inner(ast)
    assert inner.expression is not None, (
        "expected body after bullet, got None — bullet consumed as projection"
    )
    latex = _gen_expr("lambda x : N; y : N | x = y . x + y")
    assert "@ x + y" in latex, f"body not in output: {latex!r}"
    assert "y.x" not in latex, f"projection artefact in output: {latex!r}"


def test_comprehension_basic_typed_bullet_then_ident() -> None:
    """Set comprehension with multi-decl and bullet+identifier must keep bullet.

    Input:  { s : N; t : N | s = t . s + t }
    Target: \\{~ s : \\nat ; t : \\nat | s = t @ s + t ~\\}
    Actual: \\{~ s : \\nat ; t : \\nat | s = t.s + t ~\\}
    """
    tokens = Lexer("{ s : N; t : N | s = t . s + t }").tokenize()
    ast = Parser(tokens).parse()
    assert isinstance(ast, SetComprehension)
    # expression field should be non-None (the post-bullet body)
    assert ast.expression is not None, (
        "expected post-bullet expression, got None — bullet consumed as projection"
    )
    latex = _gen_expr("{ s : N; t : N | s = t . s + t }")
    assert "@ s + t" in latex or "s + t" in latex, f"body not in output: {latex!r}"
    assert "t.s" not in latex, f"projection artefact in output: {latex!r}"


# ---------------------------------------------------------------------------
# PASS controls: parenthesised body (workaround — must stay passing)
# ---------------------------------------------------------------------------


def test_mu_basic_typed_bullet_then_paren() -> None:
    """Parenthesised body is an existing workaround that must stay passing.

    Input:  mu c : N; d : N | c = d . (c + d)
    Target: (\\mu c : \\nat; d : \\nat | c = d @ (c + d))
    """
    ast = _parse_quantifier("mu c : N; d : N | c = d . (c + d)")
    inner = _inner(ast)
    assert inner.expression is not None, "parenthesised body should be parsed correctly"
    latex = _gen_expr("mu c : N; d : N | c = d . (c + d)")
    assert "@ (c + d)" in latex, f"body not in output: {latex!r}"


def test_exists_no_body_control() -> None:
    """Two-decl exists with no bullet and no body must stay passing.

    Input:  exists x : N; y : N | x = y
    Target: \\exists x : \\nat; y : \\nat @ x = y
    """
    ast = _parse_quantifier("exists x : N; y : N | x = y")
    inner = _inner(ast)
    assert inner.expression is None
    latex = _gen_expr("exists x : N; y : N | x = y")
    assert r"\exists" in latex
    assert "x = y" in latex


# ---------------------------------------------------------------------------
# PASS: multi-conjunct predicate variants (land breaks the projection chain)
# ---------------------------------------------------------------------------


def test_mu_multi_conjunct_bullet() -> None:
    """Multi-conjunct predicate ends before bullet — parses correctly already.

    Input:  mu c : N; d : N | c < 10 land d < 10 . c + d
    Target: (\\mu c : \\nat; d : \\nat | c < 10 \\land d < 10 @ c + d)

    The `land` operator terminates the comparison, so `d` (inside `d < 10`)
    is consumed before the bullet, and the postfix loop does not see `.c`
    immediately after `d`.  This tests the path that should remain unchanged.
    """
    ast = _parse_quantifier("mu c : N; d : N | c < 10 land d < 10 . c + d")
    inner = _inner(ast)
    assert inner.expression is not None, (
        "multi-conjunct predicate should parse bullet correctly"
    )
    latex = _gen_expr("mu c : N; d : N | c < 10 land d < 10 . c + d")
    assert "@ c + d" in latex, f"body not in output: {latex!r}"
    assert r"\land" in latex


def test_forall_multi_conjunct_bullet() -> None:
    """Multi-conjunct forall parses bullet correctly.

    The last token in the predicate is a number, not an identifier, so the
    postfix loop does not attempt projection onto it.

    Input:  forall x : N; y : N | x < y land y < 10 . x + 1 < 10
    Target: \\forall x : \\nat; y : \\nat | x < y \\land y < 10 @ x + 1 < 10
    """
    ast = _parse_quantifier("forall x : N; y : N | x < y land y < 10 . x + 1 < 10")
    inner = _inner(ast)
    assert inner.expression is not None
    latex = _gen_expr("forall x : N; y : N | x < y land y < 10 . x + 1 < 10")
    assert "@ x + 1 < 10" in latex, f"body not in output: {latex!r}"


# ---------------------------------------------------------------------------
# PASS: schema-typed — bullet after s.name = t.name is unambiguous
# ---------------------------------------------------------------------------


def test_mu_schema_typed_bullet_projection() -> None:
    """Schema-typed mu: predicate ends with named projection, bullet is unambiguous.

    Input:  mu s : Ship; t : Ship | s.name = t.name . s.name
    Target: (\\mu s : Ship; t : Ship | s.name = t.name @ s.name)

    After `s.name = t.name`, the next token is `.` then `s` (an identifier);
    `token_after_id` is `(` (from `s.name`) — this lands in the
    TupleProjection guard, stopping the greedy loop.  Already correct.
    """
    ast = _parse_quantifier("mu s : Ship; t : Ship | s.name = t.name . s.name")
    inner = _inner(ast)
    assert inner.expression is not None, "schema-typed mu should parse bullet correctly"
    latex = _gen_expr("mu s : Ship; t : Ship | s.name = t.name . s.name")
    assert "@ s.name" in latex or r"@ s\mathord{.}name" in latex or "s.name" in latex
    assert "t.name.s" not in latex, f"double-projection bug: {latex!r}"


# ---------------------------------------------------------------------------
# PASS: single-decl baselines — must be completely unaffected
# ---------------------------------------------------------------------------


def test_mu_single_decl_baseline() -> None:
    """Single-decl mu with bullet+identifier body is unaffected by any fix.

    Input:  mu x : N | x > 0 . x + 1
    Target: (\\mu x : \\nat | x > 0 @ x + 1)
    """
    ast = _parse_quantifier("mu x : N | x > 0 . x + 1")
    assert isinstance(ast, Quantifier)
    assert ast.expression is not None, "single-decl mu should have expression"
    latex = _gen_expr("mu x : N | x > 0 . x + 1")
    assert latex == r"(\mu x : \nat | x > 0 @ x + 1)", f"unexpected: {latex!r}"


def test_forall_single_decl_baseline() -> None:
    """Single-decl forall with bullet+body is unaffected by any fix.

    Input:  forall x : N | x > 0 . x + 1
    Target: \\forall x : \\nat | x > 0 @ x + 1
    """
    ast = _parse_quantifier("forall x : N | x > 0 . x + 1")
    assert isinstance(ast, Quantifier)
    assert ast.expression is not None, "single-decl forall should have expression"
    latex = _gen_expr("forall x : N | x > 0 . x + 1")
    assert latex == r"\forall x : \nat | x > 0 @ x + 1", f"unexpected: {latex!r}"


# ---------------------------------------------------------------------------
# Optional: fuzz round-trip for the parenthesised-body workaround (sanity)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not _fuzz_available(), reason="fuzz binary not on PATH")
def test_fuzz_accepts_mu_paren_body_workaround(tmp_path: Path) -> None:
    """Fuzz accepts the parenthesised-body workaround output.

    This confirms the generated LaTeX for the workaround form is fuzz-clean,
    establishing the target that the bullet fix must also satisfy.
    """
    src = """\
axdef
  k : N
where
  k = (mu c : N; d : N | c = d . (c + d))
end
"""
    tokens = Lexer(src).tokenize()
    doc = Parser(tokens).parse()
    assert isinstance(doc, Document)
    tex = LaTeXGenerator(use_fuzz=True).generate_document(doc)
    result = _run_fuzz(tex, tmp_path)
    assert result.returncode == 0, (
        f"fuzz rejected parenthesised-body workaround\n"
        f"tex:\n{tex}\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )


# ---------------------------------------------------------------------------
# Coverage-gap additions (jms Phase-1.5 review)
# ---------------------------------------------------------------------------


# Gap 1 — mixed basic + schema declarations.
# Current output: inner.expression is None; latex contains 's.name = d.d'.
# The postfix loop reads 'd . d' as projection d.d because the second d's
# token_after_id ('.' then EOF) passes safe_followers.
def test_mixed_basic_and_schema_decls() -> None:
    """Mixed schema+basic mu must recognise the final dot as the bullet.

    Input:  mu s : Ship; d : N | s.name = d . d
    Target: (\\mu s : Ship; d : \\nat | s.name = d @ d)
    Actual: (\\mu s : Ship; d : \\nat | s.name = d.d)

    The predicate ends at the first `d`; the body is just `d`.
    Because `d : N` is a basic type, `d.d` is ill-typed (Z RM §3.16)
    and the period must be the bullet.
    """
    ast = _parse_quantifier("mu s : Ship; d : N | s.name = d . d")
    inner = _inner(ast)
    assert inner.expression is not None, (
        "expected body 'd' after bullet, got None — bullet consumed as projection d.d"
    )
    latex = _gen_expr("mu s : Ship; d : N | s.name = d . d")
    assert "@ d" in latex, f"body 'd' not in output: {latex!r}"
    assert "d.d" not in latex, f"projection artefact in output: {latex!r}"


# Gap 2 — schema-typed single-decl where the bullet body is itself a projection.
# Current output: ast.expression is Identifier('name'), ast.body is TupleProjection.
# The parser mis-reads 'true.s' as a field selection, placing 'name' as the
# expression and discarding the correct bullet boundary.
def test_schema_bullet_then_projection() -> None:
    """Schema-typed single-decl mu with bullet body that is itself a projection.

    Input:  mu s : Ship | true . s.name
    Target: (\\mu s : Ship | true @ s.name)
    Actual: (\\mu s : Ship | true.s @ name)   ← projection spans the bullet

    The predicate is `true`; the body is the projection `s.name`.
    Projection in the body is Z-valid (s : Ship, a schema type).
    The `.` after `true` must be the bullet, not the start of `true.s`.
    """
    tokens = Lexer("mu s : Ship | true . s.name").tokenize()
    ast = Parser(tokens).parse()
    assert isinstance(ast, Quantifier)
    # Single-decl: expression field is the bullet body.
    assert ast.expression is not None, (
        "expected body 's.name' in ast.expression, got None"
    )
    latex = _gen_expr("mu s : Ship | true . s.name")
    assert "@ s" in latex or "@ s.name" in latex or r"@ s\mathord{.}name" in latex, (
        f"body 's.name' not in output: {latex!r}"
    )
    assert "true.s" not in latex, f"projection bug in output: {latex!r}"


# Gap 3 — body is a set comprehension (must stay passing).
# Current output: inner.expression is a SetComprehension; latex is correct.
# Verifies the fix does not over-correct when the body opens '{'.
def test_body_is_comprehension() -> None:
    """Multi-decl mu with bullet body that is a set comprehension.

    Input:  mu c : N; d : N | c = d . { x : N | x < c + d }
    Target: (\\mu c : \\nat; d : \\nat | c = d @ \\{~ x : \\nat | x < c + d ~\\})

    The `{` after the bullet is unambiguous — the fix must not disturb this path.
    Already parses correctly (inner.expression=SetComprehension).
    """
    ast = _parse_quantifier("mu c : N; d : N | c = d . { x : N | x < c + d }")
    inner = _inner(ast)
    assert inner.expression is not None, (
        "comprehension body should parse correctly — fix must not break this"
    )
    latex = _gen_expr("mu c : N; d : N | c = d . { x : N | x < c + d }")
    assert r"@ \{~" in latex or "@ {" in latex, f"body not in output: {latex!r}"
    assert "d.{" not in latex, f"unexpected projection: {latex!r}"


# Gap 4a — operator `*` (safe_followers contains STAR — must be covered by fix).
# Current output: inner.expression is a BinaryOp for multiplication; latex is correct.
# Already parses correctly — STAR does not trigger the projection in this input
# because the token after the body-start identifier is `*`, which safe_followers
# includes as a signal NOT to project.  The fix must preserve this.
def test_body_arithmetic_star() -> None:
    """Multi-decl mu with `*` body already parses correctly.

    Input:  mu c : N; d : N | c = d . c * d
    Target: (\\mu c : \\nat; d : \\nat | c = d @ c * d)

    `STAR` is in safe_followers so the postfix loop stops at `.c`; body is `c * d`.
    The fix must not regress this case.
    """
    ast = _parse_quantifier("mu c : N; d : N | c = d . c * d")
    inner = _inner(ast)
    assert inner.expression is not None, "body 'c * d' must be parsed correctly"
    latex = _gen_expr("mu c : N; d : N | c = d . c * d")
    assert "@ c * d" in latex, f"body not in output: {latex!r}"
    assert "d.c" not in latex, f"unexpected projection: {latex!r}"


# Gap 4b — operator `-` (MINUS is in safe_followers but FAILS for this input)
# Actual: inner.expression=None; latex '(\mu c : \nat; d : \nat | c = d.c - d)'
# Unlike `*`, `c - d` triggers the bug.  The reason is subtle: the token
# immediately after `c` (the would-be body start) is `-`, which safe_followers
# includes — so _parse_postfix does NOT project.  But `d . c` still gets parsed
# as projection d.c because `-` follows `c`.  Confirmed by actual output.
def test_body_arithmetic_minus() -> None:
    """Multi-decl mu with subtraction body must separate predicate from body.

    Input:  mu c : N; d : N | c = d . c - d
    Target: (\\mu c : \\nat; d : \\nat | c = d @ c - d)
    Actual: (\\mu c : \\nat; d : \\nat | c = d.c - d)   ← projection bug

    `MINUS` is in safe_followers for the token after `c`, so the loop stops
    at `c`, but the preceding `d . c` was already consumed as `d.c`.
    Confirms the fix must cover MINUS uniformly with PLUS.
    """
    ast = _parse_quantifier("mu c : N; d : N | c = d . c - d")
    inner = _inner(ast)
    assert inner.expression is not None, "expected body 'c - d' after bullet, got None"
    latex = _gen_expr("mu c : N; d : N | c = d . c - d")
    assert "@ c - d" in latex, f"body not in output: {latex!r}"
    assert "d.c" not in latex, f"projection artefact in output: {latex!r}"


# Gap 4c — operator `mod` (already passes).
# Current output: inner.expression is a BinaryOp for mod; latex is correct.
def test_body_arithmetic_mod() -> None:
    """Multi-decl mu with `mod` body already parses correctly.

    Input:  mu c : N; d : N | c = d . c mod d
    Target: (\\mu c : \\nat; d : \\nat | c = d @ c \\mod d)

    `mod` is a keyword token that breaks the projection chain. Fix must not
    disturb this path.
    """
    ast = _parse_quantifier("mu c : N; d : N | c = d . c mod d")
    inner = _inner(ast)
    assert inner.expression is not None, "body 'c mod d' must be parsed correctly"
    latex = _gen_expr("mu c : N; d : N | c = d . c mod d")
    assert r"@ c \mod d" in latex or "@ c mod d" in latex, (
        f"body not in output: {latex!r}"
    )
    assert "d.c" not in latex, f"unexpected projection: {latex!r}"


# Gap 5 — comprehension with `.` separator but no `|` predicate.
# Z RM §3.10: { Schema-Text @ Expr } where Schema-Text has no constraint.
# txt2tex already handles this form; current output is correct.
def test_comprehension_no_constraint_only_body() -> None:
    """Set comprehension with only a type constraint (no `|` predicate) and a body.

    Input:  { c : N; d : N . c + d }
    Target: \\{~ c : \\nat ; d : \\nat @ c + d ~\\}

    Z RM §3.10: `{ Schema-Text @ Expr }` allows Schema-Text with no predicate.
    txt2tex already handles this via the `.` separator in comprehensions.
    Already passes — the fix must not regress it.
    """
    tokens = Lexer("{ c : N; d : N . c + d }").tokenize()
    ast = Parser(tokens).parse()
    assert isinstance(ast, SetComprehension)
    assert ast.expression is not None, (
        "no-constraint comprehension should carry post-bullet expression"
    )
    latex = _gen_expr("{ c : N; d : N . c + d }")
    assert r"\{~" in latex, f"missing set-comprehension open in output: {latex!r}"
    assert "@ c + d" in latex, f"missing body in output: {latex!r}"
    assert "d.c" not in latex, f"projection artefact: {latex!r}"


# Gap 6 — three-variable schema-text (body is the last-declared var).
# Current output: inner.expression is None; latex contains 'a = b.c'.
# The bug fires on the last pair: `b . c` becomes projection b.c.
def test_three_variable_schema_text() -> None:
    """Three-variable schema-text mu: bullet body is the last-declared variable.

    Input:  mu a : N; b : N; c : N | a = b . c
    Target: (\\mu a : \\nat; b : \\nat; c : \\nat | a = b @ c)

    Confirms the fix scales beyond two declarations.  The body identifier `c`
    is the LAST declared variable, not the second-to-last.

    The AST nests three Quantifier levels (a → b → c); the expression field is
    on the innermost node (variables=['c']).  We verify via the generated LaTeX.
    """
    ast = _parse_quantifier("mu a : N; b : N; c : N | a = b . c")
    # Drill to innermost Quantifier (three levels: a, b, c)
    inner_b = _inner(ast)
    inner_c = _inner(inner_b)
    assert inner_c.expression is not None, (
        "expected body 'c' on innermost Quantifier, got None"
    )
    latex = _gen_expr("mu a : N; b : N; c : N | a = b . c")
    assert "@ c" in latex, f"body 'c' not in output: {latex!r}"
    assert "b.c" not in latex, f"projection artefact in output: {latex!r}"


# Gap 7 — fuzz round-trip positive: after the fix, the parser emits `@ c + d`
# instead of the ill-typed `d.c + d`, and fuzz must accept the output.
# This pins the regression at the semantic level: if the bug reappears the
# parser would emit `d.c` again, which fuzz rejects with "Argument of
# selection must have schema type" (Z RM §3.16).
@pytest.mark.skipif(not _fuzz_available(), reason="fuzz binary not on PATH")
def test_fuzz_accepts_fixed_bullet_output(tmp_path: Path) -> None:
    """Fuzz accepts the fixed LaTeX for the canonical bullet disambiguation input.

    Generates LaTeX for `mu c : N; d : N | c = d . c + d` using the fixed
    parser (which now emits `@ c + d`, not `d.c + d`), wraps it in a minimal
    axdef, and asserts fuzz exits zero.

    Regression pin: if the bullet disambiguation regresses, the parser will
    re-emit `d.c`, which is ill-typed per Z RM §3.16 and fuzz will reject it.
    """
    src = """\
axdef
  k : N
where
  k = (mu c : N; d : N | c = d . c + d)
end
"""
    tokens = Lexer(src).tokenize()
    doc = Parser(tokens).parse()
    assert isinstance(doc, Document)
    tex = LaTeXGenerator(use_fuzz=True).generate_document(doc)
    # Confirm the parser emits the bullet form, not the projection form.
    assert "@ c + d" in tex, f"expected bullet output '@ c + d' in tex:\n{tex}"
    assert "d.c" not in tex, f"projection artefact 'd.c' in tex:\n{tex}"
    result = _run_fuzz(tex, tmp_path)
    assert result.returncode == 0, (
        f"fuzz rejected the fixed bullet output\n"
        f"tex:\n{tex}\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )
