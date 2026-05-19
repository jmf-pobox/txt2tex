"""Fuzz round-trip tests for multi-declaration lambda expressions.

These tests exercise the full txt2tex → fuzz pipeline for the Spivey-canonical
multi-decl lambda form introduced in Phase 3.2.

The canonical form (Z RM §3.12):

    (\\lambda s : S; c : C | predicate @ expression)

Both two-decl and three-decl chains are covered.  Each test generates LaTeX
via LaTeXGenerator(use_fuzz=True), writes it to a temp file, invokes fuzz,
and asserts a clean exit.
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


def _make_axdef_tex(decl: str, predicate: str) -> str:
    """Wrap decl + predicate in an axdef body for fuzz type checking."""
    body = f"\\begin{{axdef}}\n{decl}\n\\where\n{predicate}\n\\end{{axdef}}"
    return _FUZZ_PREAMBLE.format(body=body)


def _gen_latex(src: str) -> str:
    """Parse txt2tex source and return generated LaTeX (document wrapper included)."""
    tokens = Lexer(src).tokenize()
    ast = Parser(tokens).parse()
    assert isinstance(ast, Document)
    gen = LaTeXGenerator(use_fuzz=True)
    return gen.generate_document(ast)


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
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not _fuzz_available(), reason="fuzz binary not on PATH")
class TestMultiDeclLambdaFuzz:
    """Fuzz type-check acceptance for multi-decl lambda Spivey canonical form."""

    def test_two_decl_lambda_fuzz_clean(self, tmp_path: Path) -> None:
        """Two-decl lambda (nat types) passes fuzz type check.

        Generated LaTeX: (\\lambda a : \\nat; b : \\nat | a = b @ a)
        """
        tex = _make_axdef_tex(
            decl=r"  f : \nat \cross \nat \fun \nat",
            predicate=r"  f = (\lambda a : \nat; b : \nat | a = b @ a)",
        )
        result = _run_fuzz(tex, tmp_path)
        assert result.returncode == 0, (
            f"fuzz rejected two-decl lambda\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )

    def test_three_decl_lambda_fuzz_clean(self, tmp_path: Path) -> None:
        """Three-decl lambda (nat types) passes fuzz type check.

        Generated LaTeX: (\\lambda a : \\nat; b : \\nat; c : \\nat | a = b @ a)
        """
        tex = _make_axdef_tex(
            decl=r"  f : \nat \cross \nat \cross \nat \fun \nat",
            predicate=r"  f = (\lambda a : \nat; b : \nat; c : \nat | a = b @ a)",
        )
        result = _run_fuzz(tex, tmp_path)
        assert result.returncode == 0, (
            f"fuzz rejected three-decl lambda\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )

    def test_txt2tex_pipeline_two_decl(self, tmp_path: Path) -> None:
        """Full pipeline: txt2tex source → LaTeX → fuzz type check.

        Input uses N (mapped to \\nat by the generator) to produce valid fuzz.
        The predicate ends with an arithmetic expression ``x + 0 = y + 0`` so
        the dot separator is unambiguously a bullet, not a field projection.
        """
        txt_src = """\
axdef
  f : N cross N -> N
where
  f = lambda x : N; y : N | x + 0 = y + 0 . x
end
"""
        full_tex = _gen_latex(txt_src)
        result = _run_fuzz(full_tex, tmp_path)
        assert result.returncode == 0, (
            f"fuzz rejected full-pipeline two-decl lambda\n"
            f"tex:\n{full_tex}\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )
