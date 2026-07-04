"""Regression tests: wrapped set-comprehension indentation tracks binder depth.

jms ruling (see mission for fix/setcomp-wrap-indent): indentation inside a Z
paragraph tracks *binding depth*, where a binder is ``forall``, ``exists``,
``exists1``, ``lambda``, ``mu``, **and** set comprehension ``{ D | P . E }``
(Z RM §3.9 — a comprehension is schema-text-plus-spot, the same construction
as a quantifier §3.8).

Before this fix, comprehensions did not increment the shared depth counter
and their own line-break used a hardcoded ``\\t1`` regardless of context.
Two defects resulted:

1. Flat body — a comprehension wrapped inside an enclosing quantifier stayed
   at the *same* ``\\t`` level as the surrounding predicate, instead of one
   level deeper.
2. Zig-zag — a comprehension nested two levels deep emitted its own body
   lines at ``\\t1`` while the surrounding conjunction breaks (computed from
   the real depth) used ``\\t2``, producing non-monotonic indentation within
   a single comprehension body.

Each test below parses a small Z paragraph (``zed`` or ``schema``), generates
LaTeX in fuzz mode, and asserts on the *exact* ``\\t{n}`` prefix of specific
continuation lines.
"""

from __future__ import annotations

from txt2tex.ast_nodes import Document
from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser


def _tex(src: str) -> str:
    """Parse src as a full document and return the generated LaTeX body."""
    tokens = Lexer(src).tokenize()
    ast = Parser(tokens).parse()
    assert isinstance(ast, Document)
    return LaTeXGenerator(use_fuzz=True).generate_document(ast)


# ---------------------------------------------------------------------------
# Shape (a): defect 1 — flat body.
#
# Source (see _DEFECT1_SRC below): a forall whose consequent is a cardinality
# comparison on a wrapped set comprehension, followed by '=>' and a plain
# consequent.
#
# forall is depth 1; the comprehension is a binder nested inside forall's
# body, so its own predicate is depth 2.  The consequent after '=>' stays at
# forall's own depth (1) — it is NOT inside the comprehension's scope.
# ---------------------------------------------------------------------------

_DEFECT1_SRC = """\
zed
  forall m : Manager |
    #{ c : Case | c.a = 1 land
      c.b = 2 } > 5 =>
    m.done = zTrue
end
"""


def test_defect1_comprehension_body_one_level_deeper_than_opener() -> None:
    r"""Comprehension body line is one tab deeper than the forall that wraps it.

    Before the fix, the hardcoded ``\t1`` left ``c.b = 2 ~\}`` flush with the
    surrounding forall body (also ``\t1``) — the wrapped set was
    indistinguishable from the enclosing predicate.  After the fix it must be
    ``\t2``: one level deeper than the enclosing ``\forall`` (depth 1).
    """
    tex = _tex(_DEFECT1_SRC)
    assert r"\t2 c.b = 2 ~\}" in tex, (
        f"expected comprehension body at \\t2 (one deeper than forall): {tex!r}"
    )


def test_defect1_consequent_stays_at_forall_depth() -> None:
    r"""The consequent after '=>' is outside the comprehension's scope.

    It sits at the forall's own depth (\t1), not the comprehension's deeper
    level — the comprehension's binder only extends over its own body.
    """
    tex = _tex(_DEFECT1_SRC)
    assert r"\t1 m.done = zTrue" in tex, (
        f"expected consequent at \\t1 (forall depth, not comprehension depth): {tex!r}"
    )


# ---------------------------------------------------------------------------
# Shape (b): defect 2 — zig-zag.
#
# forall a : N | a > 0 land
#   (exists b : N | b elem { x : N |
#     x > a land
#     x < b . x })
#
# forall -> depth 1, exists -> depth 2, comprehension -> depth 3.  Both
# wrapped lines of the comprehension body must share the SAME depth (3),
# monotonically deeper than the exists that opens it (2).
# ---------------------------------------------------------------------------

_DEFECT2_SRC = """\
zed
  forall a : N | a > 0 land
    (exists b : N | b elem { x : N |
      x > a land
      x < b . x })
end
"""


