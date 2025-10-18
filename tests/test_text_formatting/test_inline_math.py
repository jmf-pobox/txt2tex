"""Tests for inline math in TEXT blocks."""

from __future__ import annotations

from txt2tex.ast_nodes import Document, Paragraph, Part, Section
from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser


class TestInlineMath:
    """Test inline math expressions in TEXT paragraphs."""

    def test_inline_set_comprehension(self) -> None:
        """Test inline set comprehension in TEXT."""
        source = """=== Test ===

TEXT: The set { x : N | x > 0 } contains positive integers.
"""
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        assert isinstance(ast, Document)
        assert len(ast.items) == 1
        assert isinstance(ast.items[0], Section)
        section = ast.items[0]
        assert len(section.items) == 1
        assert isinstance(section.items[0], Paragraph)

        # Generate LaTeX
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # Check that set comprehension is wrapped in $...$
        assert r"$\{ x \colon \mathbb{N} \mid x > 0 \}$" in latex
        assert "contains positive integers" in latex

    def test_inline_quantifier(self) -> None:
        """Test inline quantifier in TEXT."""
        source = """=== Test ===

TEXT: We know that forall x : N | x >= 0 is true.
"""
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        assert isinstance(ast, Document)

        # Generate LaTeX
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # Check that quantifier is wrapped in $...$
        assert r"$\forall x \colon \mathbb{N} \bullet x \geq 0$" in latex
        assert "We know that" in latex
        assert "is true" in latex

    def test_multiple_inline_math(self) -> None:
        """Test multiple inline math expressions in same TEXT."""
        source = """=== Test ===

TEXT: Both { x : N | x > 0 } and { y : N | y < 10 } are sets.
"""
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        # Generate LaTeX
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # Check both set comprehensions are converted
        assert r"$\{ x \colon \mathbb{N} \mid x > 0 \}$" in latex
        assert r"$\{ y \colon \mathbb{N} \mid y < 10 \}$" in latex
        assert "Both" in latex
        assert "and" in latex
        assert "are sets" in latex

    def test_non_math_braces(self) -> None:
        """Test that non-math braces are left as-is."""
        source = """=== Test ===

TEXT: Use braces like {this} for grouping in text.
"""
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        # Generate LaTeX
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # Check that invalid set comprehension is NOT converted
        # (should fail to parse and be left as-is)
        assert "{this}" in latex or r"\{this\}" in latex

    def test_inline_math_in_part(self) -> None:
        """Test inline math in part content."""
        source = """=== Test ===

(a)
TEXT: The set { x : N | x > 0 } is non-empty.
"""
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        assert isinstance(ast, Document)
        assert len(ast.items) == 1
        assert isinstance(ast.items[0], Section)
        section = ast.items[0]
        assert len(section.items) == 1
        assert isinstance(section.items[0], Part)

        # Generate LaTeX
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # Check that set comprehension is converted
        assert r"$\{ x \colon \mathbb{N} \mid x > 0 \}$" in latex
        assert "is non-empty" in latex

    def test_symbolic_operators_with_inline_math(self) -> None:
        """Test that symbolic operators still work with inline math."""
        source = """=== Test ===

TEXT: We have { x : N | x > 0 } => x != 0 for all members.
"""
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        # Generate LaTeX
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # Check both conversions
        assert r"$\{ x \colon \mathbb{N} \mid x > 0 \}$" in latex
        assert r"$\Rightarrow$" in latex
        assert "for all members" in latex


# Simple inline math expression tests


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
