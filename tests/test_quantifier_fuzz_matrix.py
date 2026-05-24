"""Fuzz round-trip regression suite for the full quantifier form matrix.

Locks in fuzz acceptance for every combination of:
  quantifier  x {forall, exists, exists1, mu, lambda}
  arity       x {single (1 var), two-decl, three-decl}
  bullet      x {no-bullet (predicate only), with-bullet (predicate + body)}

The matrix yields 24 test cases.  Lambda and mu require a body expression
(Z RM §3.12), so the no-bullet form is invalid Z and omitted — 6 cases
skipped by design.  Forall, exists, and exists1 are predicates, not
expressions; their "with-bullet" form uses a second predicate after @,
not a body expression.

All tests skip when the fuzz binary is absent from PATH (mirrors the
pattern in tests/test_08_functions/test_lambda_multidecl_fuzz.py).

Test naming: test_<quant>_<arity>_<bullet>_fuzz_clean
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


def _fuzz_available() -> bool:
    """Return True if the fuzz binary is on PATH."""
    return shutil.which("fuzz") is not None


def _gen_doc(src: str) -> str:
    """Parse txt2tex document source and return the full LaTeX document."""
    tokens = Lexer(src).tokenize()
    ast = Parser(tokens).parse()
    assert isinstance(ast, Document)
    return LaTeXGenerator(use_fuzz=True).generate_document(ast)


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


def _assert_fuzz_clean(tex: str, tmp_path: Path, label: str) -> None:
    """Assert fuzz returns exit code 0 for the given LaTeX source."""
    result = _run_fuzz(tex, tmp_path)
    assert result.returncode == 0, (
        f"fuzz rejected {label}\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )


# ---------------------------------------------------------------------------
# forall — predicate quantifier; no-bullet = @pred, with-bullet = |guard @pred
# Context: zed environment (predicate position)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not _fuzz_available(), reason="fuzz binary not on PATH")
class TestForallFuzz:
    """Fuzz acceptance for all forall arity x bullet combinations."""

    def test_forall_single_no_bullet_fuzz_clean(self, tmp_path: Path) -> None:
        r"""Single-decl forall without guard emits \forall x : \nat @ x > 0."""
        tex = _gen_doc("zed\n  forall x : N | x > 0\nend")
        _assert_fuzz_clean(tex, tmp_path, "forall single no-bullet")

    def test_forall_single_with_bullet_fuzz_clean(self, tmp_path: Path) -> None:
        r"""Single-decl forall with guard emits \forall x : \nat | x > 0 @ (x > 0)."""
        tex = _gen_doc("zed\n  forall x : N | x > 0 . (x > 0)\nend")
        _assert_fuzz_clean(tex, tmp_path, "forall single with-bullet")

    def test_forall_two_decl_no_bullet_fuzz_clean(self, tmp_path: Path) -> None:
        r"""Two-decl forall emits \forall x : \nat; y : \nat @ x < y."""
        tex = _gen_doc("zed\n  forall x : N; y : N | x < y\nend")
        _assert_fuzz_clean(tex, tmp_path, "forall two-decl no-bullet")

    def test_forall_two_decl_with_bullet_fuzz_clean(self, tmp_path: Path) -> None:
        r"""Two-decl forall with guard: \forall x : \nat; y : \nat | x < y @ (x < y).

        Full Spivey form: guard separates declarations from body predicate.
        """
        tex = _gen_doc("zed\n  forall x : N; y : N | x < y . (x < y)\nend")
        _assert_fuzz_clean(tex, tmp_path, "forall two-decl with-bullet")

    def test_forall_three_decl_no_bullet_fuzz_clean(self, tmp_path: Path) -> None:
        r"""Three-decl forall emits \forall x : \nat; y : \nat; z : \nat @ x < y."""
        tex = _gen_doc("zed\n  forall x : N; y : N; z : N | x < y\nend")
        _assert_fuzz_clean(tex, tmp_path, "forall three-decl no-bullet")

    def test_forall_three_decl_with_bullet_fuzz_clean(self, tmp_path: Path) -> None:
        r"""Three-decl forall: three-var semicolon form with body predicate."""
        tex = _gen_doc("zed\n  forall x : N; y : N; z : N | x < y . (x < y)\nend")
        _assert_fuzz_clean(tex, tmp_path, "forall three-decl with-bullet")


# ---------------------------------------------------------------------------
# exists — predicate quantifier; same bullet semantics as forall
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not _fuzz_available(), reason="fuzz binary not on PATH")
class TestExistsFuzz:
    """Fuzz acceptance for all exists arity x bullet combinations."""

    def test_exists_single_no_bullet_fuzz_clean(self, tmp_path: Path) -> None:
        r"""Single-decl exists without guard emits \exists x : \nat @ x > 0."""
        tex = _gen_doc("zed\n  exists x : N | x > 0\nend")
        _assert_fuzz_clean(tex, tmp_path, "exists single no-bullet")

    def test_exists_single_with_bullet_fuzz_clean(self, tmp_path: Path) -> None:
        r"""Single-decl exists with guard emits \exists x : \nat | x > 0 @ (x > 0)."""
        tex = _gen_doc("zed\n  exists x : N | x > 0 . (x > 0)\nend")
        _assert_fuzz_clean(tex, tmp_path, "exists single with-bullet")

    def test_exists_two_decl_no_bullet_fuzz_clean(self, tmp_path: Path) -> None:
        r"""Two-decl exists emits \exists x : \nat; y : \nat @ x < y."""
        tex = _gen_doc("zed\n  exists x : N; y : N | x < y\nend")
        _assert_fuzz_clean(tex, tmp_path, "exists two-decl no-bullet")

    def test_exists_two_decl_with_bullet_fuzz_clean(self, tmp_path: Path) -> None:
        r"""Two-decl exists with guard: \exists x : \nat; y : \nat | x < y @ (x < y).

        Full Spivey form: guard separates declarations from body predicate.
        """
        tex = _gen_doc("zed\n  exists x : N; y : N | x < y . (x < y)\nend")
        _assert_fuzz_clean(tex, tmp_path, "exists two-decl with-bullet")

    def test_exists_three_decl_no_bullet_fuzz_clean(self, tmp_path: Path) -> None:
        r"""Three-decl exists emits \exists x : \nat; y : \nat; z : \nat @ x < y."""
        tex = _gen_doc("zed\n  exists x : N; y : N; z : N | x < y\nend")
        _assert_fuzz_clean(tex, tmp_path, "exists three-decl no-bullet")

    def test_exists_three_decl_with_bullet_fuzz_clean(self, tmp_path: Path) -> None:
        r"""Three-decl exists: three-var semicolon form with body predicate."""
        tex = _gen_doc("zed\n  exists x : N; y : N; z : N | x < y . (x < y)\nend")
        _assert_fuzz_clean(tex, tmp_path, "exists three-decl with-bullet")


# ---------------------------------------------------------------------------
# exists1 — predicate quantifier; same bullet semantics as forall/exists
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not _fuzz_available(), reason="fuzz binary not on PATH")
class TestExists1Fuzz:
    """Fuzz acceptance for all exists1 arity x bullet combinations."""

    def test_exists1_single_no_bullet_fuzz_clean(self, tmp_path: Path) -> None:
        r"""Single-decl exists1 without guard emits \exists_1 x : \nat @ x > 0."""
        tex = _gen_doc("zed\n  exists1 x : N | x > 0\nend")
        _assert_fuzz_clean(tex, tmp_path, "exists1 single no-bullet")

    def test_exists1_single_with_bullet_fuzz_clean(self, tmp_path: Path) -> None:
        r"""Single-decl exists1 with guard emits \exists_1 x : \nat | x > 0 @ (x > 0).

        Guard separates the declaration from the body predicate.
        """
        tex = _gen_doc("zed\n  exists1 x : N | x > 0 . (x > 0)\nend")
        _assert_fuzz_clean(tex, tmp_path, "exists1 single with-bullet")

    def test_exists1_two_decl_no_bullet_fuzz_clean(self, tmp_path: Path) -> None:
        r"""Two-decl exists1 emits \exists_1 x : \nat; y : \nat @ x < y."""
        tex = _gen_doc("zed\n  exists1 x : N; y : N | x < y\nend")
        _assert_fuzz_clean(tex, tmp_path, "exists1 two-decl no-bullet")

    def test_exists1_two_decl_with_bullet_fuzz_clean(self, tmp_path: Path) -> None:
        r"""Two-decl exists1 with guard: \exists_1 x : \nat; y : \nat | x < y @ (x < y).

        Full Spivey form with three-var declarations.
        """
        tex = _gen_doc("zed\n  exists1 x : N; y : N | x < y . (x < y)\nend")
        _assert_fuzz_clean(tex, tmp_path, "exists1 two-decl with-bullet")

    def test_exists1_three_decl_no_bullet_fuzz_clean(self, tmp_path: Path) -> None:
        r"""Three-decl exists1 emits \exists_1 x : \nat; y : \nat; z : \nat @ x < y."""
        tex = _gen_doc("zed\n  exists1 x : N; y : N; z : N | x < y\nend")
        _assert_fuzz_clean(tex, tmp_path, "exists1 three-decl no-bullet")

    def test_exists1_three_decl_with_bullet_fuzz_clean(self, tmp_path: Path) -> None:
        r"""Three-decl exists1: three-var semicolon form with body predicate."""
        tex = _gen_doc("zed\n  exists1 x : N; y : N; z : N | x < y . (x < y)\nend")
        _assert_fuzz_clean(tex, tmp_path, "exists1 three-decl with-bullet")


# ---------------------------------------------------------------------------
# mu — expression quantifier; body is mandatory (no-bullet form omitted)
# Context: axdef where clause (expression position)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not _fuzz_available(), reason="fuzz binary not on PATH")
class TestMuFuzz:
    """Fuzz acceptance for all mu arity x with-bullet combinations.

    Mu without a body expression is not valid Z (Z RM §3.12), so no-bullet
    variants are omitted from this class.
    """

    def test_mu_single_with_bullet_fuzz_clean(self, tmp_path: Path) -> None:
        r"""Single-decl mu emits (\mu x : \nat | x > 0 @ x)."""
        tex = _gen_doc("axdef\n  k : N\nwhere\n  k = (mu x : N | x > 0 . x)\nend")
        _assert_fuzz_clean(tex, tmp_path, "mu single with-bullet")

    def test_mu_two_decl_with_bullet_fuzz_clean(self, tmp_path: Path) -> None:
        r"""Two-decl mu emits (\mu x : \nat; y : \nat | x = y @ x)."""
        tex = _gen_doc(
            "axdef\n  k : N\nwhere\n  k = (mu x : N; y : N | x = y . x)\nend"
        )
        _assert_fuzz_clean(tex, tmp_path, "mu two-decl with-bullet")

    def test_mu_three_decl_with_bullet_fuzz_clean(self, tmp_path: Path) -> None:
        r"""Three-decl mu emits (\mu x : \nat; y : \nat; z : \nat | x = y @ x)."""
        tex = _gen_doc(
            "axdef\n  k : N\nwhere\n  k = (mu x : N; y : N; z : N | x = y . x)\nend"
        )
        _assert_fuzz_clean(tex, tmp_path, "mu three-decl with-bullet")


# ---------------------------------------------------------------------------
# lambda — expression quantifier; body is mandatory (no-bullet form omitted)
# Context: axdef where clause (expression position)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not _fuzz_available(), reason="fuzz binary not on PATH")
class TestLambdaFuzz:
    """Fuzz acceptance for all lambda arity x with-bullet combinations.

    Lambda without a body expression is not valid Z (Z RM §3.12), so no-bullet
    variants are omitted from this class.
    """

    def test_lambda_single_with_bullet_fuzz_clean(self, tmp_path: Path) -> None:
        r"""Single-decl lambda emits (\lambda x : \nat | x > 0 @ x)."""
        tex = _gen_doc(
            "axdef\n  f : N -> N\nwhere\n  f = (lambda x : N | x > 0 . x)\nend"
        )
        _assert_fuzz_clean(tex, tmp_path, "lambda single with-bullet")

    def test_lambda_two_decl_with_bullet_fuzz_clean(self, tmp_path: Path) -> None:
        r"""Two-decl lambda emits (\lambda x : \nat; y : \nat | x = y @ x)."""
        src = (
            "axdef\n  f : N cross N -> N\nwhere\n"
            "  f = (lambda x : N; y : N | x = y . x)\nend"
        )
        tex = _gen_doc(src)
        _assert_fuzz_clean(tex, tmp_path, "lambda two-decl with-bullet")

    def test_lambda_three_decl_with_bullet_fuzz_clean(self, tmp_path: Path) -> None:
        r"""Three-decl lambda: (\lambda x : \nat; y : \nat; z : \nat | x = y @ x)."""
        src = (
            "axdef\n  f : N cross N cross N -> N\nwhere\n"
            "  f = (lambda x : N; y : N; z : N | x = y . x)\nend"
        )
        tex = _gen_doc(src)
        _assert_fuzz_clean(tex, tmp_path, "lambda three-decl with-bullet")
