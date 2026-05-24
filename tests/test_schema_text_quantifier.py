"""Tests for schema-text quantification (Z RM §3.10).

The four binding forms:
    exists Delta S | P   →  \\exists \\Delta S @ P    (fuzz)
    exists Xi S | P      →  \\exists \\Xi S @ P       (fuzz)
    exists S | P         →  \\exists S @ P             (fuzz)
    exists S' | P        →  \\exists S^{\\prime} @ P  (fuzz)

The same forms apply to forall and exists1.

AST contract: Quantifier.schema_binding is a SchemaBinding instance;
Quantifier.variables is [] and Quantifier.domain is None.

Regression contract: the existing value-binding quantifier path is
unaffected.  Tests in this module include dedicated regression cases.

Fuzz round-trip tests use a miniature promotion schema (BoxOffice +
Promote) that mirrors SBM Ex 21 in structure.  They skip when the fuzz
binary is absent from PATH.
"""

from __future__ import annotations

import contextlib
import shutil
import subprocess
from pathlib import Path

import pytest

from txt2tex.ast_nodes import Document, Quantifier, SchemaBinding
from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_expr(src: str) -> Quantifier:
    """Parse *src* as a single quantifier expression."""
    tokens = Lexer(src).tokenize()
    ast = Parser(tokens).parse()
    assert isinstance(ast, Quantifier), f"Expected Quantifier, got {type(ast).__name__}"
    return ast


def _gen_expr(src: str, *, use_fuzz: bool = True) -> str:
    """Parse *src* as a txt2tex expression and return the generated LaTeX."""
    tokens = Lexer(src).tokenize()
    ast = Parser(tokens).parse()
    gen = LaTeXGenerator(use_fuzz=use_fuzz)
    if isinstance(ast, Document):
        return gen.generate_document(ast)
    return gen.generate_expr(ast)


def _gen_doc(src: str) -> str:
    """Parse a txt2tex document source and return the full LaTeX document."""
    tokens = Lexer(src).tokenize()
    ast = Parser(tokens).parse()
    assert isinstance(ast, Document)
    return LaTeXGenerator(use_fuzz=True).generate_document(ast)


def _fuzz_available() -> bool:
    """Return True if the fuzz binary is on PATH."""
    return shutil.which("fuzz") is not None


def _run_fuzz(tex: str, tmp_path: Path) -> subprocess.CompletedProcess[str]:
    """Write *tex* to a temp file and run fuzz on it."""
    fuzz_bin = shutil.which("fuzz")
    assert fuzz_bin is not None
    tex_file = tmp_path / "test.tex"
    tex_file.write_text(tex, encoding="utf-8")
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
# AST shape tests — verify schema_binding is populated correctly
# ---------------------------------------------------------------------------


class TestAST:
    """Verify the AST shape for every schema-text binding form."""

    def test_exists_delta_s_ast(self) -> None:
        """exists Delta S | P → SchemaBinding(decoration='Delta', schema_name='S')."""
        node = _parse_expr("exists Delta S | true")
        assert node.schema_binding is not None
        assert node.schema_binding.decoration == "Delta"
        assert node.schema_binding.schema_name == "S"
        assert node.variables == []
        assert node.domain is None
        assert node.quantifier == "exists"

    def test_exists_xi_s_ast(self) -> None:
        """exists Xi S | P → SchemaBinding(decoration='Xi', schema_name='S')."""
        node = _parse_expr("exists Xi S | true")
        assert node.schema_binding is not None
        assert node.schema_binding.decoration == "Xi"
        assert node.schema_binding.schema_name == "S"

    def test_exists_bare_s_ast(self) -> None:
        """exists S | P → SchemaBinding(decoration='None', schema_name='S')."""
        node = _parse_expr("exists S | true")
        assert node.schema_binding is not None
        assert node.schema_binding.decoration == "None"
        assert node.schema_binding.schema_name == "S"

    def test_exists_primed_s_ast(self) -> None:
        """exists S' | P → SchemaBinding(decoration='Prime', schema_name=\"S'\")."""
        node = _parse_expr("exists S' | true")
        assert node.schema_binding is not None
        assert node.schema_binding.decoration == "Prime"
        assert node.schema_binding.schema_name == "S'"

    def test_forall_delta_s_ast(self) -> None:
        """forall Delta S | P → SchemaBinding(decoration='Delta')."""
        node = _parse_expr("forall Delta S | true")
        assert node.schema_binding is not None
        assert node.schema_binding.decoration == "Delta"
        assert node.quantifier == "forall"

    def test_exists1_delta_s_ast(self) -> None:
        """exists1 Delta S | P → SchemaBinding(decoration='Delta')."""
        node = _parse_expr("exists1 Delta S | true")
        assert node.schema_binding is not None
        assert node.schema_binding.decoration == "Delta"
        assert node.quantifier == "exists1"

    def test_schema_binding_is_frozen(self) -> None:
        """SchemaBinding is immutable (frozen dataclass)."""
        sb = SchemaBinding(decoration="Delta", schema_name="S", line=0, column=0)
        with contextlib.suppress(AttributeError, TypeError):
            sb.schema_name = "T"  # type: ignore[misc]
        assert sb.schema_name == "S"


