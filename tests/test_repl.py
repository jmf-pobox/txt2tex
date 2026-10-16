"""Tests for txt2tex interactive REPL module."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from txt2tex.ast_nodes import Document
from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser
from txt2tex.repl import (
    BLOCK_KEYWORDS,
    BLOCK_START_WORDS,
    generate_preview_document,
    is_block_input,
    process_input,
    repl_main,
)


class TestIsBlockInput:
    """Tests for block input detection."""

    @pytest.mark.parametrize(
        "text",
        [
            "PROOF:",
            "proof:",
            "PROOF: something",
            "ARGUE:",
            "EQUIV:",
            "TRUTH TABLE:",
            "TEXT:",
            "PURETEXT:",
            "LATEX:",
            "INFRULE:",
            "SYNTAX:",
        ],
    )
    def test_block_keywords_detected(self, text: str) -> None:
        """Block keywords should be detected as multi-line input."""
        assert is_block_input(text) is True

    @pytest.mark.parametrize(
        "text",
        [
            "schema Foo",
            "axdef",
            "gendef",
            "given A, B",
            "zed",
            "syntax",
        ],
    )
    def test_block_start_words_detected(self, text: str) -> None:
        """Block start words should be detected as multi-line input."""
        assert is_block_input(text) is True

    @pytest.mark.parametrize(
        "text",
        [
            "forall x : N | x > 0",
            "p land q",
            "1 + 2",
            "x = y",
            "",
            "   ",
        ],
    )
    def test_expressions_not_detected_as_blocks(self, text: str) -> None:
        """Single expressions should not be detected as blocks."""
        assert is_block_input(text) is False

    def test_block_keywords_constant(self) -> None:
        """BLOCK_KEYWORDS should contain expected keywords."""
        assert "PROOF:" in BLOCK_KEYWORDS
        assert "EQUIV:" in BLOCK_KEYWORDS
        assert "TRUTH TABLE:" in BLOCK_KEYWORDS

    def test_block_start_words_constant(self) -> None:
        """BLOCK_START_WORDS should contain expected words."""
        assert "schema" in BLOCK_START_WORDS
        assert "axdef" in BLOCK_START_WORDS
        assert "given" in BLOCK_START_WORDS


class TestGeneratePreviewDocument:
    """Tests for preview document generation."""

    def test_generates_valid_document_with_fuzz(self) -> None:
        """Should generate valid LaTeX document with fuzz package."""
        fragment = r"$\forall x : \nat \spot x \geq 0$"
        doc = generate_preview_document(fragment, use_fuzz=True)

        assert r"\documentclass" in doc
        assert r"\usepackage{fuzz}" in doc
        assert r"\begin{document}" in doc
        assert fragment in doc
        assert r"\end{document}" in doc

    def test_generates_valid_document_with_zed(self) -> None:
        """Should generate valid LaTeX document with zed-cm package."""
        fragment = r"$x + y$"
        doc = generate_preview_document(fragment, use_fuzz=False)

        assert r"\usepackage{zed-cm}" in doc
        assert r"\usepackage{fuzz}" not in doc

    def test_includes_required_packages(self) -> None:
        """Should include all required packages."""
        doc = generate_preview_document("test", use_fuzz=True)

        assert r"\usepackage{amssymb}" in doc
        assert r"\usepackage{adjustbox}" in doc
        assert r"\usepackage{zed-maths}" in doc
        assert r"\usepackage{zed-proof}" in doc


class TestProcessInput:
    """Tests for input processing."""

    def test_process_simple_expression(self) -> None:
        """Should process a simple expression."""
        generator = LaTeXGenerator(use_fuzz=True)
        result = process_input(
            "forall x : N | x > 0",
            generator,
            latex_only=True,
        )
        assert result is True

    def test_process_invalid_input(self) -> None:
        """Should handle invalid input gracefully."""
        generator = LaTeXGenerator(use_fuzz=True)
        # Invalid syntax - unclosed parenthesis
        result = process_input(
            "(((invalid",
            generator,
            latex_only=True,
        )
        assert result is False

    def test_process_inline_math_error_is_clean(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """A strict $...$ error in a TEXT block is handled cleanly, no traceback."""
        generator = LaTeXGenerator(use_fuzz=True)
        result = process_input(
            r"TEXT: bad $n \geq 0$ here.",
            generator,
            latex_only=True,
        )
        assert result is False
        err = capsys.readouterr().err
        assert "Error:" in err
        assert "whiteboard notation only" in err
        assert "Traceback" not in err

    def test_process_truth_table(self) -> None:
        """Should process a truth table."""
        generator = LaTeXGenerator(use_fuzz=True)
        text = """TRUTH TABLE:
p | q | p land q
T | T | T
T | F | F
F | T | F
F | F | F"""
        result = process_input(text, generator, latex_only=True)
        assert result is True

    def test_process_ra_in_zed_error_is_clean(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """An RA construct inside a `zed` block is handled cleanly, no traceback."""
        generator = LaTeXGenerator(use_fuzz=True)
        text = """given T
axdef
  S : T <-> T
  U : T <-> T
end

zed
  RJoin == S join U
