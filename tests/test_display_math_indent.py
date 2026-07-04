"""Regression tests: display-math indentation matches the Z-paragraph form.

jms ruling (see mission for fix/display-math-binding-indent): layout is not
semantically significant in Z (Z RM §6), so a wrapped set comprehension must
indent identically whether it renders inside a Z paragraph (``zed``/``schema``/
``axdef``, ``self._in_z_paragraph is True``) or inside display math (an
inline ``$...$`` span used when the expression is RA-tainted — a binding
``\\lblot ... \\rblot`` yield, a relational-algebra construct, or a reference
to an RA-tainted name).

Before this fix, display math used two divergent mechanisms:

1. Each comprehension wrapped *itself* in its own ``\\begin{array}{l}`` and
   broke with a bare ``\\\\`` (no ``\\t{depth}``), while any conjunction or
   quantifier break nested inside still emitted ``\\t{depth}`` — producing
   *mixed* indentation within one comprehension body.
2. Nested comprehensions each emitted their own array, so the absolute
   ``\\t{depth}`` values did not share a common left margin (ragged, not
   monotonic).

After the fix, a comprehension's own break uses ``_get_indentation()``
unconditionally (same as the Z-paragraph path), and exactly one
``\\begin{array}{l}`` wraps the entire display expression — emitted once by
the caller (the bare top-level document-item emitter, or the RA-tainted
abbreviation emitter), never by the comprehension itself.
"""

from __future__ import annotations

import re

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


def _tab_sequence(tex: str, start_marker: str, end_marker: str) -> list[str]:
    """Return the ordered list of \\t{n} prefixes between two markers.

    Extracts the fragment between the first occurrence of ``start_marker``
    and the first subsequent occurrence of ``end_marker``, then returns every
    ``\\t{n}`` token found in it, in source order.  Used to compare the
    binding-depth prefix sequence of two differently-wrapped renderings of
    the same body line-for-line.
    """
    start = tex.index(start_marker)
    end = tex.index(end_marker, start)
    fragment = tex[start:end]
    return re.findall(r"\\t\d+", fragment)


# A comprehension whose predicate contains a *nested* comprehension (the
# shape that used to trigger self-wrapping arrays at every level) and whose
# yield differs only in its final term: a plain projection in the zed form,
# a binding (\lblot ... \rblot) in the two display forms.  The binding is
# what forces display math — fuzz never parses \lblot inside a zed box.
_ZED_SRC = """\
zed
  Ref == { p : Property | (sum({ i : Invoice | i.propertyId = p.propertyId .
        i.amount }) > 100) .
      p.propertyId }
end
"""

# Same body, no enclosing zed/end -- a bare top-level expression document
# item, yielding a binding instead of a plain projection.  Routes through
# the bare-expr fallback (txt2tex.codegen._dispatch.generate_document_item).
_BARE_DISPLAY_SRC = """\
{ p : Property | (sum({ i : Invoice | i.propertyId = p.propertyId .
      i.amount }) > 100) .
    {| propertyId == p.propertyId |} }
"""

# Same body again, this time as a named abbreviation -- RA-tainted because
# the RHS yields a Binding.  Routes through
# txt2tex.codegen.paragraphs._generate_abbreviation's display-math branch.
_ABBREV_DISPLAY_SRC = """\
Disp == { p : Property | (sum({ i : Invoice | i.propertyId = p.propertyId .
      i.amount }) > 100) .
    {| propertyId == p.propertyId |} }
"""


def test_bare_display_math_tab_sequence_matches_zed() -> None:
    r"""The bare top-level display form indents identically to the zed form.

    Both bodies share the same predicate structure (an inner comprehension
    nested inside a `sum(...)` call).  The ``\t{depth}`` sequence must match
    line-for-line; only the final yielded term's *text* may differ (a plain
    projection vs. a binding).
    """
    zed_tex = _tex(_ZED_SRC)
    bare_tex = _tex(_BARE_DISPLAY_SRC)

    zed_tabs = _tab_sequence(zed_tex, r"\begin{zed}", r"\end{zed}")
    bare_tabs = _tab_sequence(bare_tex, r"\begin{array}{l}", r"\end{array}$")

    assert bare_tabs == zed_tabs, (
        f"display \\t sequence {bare_tabs!r} does not match zed \\t sequence"
        f" {zed_tabs!r}\nzed:\n{zed_tex}\nbare display:\n{bare_tex}"
    )


def test_abbrev_display_math_tab_sequence_matches_zed() -> None:
    r"""The RA-tainted abbreviation display form indents identically to zed."""
    zed_tex = _tex(_ZED_SRC)
    abbrev_tex = _tex(_ABBREV_DISPLAY_SRC)

    zed_tabs = _tab_sequence(zed_tex, r"\begin{zed}", r"\end{zed}")
    abbrev_tabs = _tab_sequence(abbrev_tex, r"\begin{array}{l}", r"\end{array}$")

    assert abbrev_tabs == zed_tabs, (
        f"display \\t sequence {abbrev_tabs!r} does not match zed \\t sequence"
        f" {zed_tabs!r}\nzed:\n{zed_tex}\nabbrev display:\n{abbrev_tex}"
    )


def test_bare_display_math_has_exactly_one_array() -> None:
    r"""Exactly one \begin{array} wraps the whole display expression.

    Before the fix, the outer bare-expr wrapper and the inner comprehension's
    self-wrap each emitted their own array, nesting two (or more, one per
    nested comprehension) inside a single ``$...$`` span.
    """
    tex = _tex(_BARE_DISPLAY_SRC)
    assert tex.count(r"\begin{array}") == 1, (
        f"expected exactly one \\begin{{array}}, found"
        f" {tex.count(r'\begin{array}')}: {tex!r}"
    )


def test_abbrev_display_math_has_exactly_one_array() -> None:
    r"""Exactly one \begin{array} wraps the whole abbreviation RHS."""
    tex = _tex(_ABBREV_DISPLAY_SRC)
    assert tex.count(r"\begin{array}") == 1, (
        f"expected exactly one \\begin{{array}}, found"
        f" {tex.count(r'\begin{array}')}: {tex!r}"
    )


def test_bare_display_math_yield_line_matches_sibling_depth() -> None:
    r"""The yielded binding sits at the same \t{depth} as its sibling lines.

    The zed form's final line is ``\t1 p.propertyId ~\}`` (depth 1, the
    comprehension's own binding level).  The display form's yield is a
    binding at the same depth -- only the yielded text differs.
    """
    tex = _tex(_BARE_DISPLAY_SRC)
    assert r"\t1 \lblot~propertyId == p.propertyId~\rblot ~\}" in tex, (
        f"expected the yielded binding at \\t1 (matching the zed form's"
        f" \\t1 p.propertyId): {tex!r}"
    )
    # And the inner comprehension's own yield line keeps its \t2, exactly as
    # in the zed form -- the bug used to drop this indentation entirely.
    assert r"\t2 i.amount ~\}" in tex, (
        f"expected inner comprehension yield at \\t2 (matching zed): {tex!r}"
    )


def test_zed_path_unchanged() -> None:
    r"""The (already-correct) zed rendering is untouched by this fix."""
    tex = _tex(_ZED_SRC)
    assert (
        r"Ref == \{~ p : Property | (sum(\{~ i : Invoice |"
        r" i.propertyId = p.propertyId @ \\" in tex
    )
    assert r"\t2 i.amount ~\}) > 100) @ \\" in tex
    assert r"\t1 p.propertyId ~\}" in tex
