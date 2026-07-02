"""Tests for nested set-comprehension bullet detection.

Branch: fix/nested-comprehension-bullet.

Root cause: four parse sites (quantifier, quantifier-continuation,
lambda-pipe, set-comprehension) set ``_in_comprehension_body = True`` and in
their ``finally`` unconditionally assign ``False``.  When a NESTED
comprehension's ``finally`` runs first, it clobbers the OUTER comprehension's
``True``, so the outer's postfix bullet-vs-selection check never fires.

Two changes are required:

Change 1 - stack ``_in_comprehension_body``:
  At each of the four sites, save
  ``prev_in_comprehension = self._in_comprehension_body``
  before setting ``True``, and in ``finally`` restore it instead of
  assigning ``False``.  The mid-parse ``= False`` steps (line 873 and
  siblings) are left in place.

Change 2 - UNION ``_current_quantifier_vars`` across nesting:
  An inner comprehension is in scope of ALL enclosing schema-text variables.
  Sites that currently replace (``= set(variables)``) must instead union with
  the enclosing scope (``= prev_quantifier_vars | set(variables)``).

The seven shapes below map to the jms specification shapes 1-7:
  * Load-bearing (must FAIL before fix, PASS after): 1, 3, 4, 6, 7
  * Guards (must PASS before and after, resist naive fixes): 2, 5
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


def _gen(src: str, *, use_fuzz: bool = True) -> str:
    """Parse src and return generated LaTeX."""
    tokens = Lexer(src).tokenize()
    ast = Parser(tokens).parse()
    gen = LaTeXGenerator(use_fuzz=use_fuzz)
    if isinstance(ast, Document):
        return gen.generate_document(ast)
    return gen.generate_expr(ast)


def _parse(src: str) -> SetComprehension | Quantifier:
    """Parse src and return the root AST node (SetComprehension or Quantifier)."""
    tokens = Lexer(src).tokenize()
    ast = Parser(tokens).parse()
    assert isinstance(ast, (SetComprehension, Quantifier)), (
        f"expected SetComprehension or Quantifier, got {type(ast).__name__}"
    )
    return ast


def _fuzz_available() -> bool:
    """Return True if the fuzz binary is on PATH."""
    return shutil.which("fuzz") is not None


def _run_fuzz(tex_body: str, tmp_path: Path) -> subprocess.CompletedProcess[str]:
    """Run fuzz on tex_body wrapped in a minimal document."""
    fuzz_bin = shutil.which("fuzz")
    assert fuzz_bin is not None
    content = (
        "\\documentclass[a4paper]{article}\n"
        "\\usepackage{fuzz}\n"
        "\\begin{document}\n"
        f"{tex_body}\n"
        "\\end{document}\n"
    )
    tex_file = tmp_path / "test.tex"
    tex_file.write_text(content, encoding="utf-8")
    return subprocess.run(  # noqa: S603
        [fuzz_bin, str(tex_file)],
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )


# ---------------------------------------------------------------------------
# Shape 1 (load-bearing, Change 1): nested comprehension in outer predicate,
# outer bullet after it.
#
# Input:  { c : Cls | #({ cp : Part | cp.cid = c.cid }) = 0 land c.status = zFalse . c }
# Bug:    inner comp finally clobbers _in_comprehension_body → False.
#         Postfix sees zFalse . c with _in_comprehension_body=False → parses
#         as TupleProjection zFalse.c → no outer bullet.
# Fix:    Change 1 restores outer's True after inner finally → postfix var check
#         fires → breaks at zFalse → outer bullet `. c` detected.
# ---------------------------------------------------------------------------

_SHAPE1_SRC = (
    "{ c : Cls | #({ cp : Part | cp.cid = c.cid }) = 0 land c.status = zFalse . c }"
)


def test_shape1_outer_bullet_detected() -> None:
    """Outer bullet is detected after a nested comprehension in the predicate.

    Without Change 1, the inner comprehension's ``finally`` clobbers
    ``_in_comprehension_body`` to ``False``.  The postfix parser then treats
    ``zFalse . c`` as field selection (``zFalse.c``) rather than stopping at
    ``zFalse`` and leaving ``. c`` as the outer bullet.

    After the fix: outer ``SetComprehension.expression`` is ``Identifier('c')``
    and the LaTeX ends with ``@ c ~\\}``.
    """
    ast = _parse(_SHAPE1_SRC)
    assert isinstance(ast, SetComprehension)
    assert ast.expression is not None, (
        "outer bullet was not detected — "
        "inner comp's finally clobbered _in_comprehension_body"
    )
    latex = _gen(_SHAPE1_SRC)
    assert "@ c ~\\}" in latex, f"outer bullet '@ c' absent from output: {latex!r}"
    assert "zFalse.c" not in latex, (
        f"projection artefact 'zFalse.c' in output: {latex!r}"
    )


# ---------------------------------------------------------------------------
# Shape 2 (guard, passes before and after fix): nested comprehension in
# predicate, NO outer bullet.
#
# When a naive fix introduces a spurious bullet on every set comprehension
# that contains a nested one, this guard catches it.
# ---------------------------------------------------------------------------

_SHAPE2_SRC = (
    "{ c : Cls | #({ cp : Part | cp.cid = c.cid }) = 0 land c.status = zFalse }"
)


def test_shape2_no_bullet_no_regression() -> None:
    """Outer comprehension with nested predicate but NO bullet closes cleanly.

    The outer comprehension has no ``@`` separator.  After the fix the outer
    ``SetComprehension.expression`` must still be ``None``.  Any fix that
    spuriously treats the final identifier as a bullet will fail here.
    """
    ast = _parse(_SHAPE2_SRC)
    assert isinstance(ast, SetComprehension)
    assert ast.expression is None, (
        "spurious bullet detected — fix incorrectly treated closing"
        " identifier as a bullet when none was present"
    )
    latex = _gen(_SHAPE2_SRC)
    # The outer comp must close with ~\} immediately after the predicate.
    assert "zFalse ~\\}" in latex, (
        f"expected predicate to end the outer comp, got: {latex!r}"
    )


# ---------------------------------------------------------------------------
# Shape 3 (load-bearing, Change 2): inner comprehension's characteristic
# expression is an outer-scope variable.
#
# Input:  { c : Cls | c.ok . { cp : Part | cp.status = val . c } }
# Bug:    inner comp's _current_quantifier_vars = {cp} (old replace, no union).
#         Postfix sees val . c with _in_comparison_rhs=True → RBRACE-check
#         does not fire (requires not _in_comparison_rhs) → safe_followers sees
#         'c' followed by '}' → RBRACE is in safe_followers → parses as val.c.
# Fix:    Change 2 unions enclosing scope: inner's vars = {c, cp}.
#         Postfix var-check fires: c in {c, cp}, spaced → BREAK → val is the
#         predicate end, `. c` is the inner bullet.
# ---------------------------------------------------------------------------

_SHAPE3_SRC = "{ c : Cls | c.ok . { cp : Part | cp.status = val . c } }"


def test_shape3_inner_bullet_outer_scope_var() -> None:
    """Inner comprehension bullet whose characteristic expression is an outer var.

    Without Change 2 the inner ``_current_quantifier_vars`` does not include
    the outer variable ``c``.  When postfix processes ``val . c }`` inside the
    inner predicate (as the RHS of an equality), the RBRACE-check is gated on
    ``not _in_comparison_rhs`` which is ``False``, so the check does not fire.
    The safe-followers path then treats ``c`` followed by ``}`` as projection:
    ``val.c``.

    After the fix: inner ``SetComprehension.expression`` is ``Identifier('c')``
    and the LaTeX contains ``@ c ~\\}`` from the inner comprehension.
    """
    ast = _parse(_SHAPE3_SRC)
    assert isinstance(ast, SetComprehension)
    # The outer comp has c.ok as predicate; its expression is the inner comp.
    inner = ast.expression
    assert isinstance(inner, SetComprehension), (
        f"outer expression should be inner SetComprehension, got {type(inner).__name__}"
    )
    assert inner.expression is not None, (
        "inner bullet '. c' was not detected — "
        "'c' was not in inner _current_quantifier_vars (union missing)"
    )
    latex = _gen(_SHAPE3_SRC)
    assert "@ c ~\\}" in latex, f"inner bullet '@ c' absent from output: {latex!r}"
    assert "val.c" not in latex, f"projection artefact 'val.c' in output: {latex!r}"


# ---------------------------------------------------------------------------
# Shape 4 (load-bearing, Change 1): both inner quantifier and outer
# comprehension have explicit bullets.
#
# Input:  { c : Cls | (mu cp : Part | cp.ref = cref . cp.name) = res land c.ok . c }
# Bug:    the inner mu sets _in_comprehension_body True, hits bullet,
#         mid-parse sets False (line 873), finally sets False unconditionally.
#         After mu returns, outer _in_comprehension_body = False.
#         Postfix sees c.ok (TupleProjection) then `. c` with
#         _in_comprehension_body=False → TupleProjection check does not fire
#         → safe_followers: c followed by } → RBRACE in safe_followers
#         → c.ok.c is absorbed into predicate.  No outer bullet.
# Fix:    Change 1 restores outer's True after mu finally.  TupleProjection
#         check fires on c.ok then . → BREAK → outer bullet `. c` detected.
# ---------------------------------------------------------------------------

_SHAPE4_SRC = (
    "{ c : Cls | (mu cp : Part | cp.ref = cref . cp.name) = res land c.ok . c }"
)


def test_shape4_outer_bullet_after_inner_quantifier_with_bullet() -> None:
    """Outer bullet is detected after an inner quantifier that itself has a bullet.

    The inner mu quantifier executes both the mid-parse ``_in_comprehension_body
    = False`` (line 873) AND the ``finally`` reset.  Without Change 1 the
    outer's ``True`` is clobbered so the TupleProjection-check for ``c.ok . c``
    does not fire.  The predicate absorbs ``c.ok.c`` and no outer bullet is
    emitted.

    After the fix: outer ``SetComprehension.expression`` is ``Identifier('c')``.
    """
    ast = _parse(_SHAPE4_SRC)
    assert isinstance(ast, SetComprehension)
    assert ast.expression is not None, (
        "outer bullet was not detected after inner mu-with-bullet — "
        "inner's finally clobbered _in_comprehension_body"
    )
    latex = _gen(_SHAPE4_SRC)
    assert "@ c ~\\}" in latex, f"outer bullet '@ c' absent from output: {latex!r}"
    assert "c.ok.c" not in latex, f"projection artefact 'c.ok.c' in output: {latex!r}"


# ---------------------------------------------------------------------------
# Shape 5 (guard, passes before and after fix): nested comprehension in the
# outer's CHARACTERISTIC expression (after the outer bullet).
#
# When the outer quantifier's mid-parse step sets _in_comprehension_body False
# before parsing the char expr, the inner comprehension is entered with False.
# A correct fix saves the actual value (False at that point), so the inner's
# finally restores False — not a spurious True.
#
# This shape catches the naive fix that replaces ``False`` with a hardcoded
# ``True`` in prev_in_comprehension (always restoring True from inner).
# ---------------------------------------------------------------------------

_SHAPE5_SRC = "forall c : Cls | c.status = zFalse . { cp : Part | cp.ref = c.name }"


def test_shape5_inner_comp_in_char_expr_no_spurious_true() -> None:
    """Quantifier with bullet: inner comp in char expr restores False, not True.

    The outer quantifier's mid-parse sets ``_in_comprehension_body = False``
    before parsing the characteristic expression.  The inner comprehension
    (the char expr) enters with ``False``, sets ``True``, and its ``finally``
    must restore ``False`` — not a spurious ``True`` that could pollute later
    parsing contexts.

    Both before and after the fix this must parse cleanly with the quantifier's
    ``expression`` being the inner ``SetComprehension``.
    """
    ast = _parse(_SHAPE5_SRC)
    assert isinstance(ast, Quantifier)
    assert isinstance(ast.expression, SetComprehension), (
        f"expected forall char expr to be a SetComprehension, "
        f"got {type(ast.expression).__name__}"
    )
    latex = _gen(_SHAPE5_SRC)
    # The outer bullet appears as '@ \{~ ...'; no inner bullet since the
    # inner comp has no '.' separator.
    assert "@ \\{~" in latex, f"outer bullet absent from output: {latex!r}"


# ---------------------------------------------------------------------------
# Shape 6 (load-bearing, both changes): triple nesting — three set
# comprehension levels.
#
# Input:
#   { a : A | #({ b : B | #({ c : C | c.tag = zFalse . a }) = 0
#               land b.tag = zFalse . b }) = 0 land a.tag = zFalse . a }
#
# Bug (Change 1): C's finally clobbers B's True → B predicate parses
#   b.tag = zFalse.b (projection), no B bullet → B's finally clobbers A's
#   True → A predicate parses a.tag = zFalse.a (projection), no A bullet.
# Bug (Change 2): C's _current_quantifier_vars = {c} (old replace), 'a' not
#   in {c} → C's postfix var-check does not fire for '. a' → zFalse.a ✗.
#
# After fix: all three bullets detected; each 'zFalse' ends its predicate.
# ---------------------------------------------------------------------------

_SHAPE6_SRC = (
    "{ a : A | #({ b : B | #({ c : C | c.tag = zFalse . a })"
    " = 0 land b.tag = zFalse . b }) = 0 land a.tag = zFalse . a }"
)


def test_shape6_triple_nesting_stack_behaviour() -> None:
    """Triple-nested comprehensions: all three bullets detected.

    Confirms genuine stack behaviour — a single saved value would only fix the
    innermost level.  All three comprehension levels must have their
    ``_in_comprehension_body`` correctly restored after their nested inner
    comprehension finishes.

    Additionally, the union of outer-scope variables must reach from A through
    B to C so that the innermost predicate ``c.tag = zFalse`` terminates before
    ``. a`` (an outer-scope variable from A).
    """
    ast = _parse(_SHAPE6_SRC)
    assert isinstance(ast, SetComprehension)
    assert ast.expression is not None, (
        "outermost (A) bullet was not detected — "
        "stack behaviour broken at the outer level"
    )
    latex = _gen(_SHAPE6_SRC)
    assert "@ a ~\\}" in latex, f"outer bullet '@ a' absent from output: {latex!r}"
    assert "zFalse.a" not in latex, (
        f"projection artefact 'zFalse.a' in output: {latex!r}"
    )
    assert "zFalse.b" not in latex, (
        f"projection artefact 'zFalse.b' in output: {latex!r}"
    )


# ---------------------------------------------------------------------------
# Shape 7 (load-bearing, Change 2): constrained quantifier with inner
# comprehension whose predicate ends with an outer-scope variable as bullet.
#
# Input:  forall x : T | x.status = zFalse | { y : S | y.status = classif . x }
# Bug:    inner comp's _current_quantifier_vars = {y} (old replace).
#         Postfix sees classif . x with _in_comparison_rhs=True → RBRACE-check
#         does not fire → safe_followers: x followed by } → RBRACE in
#         safe_followers → classif.x.
# Fix:    Change 2 unions quantifier vars into inner's set: {x, y}.
#         Var-check fires for x in {x, y}, spaced → BREAK → inner bullet.
#
# Also includes a mu constrained form to cover _parse_quantifier site 1.
# ---------------------------------------------------------------------------

_SHAPE7A_SRC = "forall x : T | x.status = zFalse | { y : S | y.status = classif . x }"
_SHAPE7B_SRC = "(mu x : T | x.status = zFalse | { y : S | y.status = classif . x })"


def test_shape7a_constrained_forall_inner_bullet_outer_var() -> None:
    """Constrained forall: inner comp bullet uses the outer quantifier variable.

    The constrained ``forall x : T | constraint | body`` form.  The body is a
    set comprehension whose predicate ends with ``classif . x``.  Without
    Change 2 the inner ``_current_quantifier_vars`` does not include ``x``, so
    the postfix var-check does not fire and ``classif.x`` is parsed as a
    projection.

    After the fix: inner comp has ``expression = Identifier('x')`` and the
    LaTeX contains ``@ x ~\\}``.
    """
    latex = _gen(_SHAPE7A_SRC)
    assert "@ x ~\\}" in latex, f"inner bullet '@ x' absent from output: {latex!r}"
    assert "classif.x" not in latex, (
        f"projection artefact 'classif.x' in output: {latex!r}"
    )


def test_shape7b_constrained_mu_inner_bullet_outer_var() -> None:
    """Constrained mu form: inner comp bullet uses the outer quantifier variable.

    Same mechanics as shape 7a but via the mu quantifier form, exercising the
    ``_parse_quantifier`` site (site 1) rather than the forall site in
    isolation.
    """
    latex = _gen(_SHAPE7B_SRC)
    assert "@ x ~\\}" in latex, f"inner bullet '@ x' absent from output: {latex!r}"
    assert "classif.x" not in latex, (
        f"projection artefact 'classif.x' in output: {latex!r}"
    )


# ---------------------------------------------------------------------------
# Shape 8 (load-bearing, Fix 1 Site A): schema-text quantifier body nested
# inside an outer set comprehension — exercises _parse_schema_quantifier_body.
#
# Input:  { c : Cls | (forall Env | c.status = zFalse) . c }
# Bug:    _parse_schema_quantifier_body sets _in_comprehension_body = True and
#         unconditionally resets it to False in finally (NOT stacked).
#         After the schema-text quantifier returns, the outer comprehension's
#         _in_comprehension_body is False.  Postfix sees `. c` with False →
#         rule at §3.16 spaced-dot var-check does not fire → outer bullet missed.
# Fix:    Site A stacks the flag: save prev before True, restore it in finally.
# ---------------------------------------------------------------------------

_SHAPE8_SRC = "{ c : Cls | (forall Env | c.status = zFalse) . c }"


def test_shape8_schema_text_quantifier_nested_outer_bullet() -> None:
    """Outer bullet is detected after a nested schema-text quantifier body.

    ``_parse_schema_quantifier_body`` unconditionally assigns
    ``_in_comprehension_body = False`` in its ``finally`` (Site A).  When
    nested inside an outer set comprehension predicate the outer ``True`` is
    clobbered.  Postfix then treats ``. c`` as field projection instead of the
    outer bullet separator.

    After the fix: outer ``SetComprehension.expression`` is
    ``Identifier('c')`` and the LaTeX ends with ``@ c ~\\}``.
    """
    ast = _parse(_SHAPE8_SRC)
    assert isinstance(ast, SetComprehension)
    assert ast.expression is not None, (
        "outer bullet was not detected — "
        "schema-text quantifier finally clobbered _in_comprehension_body"
    )
    latex = _gen(_SHAPE8_SRC)
    assert "@ c ~\\}" in latex, f"outer bullet '@ c' absent from output: {latex!r}"


# ---------------------------------------------------------------------------
# Shape 9 (load-bearing, Fix 2 Site B): period-without-predicate
# { x : T . expr } where expr is a nested comprehension referencing x in
# bullet position — exercises the PERIOD branch of
# _parse_set_comprehension_from_brace.
#
# Input:  { a : Arr . { b : Items | b.ref = idx . a } }
# Bug:    PERIOD branch parses expression = self._parse_set_expression()
#         WITHOUT updating _current_quantifier_vars.
#         Inner PIPE branch unions prev_quantifier_vars | {b} — no 'a'.
#         Inner postfix sees `idx . a }`: 'a' not in {b}, _in_comparison_rhs
#         is True so RBRACE-check is gated out; safe_followers sees 'a}'
#         → idx.a parsed as projection, no inner bullet.
# Fix:    PERIOD branch computes all_comp_vars ({a}), unions into
#         _current_quantifier_vars, and save/restores both vars and flag.
#         Inner PIPE branch inherits {a} and unions {b} → {a, b}.
#         'a' in {a, b} AND spaced → var-check fires → inner bullet `. a`.
# ---------------------------------------------------------------------------

_SHAPE9_SRC = "{ a : Arr . { b : Items | b.ref = idx . a } }"


def test_shape9_period_branch_nested_comp_outer_var_bullet() -> None:
    """Period-without-predicate outer comp: nested inner comp sees outer var.

    The PERIOD (no-predicate) branch of ``_parse_set_comprehension_from_brace``
    does not update ``_current_quantifier_vars`` before parsing the expression.
    The inner comprehension's PIPE branch unions ``prev_quantifier_vars | {b}``
    — without Fix 2, ``a`` is absent and the inner bullet ``. a`` is not
    detected.

    After the fix: inner ``SetComprehension.expression`` is ``Identifier('a')``
    and the LaTeX contains ``@ a ~\\}``.  The regression artefact ``idx.a``
    must be absent.
    """
    ast = _parse(_SHAPE9_SRC)
    assert isinstance(ast, SetComprehension)
    inner = ast.expression
    assert isinstance(inner, SetComprehension), (
        f"outer expression should be inner SetComprehension, got {type(inner).__name__}"
    )
    assert inner.expression is not None, (
        "inner bullet '. a' was not detected — "
        "'a' was not in inner _current_quantifier_vars (PERIOD branch union missing)"
    )
    latex = _gen(_SHAPE9_SRC)
    assert "@ a ~\\}" in latex, f"inner bullet '@ a' absent from output: {latex!r}"
    assert "idx.a" not in latex, f"projection artefact 'idx.a' in output: {latex!r}"


# ---------------------------------------------------------------------------
# Optional fuzz round-trip for shape 1 (requires fuzz binary)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not _fuzz_available(), reason="fuzz binary not on PATH")
def test_shape1_fuzz_round_trip(tmp_path: Path) -> None:
    """Fuzz accepts the fixed output for shape 1.

    If the bullet fix regresses, the generator re-emits ``zF.c``.  Fuzz
    then rejects with "Argument of selection must have schema type" (Z RM §3.16)
    because ``zF : zBool`` is not a schema type.

    This test pins the semantic-level regression: a generator-level change that
    re-introduces the projection bug will be caught here even if the parser-unit
    assertions above have false positives.
    """
    # Use schema types so field access is fuzz-valid.  A given set has no
    # fields; all access must be via schema declarations (Z RM §3.16).
    src = """\
given CID, PID

zed
  zBool ::= zT | zF
end

schema Cas
  cid : CID
  ok : zBool
end

schema Prt
  pid : PID
  cid : CID
end

axdef
  result : P Cas
where
  result = { c : Cas | #({ p : Prt | p.cid = c.cid }) = 0 land c.ok = zF . c }
end
"""
    tokens = Lexer(src).tokenize()
    doc = Parser(tokens).parse()
    assert isinstance(doc, Document)
    tex = LaTeXGenerator(use_fuzz=True).generate_document(doc)
    assert "@ c ~\\}" in tex, f"expected bullet output in tex:\n{tex}"
    assert "zF.c" not in tex, f"projection artefact 'zF.c' in tex:\n{tex}"
    result = _run_fuzz(tex, tmp_path)
    assert result.returncode == 0, (
        f"fuzz rejected the fixed output\n"
        f"tex:\n{tex}\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )
