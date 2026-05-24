"""Regression tests for WYSIWYG pipe-break in semicolon-chained quantifiers.

Change: ``_parse_quantifier_continuation`` now honours a natural newline or
explicit ``\\`` continuation after ``|``, mirroring the single-binding path
in ``_parse_quantifier``.

Previously the chained form (``forall x : T; y : U | body``) silently
collapsed the newline and emitted a single-line result even when the source
author placed a line break after ``|``.  The single-binding form already
worked; this regression suite guards all four quantifier types and both
continuation styles.

Tests are grouped by quantifier type and then by continuation style:
- backslash continuation (``|\\``)
- bare WYSIWYG newline (``|\n``)

Additional groups:
- constraint+body form (``| constraint . expr``) — bullet break
- dependency-stop path — inner Quantifier node carries the flag
- mu chain — ``| pred . expr`` flag survives chain collapse
- single-decl control — the existing single-decl path must be unaffected
"""

from __future__ import annotations

from txt2tex.ast_nodes import Document
from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _expr(src: str, *, use_fuzz: bool = True) -> str:
    """Parse *src* as a txt2tex expression and return the generated LaTeX."""
    tokens = Lexer(src).tokenize()
    ast = Parser(tokens).parse()
    gen = LaTeXGenerator(use_fuzz=use_fuzz)
    if isinstance(ast, Document):
        return gen.generate_document(ast)
    return gen.generate_expr(ast)


# ---------------------------------------------------------------------------
# forall — two-decl chain
# ---------------------------------------------------------------------------


class TestForallTwoDeclPipeBreak:
    r"""Semicolon-chained forall honours ``\`` and natural newline after ``|``."""

    def test_backslash_continuation_emits_break(self) -> None:
        r"""Explicit ``\`` after ``|`` in two-decl forall emits ``\\``+indent."""
        result = _expr("forall x : N; y : N |\\\n  x < y")
        assert r"\\" in result, f"Expected line-break marker in: {result!r}"
        assert r"\t1" in result or "\\t1" in result, (
            f"Expected \\t1 indent in: {result!r}"
        )

    def test_natural_newline_emits_break(self) -> None:
        r"""Bare newline after ``|`` in two-decl forall emits ``\\``+indent."""
        result = _expr("forall x : N; y : N |\n  x < y")
        assert r"\\" in result, f"Expected line-break marker in: {result!r}"

    def test_backslash_continuation_body_present(self) -> None:
        r"""Body expression appears after the break in the emitted LaTeX."""
        result = _expr("forall x : N; y : N |\\\n  x < y")
        assert r"x < y" in result, f"Expected body in output: {result!r}"

    def test_no_break_single_line(self) -> None:
        r"""Single-line form (no continuation after ``|``) stays on one line."""
        result = _expr("forall x : N; y : N | x < y")
        # No backslash-backslash in the output — single-line form
        assert r"\\" not in result, f"Unexpected break in single-line form: {result!r}"

    def test_spivey_form_preserved_with_break(self) -> None:
        r"""Spivey collapse still fires: one ``\forall`` with semicolon."""
        result = _expr("forall x : N; y : N |\n  x < y")
        assert result.count(r"\forall") == 1, (
            f"Expected single \\forall, got: {result!r}"
        )
        assert r"\nat; y : \nat" in result, (
            f"Expected semicolon-joined declarations: {result!r}"
        )


# ---------------------------------------------------------------------------
# forall — three-decl chain
# ---------------------------------------------------------------------------


class TestForallThreeDeclPipeBreak:
    r"""Three-binding forall also honours pipe-break."""

    def test_backslash_emits_break(self) -> None:
        r"""Explicit ``\`` after ``|`` in three-decl forall emits ``\\``."""
        result = _expr("forall x : N; y : N; z : N |\\\n  x < y")
        assert r"\\" in result, f"Expected line-break in: {result!r}"

    def test_natural_newline_emits_break(self) -> None:
        """Natural newline after ``|`` in three-decl forall emits break."""
        result = _expr("forall x : N; y : N; z : N |\n  x < y")
        assert r"\\" in result, f"Expected line-break in: {result!r}"

    def test_spivey_form_preserved(self) -> None:
        """Three-decl output still contains two semicolons."""
        result = _expr("forall x : N; y : N; z : N |\n  x < y")
        assert r"\nat; y : \nat; z : \nat" in result, (
            f"Expected three-decl Spivey form: {result!r}"
        )


# ---------------------------------------------------------------------------
# exists — two-decl chain
# ---------------------------------------------------------------------------


class TestExistsTwoDeclPipeBreak:
    r"""Semicolon-chained exists honours ``\`` and natural newline after ``|``."""

    def test_backslash_continuation_emits_break(self) -> None:
        r"""Explicit ``\`` after ``|`` in two-decl exists emits ``\\``+indent."""
        result = _expr("exists x : N; y : N |\\\n  x < y")
        assert r"\\" in result, f"Expected line-break in: {result!r}"

    def test_natural_newline_emits_break(self) -> None:
        """Natural newline after ``|`` in two-decl exists emits break."""
        result = _expr("exists x : N; y : N |\n  x < y")
        assert r"\\" in result, f"Expected line-break in: {result!r}"

    def test_no_break_single_line(self) -> None:
        """Single-line exists form has no backslash-backslash."""
        result = _expr("exists x : N; y : N | x < y")
        assert r"\\" not in result, f"Unexpected break in single-line form: {result!r}"

    def test_spivey_form_preserved(self) -> None:
        """Two-decl exists collapses to one ``\\exists`` with semicolon."""
        result = _expr("exists x : N; y : N |\n  x < y")
        assert result.count(r"\exists") == 1, (
            f"Expected single \\exists, got: {result!r}"
        )


# ---------------------------------------------------------------------------
# exists1 — two-decl chain
# ---------------------------------------------------------------------------


class TestExistsOneTwoDeclPipeBreak:
    r"""Semicolon-chained exists1 honours ``\`` and natural newline after ``|``."""

    def test_backslash_continuation_emits_break(self) -> None:
        r"""Explicit ``\`` after ``|`` in two-decl exists1 emits ``\\``."""
        result = _expr("exists1 x : N; y : N |\\\n  x < y")
        assert r"\\" in result, f"Expected line-break in: {result!r}"

    def test_natural_newline_emits_break(self) -> None:
        """Natural newline after ``|`` in two-decl exists1 emits break."""
        result = _expr("exists1 x : N; y : N |\n  x < y")
        assert r"\\" in result, f"Expected line-break in: {result!r}"

    def test_no_break_single_line(self) -> None:
        """Single-line exists1 form has no backslash-backslash."""
        result = _expr("exists1 x : N; y : N | x < y")
        assert r"\\" not in result, f"Unexpected break: {result!r}"


# ---------------------------------------------------------------------------
# mu — two-decl chain
# ---------------------------------------------------------------------------


class TestMuTwoDeclPipeBreak:
    r"""Semicolon-chained mu honours ``\`` and natural newline after ``|``."""

    def test_backslash_continuation_emits_break(self) -> None:
        r"""Explicit ``\`` after ``|`` in two-decl mu emits ``\\``."""
        result = _expr("(mu x : N; y : N |\\\n  x = y . (x + 0))")
        assert r"\\" in result, f"Expected line-break in: {result!r}"

    def test_natural_newline_emits_break(self) -> None:
        """Natural newline after ``|`` in two-decl mu emits break."""
        result = _expr("(mu x : N; y : N |\n  x = y . (x + 0))")
        assert r"\\" in result, f"Expected line-break in: {result!r}"

    def test_no_break_single_line(self) -> None:
        """Single-line mu form has no backslash-backslash."""
        result = _expr("(mu x : N; y : N | x = y . (x + 0))")
        assert r"\\" not in result, f"Unexpected break: {result!r}"

    def test_mu_parenthesized(self) -> None:
        """Mu result is parenthesized in fuzz mode regardless of line break."""
        result = _expr("(mu x : N; y : N |\n  x = y . (x + 0))")
        assert result.startswith("("), f"Expected leading '(': {result!r}"
        assert result.endswith(")"), f"Expected trailing ')': {result!r}"


# ---------------------------------------------------------------------------
# Constraint + body form: | pred . expr
# ---------------------------------------------------------------------------


class TestChainedConstraintBulletBreak:
    r"""``| constraint . expr`` form with bullet continuation in chained quantifier."""

    def test_forall_bullet_break_after_constraint(self) -> None:
        r"""Natural newline after ``.`` in chained forall emits ``\\`` before expr."""
        result = _expr("forall x : N; y : N | x > 0 .\n  x < y")
        assert r"\\" in result, f"Expected bullet line-break in: {result!r}"

    def test_forall_backslash_bullet_break(self) -> None:
        r"""Explicit ``\`` after ``.`` in chained forall emits ``\\``."""
        result = _expr("forall x : N; y : N | x > 0 .\\\n  x < y")
        assert r"\\" in result, f"Expected bullet break in: {result!r}"

    def test_forall_no_break_bullet_single_line(self) -> None:
        """Single-line ``| pred . expr`` has no backslash-backslash."""
        result = _expr("forall x : N; y : N | x > 0 . x < y")
        assert r"\\" not in result, f"Unexpected break: {result!r}"

    def test_exists_bullet_break(self) -> None:
        r"""Natural newline after ``.`` in chained exists emits ``\\``."""
        result = _expr("exists x : N; y : N | x > 0 .\n  x < y")
        assert r"\\" in result, f"Expected bullet break in: {result!r}"


