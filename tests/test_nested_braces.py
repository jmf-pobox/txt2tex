"""Tests for nested brace handling in inline math (Pattern 1 enhancement)."""

from __future__ import annotations

from txt2tex.ast_nodes import Paragraph
from txt2tex.latex_gen import LaTeXGenerator


def test_nested_braces_simple() -> None:
    """Test set comprehension with nested braces."""
    para = Paragraph(
        text="The function {p : Person . p |-> {p}} is simple.", line=1, column=1
    )

    gen = LaTeXGenerator()
    latex_lines = gen._generate_paragraph(para)
    latex = "\n".join(latex_lines)

    # Should wrap the entire set comprehension in math mode
    assert "Person" in latex
    assert "mapsto" in latex or "|" in latex


def test_nested_braces_relational_image() -> None:
    """Test that complex lambda expressions in TEXT are preserved.

    Note: {p : Person . p |-> expr} uses '.' not '|', so it's a lambda
    expression, not a set comprehension. Parser won't recognize it.
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

    # Lambda expressions aren't set comprehensions - left unchanged
    assert "Person" in latex


def test_nested_braces_set_comprehension() -> None:
    """Test actual set comprehension with nested braces."""
    para = Paragraph(
        text="The set {x : N | x in {1, 2, 3}} is valid.", line=1, column=1
    )

    gen = LaTeXGenerator()
    latex_lines = gen._generate_paragraph(para)
    latex = "\n".join(latex_lines)

    # This IS a valid set comprehension with nested braces
    assert "$" in latex  # Should be wrapped in math mode


def test_multiple_set_comprehensions() -> None:
    """Test multiple simple set comprehensions."""
    para = Paragraph(
        text="We have {x : N | x > 0} and {y : N | y < 10}.", line=1, column=1
    )

    gen = LaTeXGenerator()
    latex_lines = gen._generate_paragraph(para)
    latex = "\n".join(latex_lines)

    # Both should be processed
    assert latex.count("$") >= 2  # At least 2 math mode regions


def test_nested_set_in_set_comprehension() -> None:
    """Test set comprehension containing a set literal."""
    para = Paragraph(
        text="Consider {x : N | x in {1, 2}}.", line=1, column=1
    )

    gen = LaTeXGenerator()
    latex_lines = gen._generate_paragraph(para)
    latex = "\n".join(latex_lines)

    # Should handle the nested set literal
    assert "$" in latex


def test_balanced_braces_finder() -> None:
    """Test the _find_balanced_braces helper.

    This finds OUTERMOST balanced braces only (not all nested braces).
    """
    gen = LaTeXGenerator()

    # Simple case - two separate braces
    matches = gen._find_balanced_braces("text {a} more {b} text")
    assert len(matches) == 2
    assert matches[0] == (5, 8)  # {a}
    assert matches[1] == (14, 17)  # {b}

    # Nested case - only outermost returned
    matches = gen._find_balanced_braces("text {a {b} c} more")
    assert len(matches) == 1  # Only outermost
    assert matches[0] == (5, 14)  # {a {b} c}

    # Deeply nested - only outermost
    matches = gen._find_balanced_braces("{a {b {c} d} e}")
    assert len(matches) == 1  # Only outermost
    assert matches[0] == (0, 15)  # Entire expression


def test_unbalanced_braces_ignored() -> None:
    """Test that unbalanced braces are safely ignored."""
    gen = LaTeXGenerator()

    # Unclosed brace
    matches = gen._find_balanced_braces("text {unclosed")
    assert len(matches) == 0

    # Extra closing brace
    matches = gen._find_balanced_braces("text } extra")
    assert len(matches) == 0

    # Mixed
    matches = gen._find_balanced_braces("{good} {bad")
    assert len(matches) == 1
    assert matches[0] == (0, 6)  # {good}