def test_defect2_comprehension_body_lines_share_one_level() -> None:
    r"""Both wrapped lines of the comprehension body sit at the same \t{n}.

    Before the fix these emitted \t1 then \t2 (zig-zag, non-monotonic).
    After the fix both lines share \t3: forall (1) + exists (2) + the
    comprehension's own nesting level (3).
    """
    tex = _tex(_DEFECT2_SRC)
    assert r"\t3 x > a \land \\" in tex, (
        f"expected first comprehension body line at \\t3: {tex!r}"
    )
    assert r"\t3 x < b @ x ~\}" in tex, (
        f"expected second comprehension body line at \\t3 (same level as first,"
        f" not shallower): {tex!r}"
    )
    # Zig-zag guard: the two body lines must NOT differ in tab level.
    assert r"\t1 x > a" not in tex, f"body line regressed to flat \\t1: {tex!r}"
    assert r"\t2 x < b @ x ~\}" not in tex, (
        f"body lines zig-zagged (\\t2 second line): {tex!r}"
    )


def test_defect2_comprehension_opener_stays_at_exists_depth() -> None:
    r"""The comprehension's opening line sits at its container's depth (2).

    Per Q1: "the binder's opening line sits at its container's depth, and
    the binder increments depth for its scoped body."  The '(\exists b ...'
    line is part of the forall's own break, at forall depth (1); this test
    pins that unrelated line so a future change cannot accidentally bump it.
    """
    tex = _tex(_DEFECT2_SRC)
    assert r"\t1 (\exists b : \nat @ b \in \{~ x : \nat |" in tex, (
        f"expected comprehension-opening line at forall depth (\\t1): {tex!r}"
    )


# ---------------------------------------------------------------------------
# Shape (c): the bullet ('.') term sits at the SAME level as the predicate.
#
# forall q : N |
#   #{ x : N | x > 0 land
#     x < q .
#     x } > 0
#
# Both the predicate continuation (after 'land') and the bullet term ('x')
# are in the scope of 'x : N' — both must be \t2 (forall=1, comp=2), never
# different from each other.
# ---------------------------------------------------------------------------

_BULLET_SRC = """\
zed
  forall q : N |
    #{ x : N | x > 0 land
      x < q .
      x } > 0
end
"""


def test_bullet_term_matches_predicate_depth() -> None:
    r"""The bullet ('.') term shares the predicate's depth, not a shallower one.

    Q4: "the predicate P and the bullet-term e are both in the scope of D,
    so both sit at the same level.  Do not indent bullet e differently from
    P."
    """
    tex = _tex(_BULLET_SRC)
    assert r"\t2 x < q @ \\" in tex, f"expected predicate continuation at \\t2: {tex!r}"
    assert r"\t2 x ~\}" in tex, (
        f"expected bullet term at \\t2, matching the predicate's depth: {tex!r}"
    )


# ---------------------------------------------------------------------------
# Shape (d): schema `where` predicate — same mechanism, no branch on node kind.
#
# Source (see _SCHEMA_SRC below): a schema whose `where` predicate is the
# same forall-wrapping-a-comprehension shape as (a).
#
# Identical structure to shape (a) but inside a schema's `where` clause
# instead of a bare `zed` predicate — confirms the depth-tracking mechanism
# is uniform across Z-paragraph kinds (Q5).
# ---------------------------------------------------------------------------

_SCHEMA_SRC = """\
given Manager, Case, Part

schema S
  m : Manager
where
  forall c : Case | c.a = 1 land
    #{ p : Part | p.b = 2 land
      p.c = 3 } > 0
end
"""


def test_schema_where_comprehension_indents_by_binder_count() -> None:
    r"""A comprehension nested in a schema `where` predicate indents identically.

    The generator must not special-case schema predicates: the same
    binder-count depth used for zed/axdef paragraphs applies here.  The
    comprehension body line must be \t2 (forall=1, comprehension=2).
    """
    tex = _tex(_SCHEMA_SRC)
    assert r"\t2 p.c = 3 ~\}" in tex, (
        f"expected schema-where comprehension body at \\t2: {tex!r}"
    )


# ---------------------------------------------------------------------------
# Regression: existing single-level comprehension convention is unchanged.
#
# docs/guides/FUZZ_VS_STD_LATEX.md:726 —
#   Evens == { x : N | \\ \t1 x mod 2 = 0 }
#
# A bare comprehension with no enclosing quantifier sits at container depth 0;
# the comprehension itself is the only binder, so its body is \t1 — unchanged
# by this fix.
# ---------------------------------------------------------------------------

_EVENS_SRC = """\
zed
  Evens == { x : N |
    x mod 2 = 0 }
end
"""


def test_single_level_comprehension_still_emits_t1() -> None:
    r"""A comprehension with no enclosing binder still emits \t1 (unchanged)."""
    tex = _tex(_EVENS_SRC)
    assert r"\t1 x \mod 2 = 0 ~\}" in tex, (
        f"expected unchanged single-level \\t1 convention: {tex!r}"
    )


# ---------------------------------------------------------------------------
# Shape (e): pipe/multi-decl lambda (Z RM §3.12, ``_generate_lambda_quantifier``)
# is a binder too, same as forall/exists/exists1/mu/dot-form-lambda/comprehension.
#
# forall m : N |
#   lambda x : N; y : N | x > 0 land
#     y > 0 . x + y
#
# forall -> depth 1; the pipe-lambda nested in its body -> depth 2.  The
# wrapped continuation of the lambda's own predicate ('y > 0') must sit at
# \t2, not \t1 (the completeness gap PR #89 review found: the dot-form
# ``_generate_lambda`` incremented ``_binding_depth`` but the pipe/multi-decl
# ``_generate_lambda_quantifier`` did not).
# ---------------------------------------------------------------------------

_PIPE_LAMBDA_SRC = """\
zed
  forall m : N |
    lambda x : N; y : N | x > 0 land
      y > 0 . x + y
end
"""


def test_pipe_lambda_body_one_level_deeper_than_enclosing_forall() -> None:
    r"""A pipe/multi-decl lambda nested under forall indents its own wrap one deeper.

    Before the fix, ``_generate_lambda_quantifier`` never incremented
    ``_binding_depth`` around its predicate/expression, so the wrapped
    ``y > 0`` line stayed at \\t1 (the forall's own depth) instead of \\t2.
    """
    tex = _tex(_PIPE_LAMBDA_SRC)
    assert r"\t2 y > 0 @ x + y" in tex, (
        f"expected pipe-lambda predicate continuation at \\t2 (one deeper than"
        f" forall): {tex!r}"
    )


def test_pipe_lambda_at_top_level_still_wraps_sanely() -> None:
    r"""A depth-0 pipe lambda that wraps still renders without a spurious \\t0.

    No enclosing binder means ``_get_indentation`` returns ``""`` at depth 0
    and the first binding level inside the lambda is \\t1 — matching the
    single-level-comprehension convention (shape in ``_EVENS_SRC`` above).
    """
    src = """\
zed
  lambda x : N; y : N | x > 0 land
    y > 0 . x + y
end
"""
    tex = _tex(src)
    assert r"\t1 y > 0 @ x + y" in tex, (
        f"expected top-level pipe-lambda wrap at \\t1: {tex!r}"
    )


# ---------------------------------------------------------------------------
# Shape (f): dependent-domain lambda chain — the dependency-stop recursion in
# _generate_lambda_quantifier must indent monotonically, one level per lambda
# in the chain, without double-counting or under-counting across the
# recursive call.
#
# forall m : N |
#   lambda s : dom f | lambda e : f(s) | e > 0 land
#     s > 0 . s + e
#
# forall(1) + outer lambda prefix (dependency-stop, its own scope = 2) +
# inner lambda's own predicate/expression scope (3) = \t3 for the wrap.
# ---------------------------------------------------------------------------

_DEPENDENT_LAMBDA_SRC = """\
axdef
  f : N +-> P N
where
  true
end

zed
  forall m : N |
    lambda s : dom f | lambda e : f(s) | e > 0 land
      s > 0 . s + e
end
"""


def test_dependent_lambda_chain_indents_one_level_per_lambda() -> None:
    r"""A dependent-domain lambda chain nested under forall indents \t3.

    forall contributes one level; each lambda in the dependency-stop chain
    (the outer prefix and the recursed-into inner lambda) contributes one
    level each, so the wrap inside the innermost lambda's predicate sits at
    forall-depth (1) + 2 lambdas = \\t3.
    """
    tex = _tex(_DEPENDENT_LAMBDA_SRC)
    assert r"\t3 s > 0 @ s + e" in tex, (
        f"expected dependent lambda chain wrap at \\t3 (monotonic, one level"
        f" per lambda): {tex!r}"
    )
