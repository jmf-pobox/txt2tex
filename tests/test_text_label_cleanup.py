"""Tests for text-and-label-cleanup fixes.

Covers four bug clusters fixed together:
  1. Sub-question label parser scope (DAT #1, #18): (word) only promotes to
     Part at paragraph start with a short structural label.
  2. TEXT-block keyword rewrites dropped (engine #136, DAT #11): bare English
     words like 'exists', 'forall', 'group', 'union' stay as text.
  3. Consecutive TEXT: directives coalesce into one paragraph (DAT #16).
  4. Heading text passes through verbatim via _escape_latex_text (DAT #15).
"""

from __future__ import annotations

import pytest

from txt2tex.ast_nodes import Document, Paragraph, Part
from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def parse_and_generate(source: str) -> tuple[Document, str]:
    """Parse source text and return (AST, LaTeX)."""
    tokens = Lexer(source).tokenize()
    result = Parser(tokens).parse()
    assert isinstance(result, Document)
    gen = LaTeXGenerator()
    latex = gen.generate_document(result)
    return result, latex


def parse_document(source: str) -> Document:
    """Parse source text and return the Document AST."""
    tokens = Lexer(source).tokenize()
    result = Parser(tokens).parse()
    assert isinstance(result, Document)
    return result


# ---------------------------------------------------------------------------
# 1. Part-label scope
# ---------------------------------------------------------------------------


class TestPartLabelScope:
    """Bug 1: (word) at paragraph start only becomes a Part for structural labels."""

    def test_single_letter_at_paragraph_start_is_part_label(self) -> None:
        """(a) at the start of a TEXT token becomes a Part node."""
        source = "TEXT: (a) This is part a content."
        ast = parse_document(source)
        assert len(ast.items) == 1
        item = ast.items[0]
        assert isinstance(item, Part)
        assert item.label == "a"
        assert len(item.items) == 1
        assert isinstance(item.items[0], Paragraph)
        assert "This is part a content" in item.items[0].text

    def test_parenthetical_mid_line_is_prose(self) -> None:
        """(underlined) mid-line inside TEXT prose stays as prose, not a Part."""
        source = "TEXT: Each primary key is highlighted (underlined) in the schema box."
        ast = parse_document(source)
        assert len(ast.items) == 1
        item = ast.items[0]
        assert isinstance(item, Paragraph)
        assert "(underlined)" in item.text

    def test_long_word_at_start_of_text_is_prose(self) -> None:
        """(underlined) at the very start of a TEXT value is NOT a Part."""
        source = "TEXT: (underlined) in the schema box means primary key."
        ast = parse_document(source)
        assert len(ast.items) == 1
        item = ast.items[0]
        # 'underlined' is not a single letter, digit, or short Roman numeral.
        assert isinstance(item, Paragraph)
        assert "(underlined)" in item.text

    def test_roman_numeral_at_paragraph_start_is_part(self) -> None:
        """(iii) at paragraph start is a valid structural label."""
        source = "TEXT: (iii) Third sub-point content here."
        ast = parse_document(source)
        item = ast.items[0]
        assert isinstance(item, Part)
        assert item.label == "iii"

    def test_digit_at_paragraph_start_is_part(self) -> None:
        """(1) at paragraph start is a valid structural label."""
        source = "TEXT: (1) First numbered item content."
        ast = parse_document(source)
        item = ast.items[0]
        assert isinstance(item, Part)
        assert item.label == "1"

    @pytest.mark.parametrize(
        "word",
        ["continued", "underlined", "optional", "example", "solution"],
    )
    def test_arbitrary_word_in_parens_is_prose(self, word: str) -> None:
        """Arbitrary parenthesised words at TEXT start remain prose."""
        source = f"TEXT: ({word}) some continuation text here."
        ast = parse_document(source)
        item = ast.items[0]
        assert isinstance(item, Paragraph), f"({word}) should be prose, not Part"


# ---------------------------------------------------------------------------
# 2. TEXT-block math rewrites are opt-in (via $...$)
# ---------------------------------------------------------------------------


class TestTextKeywordNotRewritten:
    """Bug 2: bare English keywords in TEXT prose stay as text."""

    def test_exists_stays_as_prose(self) -> None:
        """'exists' in TEXT prose is not converted to ∃."""
        _, latex = parse_and_generate(
            "TEXT: There exists a natural number greater than any given bound."
        )
        assert "exists" in latex
        assert "$\\exists$" not in latex

    def test_forall_stays_as_prose(self) -> None:
        """'forall' in TEXT prose is not converted to ∀."""
        _, latex = parse_and_generate(
            "TEXT: The forall quantifier ranges over all elements."
        )
        assert "forall" in latex
        assert "$\\forall$" not in latex

    def test_group_stays_as_prose(self) -> None:
        """'group' in TEXT prose is not converted to GROUP operator."""
        _, latex = parse_and_generate(
            "TEXT: Each group of students submits one assignment."
        )
        assert "group" in latex

    def test_union_stays_as_prose(self) -> None:
        """'union' in TEXT prose is not converted to a set-union glyph."""
        _, latex = parse_and_generate("TEXT: A union of sets combines their members.")
        assert "union" in latex

    def test_dollar_math_inline_still_works(self) -> None:
        """$\\exists$ inside TEXT prose still renders as a math glyph."""
        _, latex = parse_and_generate(
            "TEXT: The statement $\\exists x : \\nat | x > 0$ is trivially true."
        )
        assert "$\\exists x" in latex or "\\exists" in latex

    def test_dollar_forall_inline_still_works(self) -> None:
        """$\\forall$ inside TEXT prose renders as math."""
        _, latex = parse_and_generate("TEXT: We write $\\forall$ to mean for all.")
        assert "\\forall" in latex


# ---------------------------------------------------------------------------
# 3. Consecutive TEXT: directives coalesce
# ---------------------------------------------------------------------------


class TestTextCoalescing:
    """Bug 3: adjacent TEXT: directives merge into one paragraph."""

    def test_three_adjacent_lines_coalesce(self) -> None:
        """Three consecutive TEXT: lines (no blank between) become one Paragraph."""
        source = (
            "TEXT: First line of description.\n"
            "TEXT: Second line continues the thought.\n"
            "TEXT: Third line wraps up the sentence."
        )
        ast = parse_document(source)
        # All three lines coalesce into exactly one Paragraph.
        assert len(ast.items) == 1
        item = ast.items[0]
        assert isinstance(item, Paragraph)
        assert "First line" in item.text
        assert "Second line" in item.text
        assert "Third line" in item.text

    def test_blank_line_splits_paragraphs(self) -> None:
        """A blank line between two TEXT: lines produces two separate Paragraphs."""
        source = "TEXT: First paragraph text.\n\nTEXT: Second paragraph text."
        ast = parse_document(source)
        assert len(ast.items) == 2
        assert isinstance(ast.items[0], Paragraph)
        assert isinstance(ast.items[1], Paragraph)
        assert "First paragraph" in ast.items[0].text
        assert "Second paragraph" in ast.items[1].text

    def test_two_adjacent_lines_coalesce(self) -> None:
        """Two consecutive TEXT: lines merge into one paragraph."""
        source = "TEXT: Part one of the sentence.\nTEXT: Part two of the sentence."
        ast = parse_document(source)
        assert len(ast.items) == 1
        assert isinstance(ast.items[0], Paragraph)

    def test_coalesced_latex_has_no_bigskip_between_lines(self) -> None:
        """Coalesced TEXT: lines do not emit \\bigskip between the merged lines."""
        source = "TEXT: Line one.\nTEXT: Line two.\nTEXT: Line three."
        _, latex = parse_and_generate(source)
        # Only one \\noindent block for the merged paragraph.
        assert latex.count(r"\noindent") == 1

    def test_coalescing_stops_at_structural_token(self) -> None:
        """Coalescing stops when a non-TEXT structural token follows."""
        source = "TEXT: Text before schema.\nschema Foo\n  x : N\nend"
        ast = parse_document(source)
        # Should be a Paragraph followed by a Schema.
        assert len(ast.items) == 2
        assert isinstance(ast.items[0], Paragraph)


# ---------------------------------------------------------------------------
# 4. Heading text verbatim pass-through
# ---------------------------------------------------------------------------


class TestHeadingTextEscape:
    """Bug 4: heading text bypasses the math-token pipeline."""

    def test_hyphenated_heading_no_extra_spaces(self) -> None:
        """'=== Foreign-key constraints ===' renders with hyphen intact."""
        _, latex = parse_and_generate("=== Foreign-key constraints ===\n")
        # The title must contain the hyphen with no surrounding spaces added.
        assert "Foreign-key constraints" in latex
        assert "Foreign - key constraints" not in latex

    def test_parens_in_heading_no_padding(self) -> None:
        """'=== Part (a): Relation variables ===' renders verbatim."""
        _, latex = parse_and_generate("=== Part (a): Relation variables ===\n")
        assert "Part (a): Relation variables" in latex

    def test_ampersand_in_heading_is_escaped(self) -> None:
        """'=== A & B ===' escapes the ampersand for LaTeX safety."""
        _, latex = parse_and_generate("=== A & B ===\n")
        assert r"\section*{A \& B}" in latex

    def test_section_command_present(self) -> None:
        """Heading emits \\section*{...} wrapping the verbatim title."""
        _, latex = parse_and_generate("=== Foreign-key constraints ===\n")
        assert r"\section*{Foreign-key constraints}" in latex

    def test_colon_in_heading_no_padding(self) -> None:
        """Colons in heading text are not padded with spaces."""
        _, latex = parse_and_generate("=== Constraints: Key Integrity ===\n")
        assert "Constraints: Key Integrity" in latex
        assert "Constraints : Key Integrity" not in latex
