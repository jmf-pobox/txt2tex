"""Tests for brace handling in TEXT prose (escape-only mode).

In escape-only mode, bare { } in prose are escaped to \\{ \\}.
Set comprehensions in prose pass through with escaped braces; use
explicit $...$ to trigger the full parser pipeline.
"""

from __future__ import annotations

from txt2tex.ast_nodes import Paragraph
from txt2tex.latex_gen import LaTeXGenerator


def test_nested_braces_simple() -> None:
    """Set comprehension with nested braces passes through as escaped prose."""
    para = Paragraph(
        text="The function {p : Person . p |-> {p}} is simple.", line=1, column=1
    )
    gen = LaTeXGenerator()
    latex_lines = gen._generate_paragraph(para)
    latex = "\n".join(latex_lines)
    assert "Person" in latex
    assert "mapsto" in latex or "|" in latex


def test_nested_braces_relational_image() -> None:
    """Complex lambda expressions in TEXT are preserved with escaped braces.

    Note: {p : Person . p |-> expr} uses '.' not '|', so it's a lambda
    expression, not a set comprehension. Parser won't recognise it.
    These belong in axdef blocks, not TEXT paragraphs.
    """
    para = Paragraph(
        text="Define children = {p : Person . p |-> parentOf(| {p} |)}.",
        line=1,
        column=1,
    )
    gen = LaTeXGenerator()
    latex_lines = gen._generate_paragraph(para)
    latex = "\n".join(latex_lines)
    assert "Person" in latex


def test_nested_braces_set_comprehension() -> None:
    """Bare {x : N | x elem {1, 2, 3}} in TEXT has braces escaped."""
    para = Paragraph(
        text="The set {x : N | x elem {1, 2, 3}} is valid.", line=1, column=1
    )
    gen = LaTeXGenerator()
    latex_lines = gen._generate_paragraph(para)
    latex = "\n".join(latex_lines)
    # Escape-only: braces are escaped, content preserved.
    assert "\\{" in latex
    assert "N" in latex
    assert "1, 2, 3" in latex


def test_multiple_set_comprehensions() -> None:
    """Multiple bare set comprehensions in TEXT have their braces escaped."""
    para = Paragraph(
        text="We have {x : N | x > 0} and {y : N | y < 10}.", line=1, column=1
    )
    gen = LaTeXGenerator()
    latex_lines = gen._generate_paragraph(para)
    latex = "\n".join(latex_lines)
    # Escape-only: both brace pairs are escaped, content preserved.
    assert latex.count("\\{") >= 2
    assert "x > 0" in latex
    assert "y < 10" in latex


def test_nested_set_in_set_comprehension() -> None:
    """Set comprehension containing a set literal has braces escaped."""
    para = Paragraph(text="Consider {x : N | x elem {1, 2}}.", line=1, column=1)
    gen = LaTeXGenerator()
    latex_lines = gen._generate_paragraph(para)
    latex = "\n".join(latex_lines)
    assert "\\{" in latex
    assert "1, 2" in latex
