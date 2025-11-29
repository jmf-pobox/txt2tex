"""Tests for identifier underscore handling coverage."""

from __future__ import annotations

from txt2tex.ast_nodes import Identifier
from txt2tex.latex_gen import LaTeXGenerator


def test_multi_word_identifier_long_prefix() -> None:
    """Test multi-word identifier with long prefix (>3 chars)."""
    node = Identifier(name="cumulative_total", line=1, column=1)
    gen = LaTeXGenerator()
    latex = gen._generate_identifier(node)

    # Should use mathit with escaped underscore
    assert latex == r"\mathit{cumulative\_total}"


def test_multi_word_identifier_long_suffix() -> None:
    """Test multi-word identifier with long suffix (>3 chars)."""
    node = Identifier(name="max_value", line=1, column=1)
    gen = LaTeXGenerator()
    latex = gen._generate_identifier(node)

    # Should use mathit with escaped underscore
    assert latex == r"\mathit{max\_value}"


def test_single_char_subscript() -> None:
    """Test subscript with single character after underscore."""
    node = Identifier(name="x_1", line=1, column=1)
    gen = LaTeXGenerator()
    latex = gen._generate_identifier(node)

    # Should use subscript notation without braces
    assert latex == "x_1"


def test_multi_char_subscript() -> None:
    """Test subscript with multiple characters after underscore."""
    node = Identifier(name="state_init", line=1, column=1)
    gen = LaTeXGenerator()
    latex = gen._generate_identifier(node)

    # Could be subscript with braces or mathit depending on length
    assert "state_{init}" in latex or r"\mathit{state\_init}" in latex


def test_three_part_identifier() -> None:
    """Test identifier with multiple underscores (fallback case)."""
    node = Identifier(name="a_b_c", line=1, column=1)
    gen = LaTeXGenerator()
    latex = gen._generate_identifier(node)

    # Should use fallback: mathit with escaped underscores
    assert latex == r"\mathit{a\_b\_c}"


def test_identifier_no_underscore() -> None:
    """Test identifier without underscore."""
    node = Identifier(name="simple", line=1, column=1)
    gen = LaTeXGenerator()
    latex = gen._generate_identifier(node)

    # Should return as-is
    assert latex == "simple"
