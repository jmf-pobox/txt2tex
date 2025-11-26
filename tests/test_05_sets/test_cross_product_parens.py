"""Test for cross product parenthesization elem type contexts.

Bug: Nested cross products lose parentheses when used as type parameters,
causing fuzz type checking errors.

Example:
    Input:  seq((ShowId cross EpisodeId) cross N)
    Wrong:  \\seq (ShowId \\cross EpisodeId \\cross N)
    Right:  \\seq ((ShowId \\cross EpisodeId) \\cross N)
"""

from __future__ import annotations

from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser


def test_nested_cross_in_seq_fuzz() -> None:
    """Test that nested cross products are parenthesized elem seq type with fuzz."""
    txt = "Playlist == seq((ShowId cross EpisodeId) cross N)"
    lexer = Lexer(txt)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    doc = parser.parse()
    generator = LaTeXGenerator(use_fuzz=True)
    latex = generator.generate_document(doc)
    assert (
        "\\seq~((ShowId \\cross EpisodeId) \\cross" in latex
        or "\\seq~((ShowId \\cross EpisodeId) \\cross \\nat)" in latex
    ), f"Expected parenthesized cross product, got: {latex}"


def test_nested_cross_in_seq_standard() -> None:
    """Test nested cross products are parenthesized elem seq (standard LaTeX)."""
    txt = "Playlist == seq((ShowId cross EpisodeId) cross N)"
    lexer = Lexer(txt)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    doc = parser.parse()
    generator = LaTeXGenerator(use_fuzz=False)
    latex = generator.generate_document(doc)
    assert (
        "\\seq~((ShowId \\cross EpisodeId) \\cross" in latex
        or "\\seq~((ShowId \\cross EpisodeId) \\cross \\nat)" in latex
    ), f"Expected parenthesized cross product, got: {latex}"


def test_triple_cross_product() -> None:
    """Test triple cross product: A cross B cross C stays flat (no auto parens)."""
    txt = "Type == A cross B cross C"
    lexer = Lexer(txt)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    doc = parser.parse()
    generator = LaTeXGenerator(use_fuzz=True)
    latex = generator.generate_document(doc)
    assert "A \\cross B \\cross C" in latex, (
        f"Expected flat 3-tuple (no auto parens), got: {latex}"
    )


def test_cross_in_axdef() -> None:
    """Test cross product elem axdef declaration."""
    txt = "axdef\n  f : (A cross B) cross C -> D\nwhere\n  true\nend"
    lexer = Lexer(txt)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    doc = parser.parse()
    generator = LaTeXGenerator(use_fuzz=True)
    latex = generator.generate_document(doc)
    assert "(A \\cross B) \\cross C" in latex, (
        f"Expected parenthesized cross product elem function type, got: {latex}"
    )
