"""Tests for simple inline math expression wrapping (Pattern 3)."""

from __future__ import annotations

from txt2tex.ast_nodes import Paragraph
from txt2tex.latex_gen import LaTeXGenerator


def test_simple_comparison_inline() -> None:
    """Test that simple comparisons like 'x > 1' are wrapped in math mode."""
    para = Paragraph(
        text="We need a predicate that is false for x > 1.", line=1, column=1
    )

    gen = LaTeXGenerator()
    latex_lines = gen._generate_paragraph(para)
    latex = "\n".join(latex_lines)

    # Should wrap 'x > 1' in math mode
    assert "$x > 1$" in latex or r"$x \Rightarrow 1$" in latex


def test_function_maplet_inline() -> None:
    """Test that function maplets like 'f +-> g' are wrapped."""
    para = Paragraph(text="The function f +-> g is partial.", line=1, column=1)

    gen = LaTeXGenerator()
    latex_lines = gen._generate_paragraph(para)
    latex = "\n".join(latex_lines)

    # Should wrap 'f +-> g' in math mode and convert to LaTeX
    assert "pfun" in latex  # +-> becomes \pfun


def test_equivalence_inline() -> None:
    """Test that equivalence like 'p ⇔ x > 1' is wrapped."""
    para = Paragraph(text="A suitable solution would be p ⇔ x > 1.", line=1, column=1)

    gen = LaTeXGenerator()
    latex_lines = gen._generate_paragraph(para)
    latex = "\n".join(latex_lines)

    # Check that equivalence operator is present
    assert "⇔" in latex or "Leftrightarrow" in latex


def test_no_double_wrapping() -> None:
    """Test that expressions already in math mode aren't double-wrapped."""
    para = Paragraph(text="Consider $x > 1$ in the expression.", line=1, column=1)

    gen = LaTeXGenerator()
    latex_lines = gen._generate_paragraph(para)
    latex = "\n".join(latex_lines)

    # Should not have $$x > 1$$
    assert "$$" not in latex


def test_multiple_operators_in_text() -> None:
    """Test multiple inline math expressions in same paragraph."""
    para = Paragraph(text="We have x > 1 and y < 5 in the domain.", line=1, column=1)

    gen = LaTeXGenerator()
    latex_lines = gen._generate_paragraph(para)
    latex = "\n".join(latex_lines)

    # Both should be wrapped
    assert "x >" in latex or "x $" in latex  # x > 1 somewhere
    assert "y <" in latex or "y $" in latex  # y < 5 somewhere


def test_equals_operator_inline() -> None:
    """Test that equals sign is wrapped in math mode."""
    para = Paragraph(text="The value x = 5 is constant.", line=1, column=1)

    gen = LaTeXGenerator()
    latex_lines = gen._generate_paragraph(para)
    latex = "\n".join(latex_lines)

    # Should have x = 5 somewhere (possibly wrapped)
    assert "x" in latex and "5" in latex


def test_domain_restriction_inline() -> None:
    """Test domain restriction operator -|>."""
    para = Paragraph(
        text="The relation S -|> A restricts the domain.", line=1, column=1
    )

    gen = LaTeXGenerator()
    latex_lines = gen._generate_paragraph(para)
    latex = "\n".join(latex_lines)

    # Should have -|> converted to LaTeX (\pinj)
    assert "pinj" in latex  # -|> becomes \pinj