# ---------------------------------------------------------------------------
# LaTeX output tests (fuzz mode) — spot = @
# ---------------------------------------------------------------------------


class TestLaTeXFuzzMode:
    r"""Verify LaTeX output in fuzz mode for each schema binding form.

    In fuzz mode the bullet separator is ``@``, so the output is
    ``\exists \Delta S @ P`` rather than ``\exists \Delta S \bullet P``.
    """

    def test_exists_delta_s_latex(self) -> None:
        r"""exists Delta S | P → \exists \Delta S @ P."""
        latex = _gen_expr("exists Delta S | true")
        assert latex == r"\exists \Delta S @ true"

    def test_exists_xi_s_latex(self) -> None:
        r"""exists Xi S | P → \exists \Xi S @ P."""
        latex = _gen_expr("exists Xi S | true")
        assert latex == r"\exists \Xi S @ true"

    def test_exists_bare_s_latex(self) -> None:
        r"""exists S | P → \exists S @ P."""
        latex = _gen_expr("exists S | true")
        assert latex == r"\exists S @ true"

    def test_exists_primed_s_latex(self) -> None:
        r"""exists S' | P → \exists S^{\prime} @ P."""
        latex = _gen_expr("exists S' | true")
        assert latex == r"\exists S^{\prime} @ true"

    def test_forall_delta_s_latex(self) -> None:
        r"""forall Delta S | P → \forall \Delta S @ P."""
        latex = _gen_expr("forall Delta S | true")
        assert latex == r"\forall \Delta S @ true"

    def test_exists1_delta_s_latex(self) -> None:
        r"""exists1 Delta S | P → \exists_1 \Delta S @ P."""
        latex = _gen_expr("exists1 Delta S | true")
        assert latex == r"\exists_1 \Delta S @ true"

    def test_exists_xi_s_compound_body(self) -> None:
        r"""exists Xi S | x > 0 land y > 0 — compound body is generated correctly."""
        latex = _gen_expr("exists Xi S | x > 0 land y > 0")
        assert latex == r"\exists \Xi S @ x > 0 \land y > 0"


# ---------------------------------------------------------------------------
# LaTeX output tests (standard mode) — spot = \bullet
# ---------------------------------------------------------------------------


class TestLaTeXStandardMode:
    r"""Verify LaTeX output in standard (non-fuzz) mode.

    Bullet separator is ``\bullet`` and quantifier names map to
    ``\forall``, ``\exists``, ``\exists_1``.
    """

    def test_exists_delta_s_standard(self) -> None:
        r"""exists Delta S | P → \exists \Delta S \bullet P."""
        latex = _gen_expr("exists Delta S | true", use_fuzz=False)
        assert latex == r"\exists \Delta S \bullet true"

    def test_exists_bare_s_standard(self) -> None:
        r"""exists S | P → \exists S \bullet P."""
        latex = _gen_expr("exists S | true", use_fuzz=False)
        assert latex == r"\exists S \bullet true"


# ---------------------------------------------------------------------------
# Regression tests — value-binding path must be unchanged
# ---------------------------------------------------------------------------


class TestRegressionValueBinding:
    """Value-binding quantifiers must parse and generate as before."""

    def test_exists_value_binding_with_domain(self) -> None:
        r"""exists x : T | P → value binding; schema_binding is None."""
        node = _parse_expr("exists x : N | x > 0")
        assert node.schema_binding is None
        assert node.variables == ["x"]
        assert node.domain is not None

    def test_exists_value_binding_latex(self) -> None:
        r"""exists x : N | x > 0 → \exists x : \nat @ x > 0 (fuzz mode)."""
        latex = _gen_expr("exists x : N | x > 0")
        assert latex == r"\exists x : \nat @ x > 0"

    def test_forall_value_binding_multi_var(self) -> None:
        r"""forall x, y : N | x < y → value binding with two variables."""
        node = _parse_expr("forall x, y : N | x < y")
        assert node.schema_binding is None
        assert node.variables == ["x", "y"]

    def test_exists_no_domain_lowercase(self) -> None:
        r"""exists x | x > 0 — lowercase x without domain is a value binding."""
        node = _parse_expr("exists x | x > 0")
        assert node.schema_binding is None
        assert node.variables == ["x"]
        assert node.domain is None

    def test_nested_quantifier_schema_then_value(self) -> None:
        r"""exists Delta S | forall y : N | P — nested quantifier works."""
        latex = _gen_expr("exists Delta S | forall y : N | y > 0")
        assert r"\exists \Delta S @" in latex
        assert r"\forall y : \nat @ y > 0" in latex


# ---------------------------------------------------------------------------
# Fuzz round-trip tests — miniature promotion schema (mirrors SBM Ex 21)
# ---------------------------------------------------------------------------

_FUZZ_PREAMBLE = r"""\documentclass[a4paper]{article}
\usepackage{fuzz}
\begin{document}
"""
_FUZZ_SUFFIX = r"""
\end{document}
"""

# Miniature state schema: Counter with a simple increment operation.
# Using a pure state-change schema (no inputs) so schema-text quantification
# can be tested without needing extra declarations in scope.
_PROMOTION_SPEC = r"""
schema Counter
  n : N
where
  n >= 0
end
schema IncrCounter
  Delta Counter
where
  n' = n + 1
end
"""


@pytest.mark.skipif(not _fuzz_available(), reason="fuzz binary not on PATH")
class TestSchemaQuantifierFuzz:
    """Fuzz acceptance tests for schema-text quantification."""

    def test_exists_delta_fuzz_clean(self, tmp_path: Path) -> None:
        r"""exists Delta S | P typechecks under fuzz."""
        src = "zed\n  exists Delta Counter | true\nend"
        body = _gen_doc(_PROMOTION_SPEC + src)
        _assert_fuzz_clean(body, tmp_path, "exists Delta Counter")

    def test_exists_xi_fuzz_clean(self, tmp_path: Path) -> None:
        r"""exists Xi S | P typechecks under fuzz."""
        src = "zed\n  exists Xi Counter | true\nend"
        body = _gen_doc(_PROMOTION_SPEC + src)
        _assert_fuzz_clean(body, tmp_path, "exists Xi Counter")

    def test_exists_bare_fuzz_clean(self, tmp_path: Path) -> None:
        r"""exists S | P typechecks under fuzz."""
        src = "zed\n  exists Counter | true\nend"
        body = _gen_doc(_PROMOTION_SPEC + src)
        _assert_fuzz_clean(body, tmp_path, "exists Counter")

    def test_forall_delta_fuzz_clean(self, tmp_path: Path) -> None:
        r"""forall Delta S | P typechecks under fuzz."""
        src = "zed\n  forall Delta Counter | true\nend"
        body = _gen_doc(_PROMOTION_SPEC + src)
        _assert_fuzz_clean(body, tmp_path, "forall Delta Counter")

    def test_exists1_delta_fuzz_clean(self, tmp_path: Path) -> None:
        r"""exists1 Delta S | P typechecks under fuzz."""
        src = "zed\n  exists1 Delta Counter | true\nend"
        body = _gen_doc(_PROMOTION_SPEC + src)
        _assert_fuzz_clean(body, tmp_path, "exists1 Delta Counter")

    def test_promote_promotion_predicate_fuzz_clean(self, tmp_path: Path) -> None:
        r"""Miniature promotion predicate mirrors SBM Ex 21.

        Checks that ``exists Delta Counter | IncrCounter`` in a zed predicate
        position typechecks under fuzz.  This mirrors the promotion pattern:
        there exists a Counter state-change satisfying IncrCounter.
        """
        pred_src = "zed\n  exists Delta Counter | IncrCounter\nend"
        body = _gen_doc(_PROMOTION_SPEC + pred_src)
        _assert_fuzz_clean(body, tmp_path, "exists Delta Counter | IncrCounter")
