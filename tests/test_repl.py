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