end"""
        result = process_input(text, generator, latex_only=True)
        assert result is False
        err = capsys.readouterr().err
        assert "Error:" in err
        assert "cannot appear inside" in err
        assert "`zed`" in err
        assert "Traceback" not in err

    def test_process_numeric_superscript_error_is_clean(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """A numeric `^` base inside an axdef block is handled cleanly, no traceback.

        Regression: NumericSuperscriptError was uncaught in the REPL, so a
        typed axdef/schema/gendef/abbreviation block reaching this error
        printed a raw traceback instead of one clean 'Error: line N: ...'
        line.  This block-input text goes through the same
        `isinstance(ast, Document)` -> `generate_fragment` branch the CLI's
        `generate_document` exercises (an axdef/schema/gendef keyword, or
        `Name ==`, always parses to a `Document` -- see
        `test_process_numeric_superscript_bare_expression_is_unaffected`
        below for the REPL's other branch, which never reaches this check).
        """
        generator = LaTeXGenerator(use_fuzz=True)
        text = "axdef\n  x : N\nwhere\n  x^2 > 0\nend"
        result = process_input(text, generator, latex_only=True)
        assert result is False
        err = capsys.readouterr().err
        assert "Error:" in err
        assert "iter 2 x" in err
        assert "Traceback" not in err
        assert "NumericSuperscriptError" not in err

    def test_process_numeric_superscript_bare_expression_is_unaffected(self) -> None:
        """A bare single-line `^` expression never reaches the checker.

        `process_input` routes a non-`Document` AST (a lone expression with
        no trailing newline, e.g. typed alone at the `>>>` prompt) through
        `generator.generate_expr` directly -- it never enters
        `generate_document_item`, so it never reaches
        `_emit_hidden_abbreviation` (the standalone-comprehension hook) or
        any axdef/schema/gendef/abbreviation handler.  `x^2` alone at the
        prompt must render, not raise.
        """
        generator = LaTeXGenerator(use_fuzz=True)
        result = process_input("x^2", generator, latex_only=True)
        assert result is True

    def test_process_with_pdf_generation(self, tmp_path: Path) -> None:
        """Should attempt PDF generation when temp_dir provided."""
        generator = LaTeXGenerator(use_fuzz=True)

        # Mock compile_pdf to avoid actual compilation
        with patch("txt2tex.repl.compile_pdf", return_value=False):
            result = process_input(
                "x = y",
                generator,
                latex_only=False,
                temp_dir=tmp_path,
            )
            # Should fail because compile_pdf returns False
            assert result is False


class TestGenerateFragment:
    """Tests for LaTeXGenerator.generate_fragment method."""

    def test_generate_fragment_simple(self) -> None:
        """Should generate fragment without document wrapper."""
        # Use a solution block so parser returns Document
        text = """** Solution 1 **
forall x : N | x > 0"""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        generator = LaTeXGenerator(use_fuzz=True)
        assert isinstance(ast, Document)
        fragment = generator.generate_fragment(ast)

        # Should contain math but not document structure
        assert r"\forall" in fragment
        assert r"\documentclass" not in fragment
        assert r"\begin{document}" not in fragment

    def test_generate_fragment_schema(self) -> None:
        """Should generate schema fragment."""
        text = """schema Foo
  x : N
where
  x > 0
end"""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        generator = LaTeXGenerator(use_fuzz=True)
        assert isinstance(ast, Document)
        fragment = generator.generate_fragment(ast)

        assert r"\begin{schema}" in fragment
        assert r"\end{schema}" in fragment


class TestClearCommand:
    """Tests for the .clear REPL command."""

    @staticmethod
    def _run_clear(
        monkeypatch: pytest.MonkeyPatch,
        system: str,
        error: OSError | None = None,
    ) -> list[list[str]]:
        """Drive repl_main with .clear then EOF; return recorded argvs."""
        calls: list[list[str]] = []

        def fake_run(cmd: list[str], **_kwargs: object) -> None:
            calls.append(cmd)
            if error is not None:
                raise error

        inputs = iter([".clear"])

        def fake_input(_prompt: str) -> str:
            try:
                return next(inputs)
            except StopIteration:
                raise EOFError from None

        monkeypatch.setattr("txt2tex.repl.subprocess.run", fake_run)
        monkeypatch.setattr("txt2tex.repl.platform.system", lambda: system)
        monkeypatch.setattr("builtins.input", fake_input)
        assert repl_main() == 0
        return calls

    def test_clear_posix_runs_clear(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """On non-Windows, .clear runs ['clear'] without a shell."""
        assert self._run_clear(monkeypatch, "Linux") == [["clear"]]

    def test_clear_windows_runs_comspec_cls(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """On Windows, .clear runs %COMSPEC% /c cls (cls is a cmd builtin)."""
        sentinel = r"C:\sentinel\cmd.exe"
        monkeypatch.setenv("COMSPEC", sentinel)
        assert self._run_clear(monkeypatch, "Windows") == [[sentinel, "/c", "cls"]]

    def test_clear_windows_without_comspec_uses_systemroot(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """With COMSPEC unset, .clear derives cmd.exe from %SystemRoot%."""
        monkeypatch.delenv("COMSPEC", raising=False)
        monkeypatch.setenv("SYSTEMROOT", r"D:\Windows")
        assert self._run_clear(monkeypatch, "Windows") == [
            [r"D:\Windows\System32\cmd.exe", "/c", "cls"]
        ]

    def test_clear_windows_without_comspec_or_systemroot_uses_c_windows(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """With COMSPEC and SystemRoot unset, .clear falls back to C:\\Windows."""
        monkeypatch.delenv("COMSPEC", raising=False)
        monkeypatch.delenv("SYSTEMROOT", raising=False)
        assert self._run_clear(monkeypatch, "Windows") == [
            [r"C:\Windows\System32\cmd.exe", "/c", "cls"]
        ]

    @pytest.mark.parametrize("error", [FileNotFoundError(), PermissionError()])
    def test_clear_survives_unexecutable_clear(
        self, monkeypatch: pytest.MonkeyPatch, error: OSError
    ) -> None:
        """A missing or unexecutable clear must not crash the REPL."""
        assert self._run_clear(monkeypatch, "Linux", error) == [["clear"]]
