"""Tests for the Spivey-form dependent-domain bug in the generator.

``_collect_quantifier_chain`` (and its sibling ``_collect_lambda_chain``)
walk nested same-quantifier AST nodes and collapse them into a Spivey-
canonical schema text:

    forall s : T; e : f(s) | P

This is wrong when later declarations' domains reference earlier-bound
variables.  Fuzz parallel-binds schema-text declarations, so ``e : f(s)``
is ill-typed because ``s`` is not declared when ``f(s)`` is resolved.

The planned fix is *partial collapse*: truncate the chain at the first
dependency, emit the prefix as Spivey, and re-enter the generator for
the remainder (which will try its own Spivey collapse recursively).

Phase-3.2 bug — discovered via ``sem/solutions-corrected.txt`` regression.
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
# Helpers (same pattern as tests/test_08_functions/test_lambda_multidecl_fuzz.py
# and tests/test_spivey_quantifier_form.py)
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
    """Parse a txt2tex expression and return the generated LaTeX."""
    tokens = Lexer(src).tokenize()
    ast = Parser(tokens).parse()
    gen = LaTeXGenerator(use_fuzz=True)
    if isinstance(ast, Document):
        return gen.generate_document(ast)
    return gen.generate_expr(ast)


def _gen_doc(src: str) -> str:
    """Parse a full txt2tex document source and return the full LaTeX document."""
    tokens = Lexer(src).tokenize()
    ast = Parser(tokens).parse()
    assert isinstance(ast, Document)
    return LaTeXGenerator(use_fuzz=True).generate_document(ast)


def _extract_zed(full: str) -> str:
    """Extract the first zed environment body from a full document."""
    start = full.find(r"\begin{zed}")
    end = full.find(r"\end{zed}") + 9
    return full[start:end] if start >= 0 else full


def _run_fuzz(tex_content: str, tmp_path: Path) -> subprocess.CompletedProcess[str]:
    """Write tex_content to a temp file and run fuzz on it."""
    fuzz_bin = shutil.which("fuzz")
    assert fuzz_bin is not None, "fuzz binary not found on PATH"
    tex_file = tmp_path / "test.tex"
    tex_file.write_text(tex_content, encoding="utf-8")
    return subprocess.run(  # noqa: S603
        [fuzz_bin, str(tex_file)],
        capture_output=True,
        text=True,
        check=False,
    )


# ---------------------------------------------------------------------------
# Shared axdef preamble — declares f : N +-> P N and g : P N +-> P N so
# that dependent-domain expressions are well-typed under fuzz.
# ---------------------------------------------------------------------------

_AXDEF_F = """\
axdef
  f : N +-> P N
where
  true
end

"""

_AXDEF_FG = """\
axdef
  f : N +-> P N
  g : P N +-> P N
where
  true
end

"""


# ---------------------------------------------------------------------------
# Test 1 — canonical bug: two-decl forall with dependent second domain
# ---------------------------------------------------------------------------


def test_two_decl_dependent_at_pos_2() -> None:
    """Dependent second domain must NOT produce a flat Spivey schema text.

    The AST is ``Quantifier('forall', ['s'], dom f, body=Quantifier('forall',
    ['e'], f(s), body=P))``.  After the fix, the generator must emit:

        \\forall s : \\dom f @ \\forall e : f(s) @ s \\in \\dom f

    not the broken current form:

        \\forall s : \\dom f; e : f(s) @ s \\in \\dom f

    The semicolon form is wrong because fuzz parallel-binds schema-text
    declarations, so ``s`` is not in scope when ``f(s)`` is type-checked.
    """
    src = _AXDEF_F + "zed\n  forall s : dom f | forall e : f(s) | s elem dom f\nend"
    result = _gen_doc(src)
    zed = _extract_zed(result)
    # After the fix: one forall at depth-0, then nested forall at depth-1.
    assert r"\forall s : \dom f @ \forall e : f(s) @ s \in \dom f" in zed, (
        f"Expected nested forall form, got: {zed!r}"
    )


def test_two_decl_independent_stays_spivey() -> None:
    """Independent two-decl forall must stay in Spivey form (control).

    ``forall s : N; e : N | s = e`` is already valid Spivey: neither domain
    references the other variable, so collapse is safe and fuzz accepts it.

    This test must always pass — it guards against over-eager un-collapse.
    """
    result = _gen_expr("forall s : N; e : N | s = e")
    assert result == r"\forall s : \nat; e : \nat @ s = e", (
        f"Independent two-decl changed unexpectedly: {result!r}"
    )


# ---------------------------------------------------------------------------
# Test 2 — three-decl, dependency at middle position (b : f(a))
# ---------------------------------------------------------------------------


def test_three_decl_dependent_at_middle() -> None:
    """Three-decl forall with dependency at the middle position.

    Chain: ``a : N; b : f(a); c : N | P``

    After the fix the generator must truncate the Spivey prefix at ``a``
    (the first dependency boundary) and nest the remainder:

        \\forall a : \\nat @ \\forall b : f(a); c : \\nat @ a = c

    ``b : f(a)`` depends on ``a``, so ``a`` cannot share a flat schema-text
    with ``b``.  Once we nest, ``b`` and ``c`` are independent of each other
    so they can be recollapsed into one Spivey prefix at the inner level.
    """
    src = _AXDEF_F + "zed\n  forall a : N | forall b : f(a) | forall c : N | a = c\nend"
    result = _gen_doc(src)
    zed = _extract_zed(result)
    # Outer: single \\forall a : \\nat @
    assert r"\forall a : \nat @" in zed, f"Expected outer forall a, got: {zed!r}"
    # Inner: Spivey-collapsed b and c (both independent at that level)
    assert r"\forall b : f(a); c : \nat @" in zed, (
        f"Expected inner Spivey b;c, got: {zed!r}"
    )


# ---------------------------------------------------------------------------
# Test 3 — three-decl, dependency at end position (c : f(a))
# ---------------------------------------------------------------------------


def test_three_decl_dependent_at_end() -> None:
    """Three-decl forall with dependency only at the last position.

    Chain: ``a : N; b : N; c : f(a) | P``

    After the fix:

        \\forall a : \\nat; b : \\nat @ \\forall c : f(a) @ a = b

    ``a`` and ``b`` are independent — their Spivey prefix is valid.  ``c``
    depends on ``a``, so it must be nested rather than appended with a
    semicolon.
    """
    src = _AXDEF_F + "zed\n  forall a : N | forall b : N | forall c : f(a) | a = b\nend"
    result = _gen_doc(src)
    zed = _extract_zed(result)
    assert r"\forall a : \nat; b : \nat @" in zed, (
        f"Expected outer Spivey a;b, got: {zed!r}"
    )
    assert r"\forall c : f(a) @" in zed, f"Expected nested c, got: {zed!r}"


# ---------------------------------------------------------------------------
# Test 4 — three-decl, transitive dependencies (b : f(a), c : g(b))
# ---------------------------------------------------------------------------


def test_transitive_dependency() -> None:
    """Transitive dependencies require full nesting — no Spivey collapse at all.

    Chain: ``a : N; b : f(a); c : g(b) | P``

    ``b`` depends on ``a``, and ``c`` depends on ``b``.  After the fix:

        \\forall a : \\nat @ \\forall b : f(a) @ \\forall c : g(b) @ a = a

    Each level depends on the previous, so no adjacent pair can share a
    flat schema-text.  The partial-collapse rule fires at ``a``→``b`` and
    recursion fires again at ``b``→``c``.
    """
    src = (
        _AXDEF_FG
        + "zed\n  forall a : N | forall b : f(a) | forall c : g(b) | a = a\nend"
    )
    result = _gen_doc(src)
    zed = _extract_zed(result)
    assert r"\forall a : \nat @" in zed, f"Expected \\forall a, got: {zed!r}"
    assert r"\forall b : f(a) @" in zed, f"Expected \\forall b : f(a), got: {zed!r}"
    assert r"\forall c : g(b) @" in zed, f"Expected \\forall c : g(b), got: {zed!r}"
    # Must not have any semicolons joining dependent pairs
    assert "a : \\nat; b" not in zed, f"Should not have Spivey a;b, got: {zed!r}"
    assert "b : f(a); c" not in zed, f"Should not have Spivey b;c, got: {zed!r}"


# ---------------------------------------------------------------------------
# Test 5 — set comprehension: extra_declarations path is a separate code path
# ---------------------------------------------------------------------------


def test_set_comprehension_dependent_domain() -> None:
    """Set comprehension with a dependent-domain extra declaration.

    ``{ s : dom f | forall e : f(s) | e elem f(s) }``

    The set comprehension emits via ``_generate_set_comprehension``, which
    does NOT go through ``_collect_quantifier_chain``.  The nested ``forall``
    inside the predicate is a single-level quantifier (no chain-collapse
    applies), so the output is already correct.

    This test verifies the correct form is preserved and is not broken by
    the fix.  It must PASS now and after the fix.
    """
    src = _AXDEF_F + "zed\n  { s : dom f | forall e : f(s) | e elem f(s) }\nend"
    result = _gen_doc(src)
    zed = _extract_zed(result)
    # The set binder is s alone; the forall inside the predicate is single-level.
    assert r"\{~ s" in zed, f"Expected set binder s, got: {zed!r}"
    assert r"\forall e : f(s)" in zed, f"Expected forall e : f(s), got: {zed!r}"
    # No Spivey collapse across the set binder — s and e are in different binders
    assert "s; e" not in zed, f"Should not collapse s;e across binder, got: {zed!r}"


# ---------------------------------------------------------------------------
# Test 6 — mu with dependent domain
# ---------------------------------------------------------------------------


def test_mu_dependent_domain() -> None:
    """Nested mu with dependent second domain must NOT produce flat Spivey form.

    ``mu s : dom f | mu e : f(s) | e = s . s`` encodes a definite description
    with a dependent inner binding.  After the fix:

        (\\mu s : \\dom f | (\\mu e : f(s) | e = s @ s))

    or equivalently the inner mu stays nested.  The current broken output is:

        (\\mu s : \\dom f; e : f(s) | e = s.s)

    which fuzz rejects because ``s`` is not in scope for ``f(s)``.
    """
    src = _AXDEF_F + "zed\n  k = (mu s : dom f | mu e : f(s) | e = s . s)\nend"
    result = _gen_doc(src)
    zed = _extract_zed(result)
    # After fix: outer mu with s, inner mu with e : f(s), no semicolon join
    assert "s; e : f(s)" not in zed, (
        f"Should not Spivey-collapse s;e in mu, got: {zed!r}"
    )
    assert r"\mu s" in zed, f"Expected outer \\mu s, got: {zed!r}"
    assert r"\mu e : f(s)" in zed, f"Expected inner \\mu e : f(s), got: {zed!r}"


# ---------------------------------------------------------------------------
# Test 7 — exists with dependent domain
# ---------------------------------------------------------------------------


def test_exists_dependent_domain() -> None:
    """Nested exists with dependent second domain must NOT produce flat Spivey.

    ``exists s : dom f | exists e : f(s) | e elem f(s)``

    After the fix:

        \\exists s : \\dom f @ \\exists e : f(s) @ e \\in f(s)

    The current broken output is:

        \\exists s : \\dom f; e : f(s) @ e \\in f(s)
    """
    src = _AXDEF_F + "zed\n  exists s : dom f | exists e : f(s) | e elem f(s)\nend"
    result = _gen_doc(src)
    zed = _extract_zed(result)
    assert "s; e : f(s)" not in zed, (
        f"Should not Spivey-collapse s;e in exists, got: {zed!r}"
    )
    assert r"\exists s" in zed, f"Expected outer \\exists s, got: {zed!r}"
    assert r"\exists e : f(s)" in zed, f"Expected inner \\exists e : f(s), got: {zed!r}"


# ---------------------------------------------------------------------------
# Test 8 — lambda with dependent domain
# ---------------------------------------------------------------------------


def test_lambda_dependent_domain() -> None:
    """Nested lambda with dependent second domain must NOT produce flat Spivey.

    ``lambda s : dom f | lambda e : f(s) | e elem f(s) . s``

    After the fix:

        (\\lambda s : \\dom f | (\\lambda e : f(s) | e \\in f(s) @ s))

    The current broken output is:

        (\\lambda s : \\dom f; e : f(s) | e \\in f(s).s)

    Note: lambda uses ``_collect_lambda_chain``, a separate but structurally
    identical method — both sibling methods need the same fix.
    """
    lam_body = "lambda s : dom f | lambda e : f(s) | e elem f(s) . s"
    src = _AXDEF_F + f"zed\n  lam = {lam_body}\nend"
    result = _gen_doc(src)
    zed = _extract_zed(result)
    assert "s; e : f(s)" not in zed, (
        f"Should not Spivey-collapse s;e in lambda, got: {zed!r}"
    )
    assert r"\lambda s" in zed, f"Expected outer \\lambda s, got: {zed!r}"
    assert r"\lambda e : f(s)" in zed, f"Expected inner \\lambda e : f(s), got: {zed!r}"


# ---------------------------------------------------------------------------
# Test 9 — CONTROL: pure independent three-decl stays full Spivey
# ---------------------------------------------------------------------------


def test_pure_independent_stays_spivey() -> None:
    """Three independent declarations must stay in flat Spivey form.

    ``forall a : N | forall b : N | forall c : N | a = b``

    None of the domains references another bound variable, so the generator
    must emit a single flat schema text:

        \\forall a : \\nat; b : \\nat; c : \\nat @ a = b

    This test guards against over-eager un-collapse introduced by the fix.
    It must pass both before and after the fix.
    """
    src = "zed\n  forall a : N | forall b : N | forall c : N | a = b\nend"
    result = _gen_doc(src)
    zed = _extract_zed(result)
    assert r"\forall a : \nat; b : \nat; c : \nat @ a = b" in zed, (
        f"Expected flat Spivey three-decl, got: {zed!r}"
    )


# ---------------------------------------------------------------------------
# Test 10 — CONTROL: inner binder does not make outer domain dependent
# ---------------------------------------------------------------------------


def test_indirect_dependency_via_inner_binder_does_not_count() -> None:
    """A set comprehension in b's domain that mentions b does not count as a dependency.

    ``forall s : N | forall b : { x : N | x = b } | s = b``

    The domain of ``b`` is ``{ x : N | x = b }`` — the comprehension mentions
    ``b`` itself (which is a self-reference, not a reference to ``s``).  The
    domain does NOT reference ``s``, so ``b``'s domain is independent of ``s``.

    Spivey collapse should fire:

        \\forall s : \\nat; b : \\{~ x : \\nat | x = b ~\\} @ s = b

    This test verifies that the free-variable helper used by the fix correctly
    identifies the domain of ``b`` as NOT depending on ``s``.  It must pass
    both before and after the fix.
    """
    src = "zed\n  forall s : N | forall b : { x : N | x = b } | s = b\nend"
    result = _gen_doc(src)
    zed = _extract_zed(result)
    # Spivey form must be preserved — s and b share one schema text
    assert r"\forall s : \nat; b" in zed, (
        f"Expected Spivey s;b (b's domain doesn't reference s), got: {zed!r}"
    )
    # No extra nesting — one forall only
    assert zed.count(r"\forall") == 1, (
        f"Expected single \\forall (no un-collapse), got: {zed!r}"
    )


# ---------------------------------------------------------------------------
# Fuzz round-trip tests (skip when fuzz binary not available)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not _fuzz_available(), reason="fuzz binary not on PATH")
def test_fuzz_accepts_independent_two_decl(tmp_path: Path) -> None:
    """Fuzz accepts the Spivey-canonical form for independent two-decl forall.

    Verifies that the control case from test_two_decl_independent_stays_spivey
    actually passes fuzz's type checker, not just the string assertion.
    """
    src = "zed\n  forall s : N; e : N | s = e\nend"
    tex = _gen_doc(src)
    result = _run_fuzz(tex, tmp_path)
    assert result.returncode == 0, (
        f"fuzz rejected independent two-decl forall\n"
        f"tex:\n{tex}\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )


# ---------------------------------------------------------------------------
# Tests 11-14 -- jms coverage gaps: set-comp dependent extra_declarations and
# shadowing edge cases for the free-variable helper.
# ---------------------------------------------------------------------------


def test_set_comprehension_dependent_extra_declaration() -> None:
    """Set comprehension with a dependent extra_declaration must raise.

    ``{ s : dom f; e : f(s) | true }`` produces a ``SetComprehension``
    where ``extra_declarations=[('e', f(s))]`` and ``f(s)`` names ``s``,
    which is bound by the primary variables list.  Fuzz parallel-binds
    schema-text declarations, so ``s`` is NOT in scope when ``f(s)`` is
    type-checked.

    Unlike quantifiers, there is no Z RM split identity for set
    comprehensions (Z RM §3.10 -- no ``{D1;D2 | P . E} == {D1 | {D2 | P
    . E}}`` rule).  The generator must detect the dependency and raise.

    After the fix, this test must be rewritten to assert the raise rather
    than to use xfail:

        with pytest.raises(ValueError, match="dependent"):
            _gen_doc(src)

    Currently the generator succeeds and emits the broken form:

        \\\\{~ s : \\\\dom f ; e : f(s) | true ~\\\\}
    """
    src = _AXDEF_F + "zed\n  { s : dom f; e : f(s) | true }\nend"
    # After the fix the line below must be reached and must raise.
    with pytest.raises(ValueError, match="dependent"):
        _gen_doc(src)


def test_quantifier_with_set_comprehension_in_domain() -> None:
    """Quantifier with a set-comp domain that refers to an earlier variable.

    ``forall a : N | forall b : { y : N | y > a } | a + b = 0``

    The domain of ``b`` is ``{ y : N | y > a }``.  This comprehension binds
    ``y`` but leaves ``a`` free.  The free-variable helper must recognise
    that ``a`` (bound at the outer level) appears free in ``b``'s domain,
    and therefore prevent Spivey collapse at this boundary.

    After the fix the generator must emit:

        \\forall a : \\nat @ \\forall b : \\{~ y : \\nat | y > a ~\\} @ ...

    Current broken output (Spivey form, fuzz-rejected):

        \\forall a : \\nat; b : \\{~ y : \\nat | y > a ~\\} @ a + b = 0
    """
    src = "zed\n  forall a : N | forall b : { y : N | y > a } | a + b = 0\nend"
    result = _gen_doc(src)
    zed = _extract_zed(result)
    # After the fix: nested forall, no semicolon between a and b.
    assert r"\forall a : \nat @" in zed, f"Expected outer \\forall a, got: {zed!r}"
    assert r"\forall b : \{~ y : \nat | y > a ~\} @" in zed, (
        f"Expected nested \\forall b with set-comp domain, got: {zed!r}"
    )
    assert "a : \\nat; b" not in zed, (
        f"Should not Spivey-collapse a;b when b's domain is free in a, got: {zed!r}"
    )


def test_quantifier_with_lambda_in_domain() -> None:
    """Quantifier with a lambda-containing domain referencing an earlier variable.

    ``forall a : N | forall b : { x : N | x elem ran (lambda y : N . a) } | b > 0``

    The domain of ``b`` contains ``(lambda y : N . a)``; the lambda binds
    ``y`` but the body references ``a``.  So ``a`` is free in ``b``'s domain.
    The free-variable helper must subtract only the lambda's own formal
    parameter (``y``), leaving ``a`` visible as a free variable.

    After the fix the generator must emit nested foralls:

        \\forall a : \\nat @ \\forall b : \\{~ x : \\nat | ... ~\\} @ b > 0

    Current broken output (flat Spivey, fuzz-rejected):

        \\forall a : \\nat; b : \\{~ x : \\nat | ... ~\\} @ b > 0
    """
    src = (
        "zed\n"
        "  forall a : N"
        " | forall b : { x : N | x elem ran (lambda y : N . a) } | b > 0\n"
        "end"
    )
    result = _gen_doc(src)
    zed = _extract_zed(result)
    # After the fix: outer forall a, then nested forall b — no semicolon join.
    assert r"\forall a : \nat @" in zed, f"Expected outer \\forall a, got: {zed!r}"
    assert r"\forall b" in zed, f"Expected nested \\forall b, got: {zed!r}"
    assert "a : \\nat; b" not in zed, (
        "Should not Spivey-collapse a;b when lambda in b's domain is free in a, "
        f"got: {zed!r}"
    )


def test_inner_binder_shadows_outer_var() -> None:
    """Inner binder shadows outer: Spivey collapse must STILL fire (PASS control).

    ``forall a : N | forall b : { a : N | a > 0 } | a + 1 > 0``

    The domain of ``b`` is ``{ a : N | a > 0 }``.  The set comprehension
    introduces its OWN ``a`` (shadowing the outer), so the outer ``a`` is
    NOT free in ``b``'s domain.  Spivey collapse is correct here.

    The generator must emit:

        \\forall a : \\nat; b : \\{~ a : \\nat | a > 0 ~\\} @ a + 1 > 0

    This is the control case that proves the free-variable helper computes
    genuine free variables (not mere identifier occurrences).  A naive
    implementation that counts all identifier names would wrongly split.

    Current output (correct):

        \\forall a : \\nat; b : \\{~ a : \\nat | a > 0 ~\\} @ a + 1 > 0
    """
    src = "zed\n  forall a : N | forall b : { a : N | a > 0 } | a + 1 > 0\nend"
    result = _gen_doc(src)
    zed = _extract_zed(result)
    # Spivey form must be preserved — a and b share one schema text.
    assert r"\forall a : \nat; b : \{~ a : \nat | a > 0 ~\} @" in zed, (
        "Expected Spivey a;b (inner 'a' shadows outer, outer 'a' not free in "
        f"b's domain), got: {zed!r}"
    )
    # One forall only — no unnecessary nesting.
    assert zed.count(r"\forall") == 1, (
        f"Expected single \\forall (no un-collapse on shadow), got: {zed!r}"
    )


@pytest.mark.skipif(not _fuzz_available(), reason="fuzz binary not on PATH")
def test_fuzz_rejects_dependent_two_decl_current_output(tmp_path: Path) -> None:
    """Fuzz accepts the fixed generator output for a dependent two-decl forall.

    After the fix, the generator emits the nested form:
    ``\\forall s : \\dom f @ \\forall e : f(s) @ s \\in \\dom f``

    Fuzz accepts this because ``s`` is in scope (declared at the outer level)
    when ``f(s)`` is type-checked at the inner level.
    """
    src = _AXDEF_F + "zed\n  forall s : dom f | forall e : f(s) | s elem dom f\nend"
    tex = _gen_doc(src)
    result = _run_fuzz(tex, tmp_path)
    assert result.returncode == 0, (
        f"fuzz rejected the fixed nested output for dependent two-decl forall.\n"
        f"tex:\n{tex}\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )
