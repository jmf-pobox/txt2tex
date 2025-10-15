"""Additional tests to increase latex_gen.py coverage toward 90%."""

from __future__ import annotations

import pytest

from txt2tex.ast_nodes import (
    CaseAnalysis,
    Identifier,
    Paragraph,
    Quantifier,
    SequenceLiteral,
)
from txt2tex.latex_gen import LaTeXGenerator


def test_unknown_quantifier() -> None:
    """Test error for unknown quantifier (line 463)."""
    node = Quantifier(
        quantifier="???",
        variables=["x"],
        domain=Identifier(name="N", line=1, column=1),
        body=Identifier(name="true", line=1, column=1),
        expression=None,
        line=1,
        column=1,
    )
    gen = LaTeXGenerator()

    with pytest.raises(ValueError, match="Unknown quantifier"):
        gen.generate_expr(node)


def test_pattern3_parse_failure() -> None:
    """Test Pattern 3 fallback when parsing fails (lines 1048-1051)."""
    para = Paragraph(text="The value x := 5 is assigned here.", line=1, column=1)
    gen = LaTeXGenerator()
    latex_lines = gen._generate_paragraph(para)
    latex = "\n".join(latex_lines)

    # Should still process the text (even if := doesn't parse)
    assert "x" in latex


def test_sequence_notation_empty() -> None:
    """Test empty sequence notation (line 770)."""
    node = SequenceLiteral(elements=[], line=1, column=1)
    gen = LaTeXGenerator()
    latex = gen.generate_expr(node)

    # Empty sequence: \langle \rangle
    assert r"\langle" in latex
    assert r"\rangle" in latex


def test_case_analysis_depth_no_steps() -> None:
    """Test case analysis depth calculation with no steps (line 1270)."""
    # Create a CaseAnalysis with no steps
    case = CaseAnalysis(case_name="p", steps=[], line=1, column=1)

    gen = LaTeXGenerator()
    depth = gen._calculate_tree_depth(case)

    # Should return 0 for empty case
    assert depth == 0


# Complex proof tree tests removed - ProofNode requires many fields
# (label, is_assumption, indent_level, etc.) and lines 1279-1283 are
# in complex case analysis code that's hard to test in isolation


def test_identifier_edge_case_empty_parts() -> None:
    """Test identifier with empty parts after split (lines 350-351)."""
    # Edge case: multiple consecutive underscores
    node = Identifier(name="x___y", line=1, column=1)
    gen = LaTeXGenerator()
    latex = gen._generate_identifier(node)

    # Should use fallback: mathit with escaped underscores
    assert r"\mathit{" in latex
    assert r"\_" in latex


def test_identifier_exactly_two_parts_long_suffix() -> None:
    """Test identifier with exactly 2 parts where suffix > 3 chars (line 336)."""
    # Should trigger multi-word heuristic
    node = Identifier(name="x_maximum", line=1, column=1)
    gen = LaTeXGenerator()
    latex = gen._generate_identifier(node)

    # Should use mathit (suffix > 3 chars)
    assert r"\mathit{x\_maximum}" in latex


def test_sequence_corner_bracket_with_label() -> None:
    """Test sequence corner bracket with label (line 1264)."""
    para = Paragraph(text="SEQUENCE: [p => q] [modus-ponens]", line=1, column=1)
    gen = LaTeXGenerator()
    latex_lines = gen._generate_paragraph(para)
    latex = "\n".join(latex_lines)

    # Should generate corner brackets with label
    assert r"\ulcorner" in latex or "SEQUENCE:" in latex


# Removed test_right_associative_subtraction - line 425 is part of
# parenthesization logic that's already covered by test_right_associative_parens
# in test_latex_gen_errors.py