# ---------------------------------------------------------------------------
# Dependency-stop path — inner Quantifier carries the flag
# ---------------------------------------------------------------------------


class TestDependencyStopInnerFlag:
    r"""When chain stops at a dependency, the inner Quantifier's flags survive.

    ``forall s : N; e : f(s) | ...`` triggers the dependency-stop code in
    ``_collect_quantifier_chain``.  The innermost returned is ``current``,
    which is the node that stopped the chain — its ``line_break_after_pipe``
    must propagate to the emitted output.
    """

    def test_inner_flag_reaches_output(self) -> None:
        r"""Pipe-break flag on dependency-stop inner Quantifier survives."""
        # f(s) references s, so the chain stops at s.
        # The inner Quantifier (e : f(s)) carries line_break_after_pipe.
        src = (
            "axdef\n"
            "  f : N +-> N\n"
            "where\n"
            "  true\n"
            "end\n"
            "zed\n"
            "  forall s : N | forall e : f(s) |\n"
            "    s = e\n"
            "end"
        )
        tokens = Lexer(src).tokenize()
        ast = Parser(tokens).parse()
        gen = LaTeXGenerator(use_fuzz=True)
        assert isinstance(ast, Document)
        latex = gen.generate_document(ast)
        assert r"\\" in latex, f"Expected break from inner flag in: {latex!r}"


# ---------------------------------------------------------------------------
# Single-decl control — existing path must be unaffected
# ---------------------------------------------------------------------------


class TestSingleDeclUnaffected:
    r"""Single-decl quantifiers route through ``_generate_quantifier``, not the chain.

    These tests confirm the chain change did not inadvertently alter
    single-binding behaviour (regression guard for lines 1601-1698).
    """

    def test_forall_single_decl_no_break(self) -> None:
        """Single-decl forall without continuation stays on one line."""
        result = _expr("forall x : N | x > 0")
        assert result == r"\forall x : \nat @ x > 0", (
            f"Single-decl forall changed: {result!r}"
        )

    def test_forall_single_decl_pipe_break(self) -> None:
        r"""Single-decl forall with ``\`` after ``|`` still emits break."""
        result = _expr("forall x : N |\\\n  x > 0")
        assert r"\\" in result, f"Expected break in single-decl pipe-break: {result!r}"

    def test_exists_single_decl_no_break(self) -> None:
        """Single-decl exists without continuation is unchanged."""
        result = _expr("exists x : N | x > 0")
        assert result == r"\exists x : \nat @ x > 0", (
            f"Single-decl exists changed: {result!r}"
        )

    def test_exists1_single_decl_no_break(self) -> None:
        """Single-decl exists1 without continuation is unchanged."""
        result = _expr("exists1 x : N | x > 0")
        assert result == r"\exists_1 x : \nat @ x > 0", (
            f"Single-decl exists1 changed: {result!r}"
        )

    def test_mu_single_decl_no_break(self) -> None:
        """Single-decl mu without continuation is unchanged."""
        result = _expr("(mu x : N | x > 0)")
        # Parenthesized, pipe separator
        assert r"\mu x : \nat | x > 0" in result, f"Single-decl mu changed: {result!r}"


# ---------------------------------------------------------------------------
# Output shape: flag emits ``@ \\`` then ``\t1`` indent
# ---------------------------------------------------------------------------


class TestOutputShape:
    r"""The emitted break is ``@ \\`` followed by a newline and ``\t1``."""

    def test_forall_bullet_sep_with_break(self) -> None:
        r"""Two-decl forall pipe-break emits ``@ \\`` then ``\t1`` body."""
        result = _expr("forall x : N; y : N |\n  x < y")
        # bullet_sep is @ in fuzz mode; break inserts \\ then \t1
        assert "@ \\\\" in result, f"Expected '@ \\\\' in: {result!r}"

    def test_forall_t1_indent_follows_break(self) -> None:
        r"""``\t1`` appears after the break marker."""
        result = _expr("forall x : N; y : N |\n  x < y")
        # \t1 follows the newline
        assert "\\t1" in result, f"Expected \\t1 indent in: {result!r}"
