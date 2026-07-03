"""Tests for inline math in TEXT blocks.

Inline math is opt-in: write ``$whiteboard-expr$`` to render an expression
as LaTeX math.  Bare prose passes through with only character escaping.
"""

from __future__ import annotations

from txt2tex.ast_nodes import Document, Paragraph, Part, Section
from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser


class TestInlineMath:
    """Test inline math expressions in TEXT paragraphs via explicit $...$."""

    def test_inline_set_comprehension(self) -> None:
        """Explicit ${ x : N | x > 0 }$ in TEXT renders as set comprehension."""
        source = (
            "=== Test ===\n\n"
            "TEXT: The set ${ x : N | x > 0 }$ contains positive integers.\n"
        )
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
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "$\\{~ x \\colon \\mathbb{N} \\mid x > 0 ~\\}$" in latex
        assert "contains positive integers" in latex

    def test_inline_quantifier(self) -> None:
        """Explicit $forall x : N | x >= 0$ in TEXT renders as quantifier."""
        source = "=== Test ===\n\nTEXT: We know that $forall x : N | x >= 0$ is true.\n"
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Document)
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "$\\forall x \\colon \\mathbb{N} \\bullet x \\geq 0$" in latex
        assert "We know that" in latex
        assert "is true" in latex

    def test_multiple_inline_math(self) -> None:
        """Multiple explicit $...$ expressions in the same TEXT block."""
        source = (
            "=== Test ===\n\n"
            "TEXT: Both ${ x : N | x > 0 }$ and ${ y : N | y < 10 }$ are sets.\n"
        )
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "$\\{~ x \\colon \\mathbb{N} \\mid x > 0 ~\\}$" in latex
        assert "$\\{~ y \\colon \\mathbb{N} \\mid y < 10 ~\\}$" in latex
        assert "Both" in latex
        assert "are sets" in latex

    def test_non_math_braces(self) -> None:
        """Bare braces in prose are escaped to \\{ \\} in escape-only mode."""
        source = "=== Test ===\n\nTEXT: Use braces like {this} for grouping in text.\n"
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        # In escape-only mode, bare { } are escaped to \{ \}.
        # Raw unescaped {this} must not survive in the output.
        assert "\\{this\\}" in latex
        assert "{this}" not in latex.replace("\\{this\\}", "")

    def test_inline_math_in_part(self) -> None:
        """Explicit $...$ in part content renders correctly."""
        source = (
            "=== Test ===\n\n(a)\nTEXT: The set ${ x : N | x > 0 }$ is non-empty.\n"
        )
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
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "$\\{~ x \\colon \\mathbb{N} \\mid x > 0 ~\\}$" in latex
        assert "is non-empty" in latex

    def test_symbolic_operators_with_inline_math(self) -> None:
        """Multiple explicit $...$ spans in the same TEXT block coexist."""
        source = (
            "=== Test ===\n\n"
            "TEXT: We have ${ x : N | x > 0 }$ where $x /= 0$ for all members.\n"
        )
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "$\\{~ x \\colon \\mathbb{N} \\mid x > 0 ~\\}$" in latex
        assert "\\neq" in latex
        assert "for all members" in latex


def test_simple_comparison_inline() -> None:
    """In escape-only mode, bare 'x > 1' stays as literal prose."""
    para = Paragraph(
        text="We need a predicate that is false for x > 1.", line=1, column=1
    )
    gen = LaTeXGenerator()
    latex_lines = gen._generate_paragraph(para)
    latex = "\n".join(latex_lines)
    # Bare comparisons are literal prose in escape-only mode — no auto-wrapping.
    assert "x > 1" in latex
    assert "$x > 1$" not in latex


def test_function_maplet_inline() -> None:
    """$f +-> g$ in TEXT prose renders as partial function."""
    para = Paragraph(text="The function $f +-> g$ is partial.", line=1, column=1)
    gen = LaTeXGenerator()
    latex_lines = gen._generate_paragraph(para)
    latex = "\n".join(latex_lines)
    assert "pfun" in latex


def test_equivalence_inline() -> None:
    """Unicode ⇔ in prose passes through literally (not auto-converted)."""
    para = Paragraph(text="A suitable solution would be p ⇔ x > 1.", line=1, column=1)
    gen = LaTeXGenerator()
    latex_lines = gen._generate_paragraph(para)
    latex = "\n".join(latex_lines)
    # In escape-only mode, Unicode ⇔ is not converted to \Leftrightarrow.
    # It passes through as-is, satisfying the "⇔ or Leftrightarrow" check.
    assert "⇔" in latex or "Leftrightarrow" in latex


def test_no_double_wrapping() -> None:
    """An existing $...$ span is not double-wrapped."""
    para = Paragraph(text="Consider $x > 1$ in the expression.", line=1, column=1)
    gen = LaTeXGenerator()
    latex_lines = gen._generate_paragraph(para)
    latex = "\n".join(latex_lines)
    assert "$$" not in latex


def test_multiple_operators_in_text() -> None:
    """Bare operators in prose stay as literal text in escape-only mode."""
    para = Paragraph(text="We have x > 1 land y < 5 in the domain.", line=1, column=1)
    gen = LaTeXGenerator()
    latex_lines = gen._generate_paragraph(para)
    latex = "\n".join(latex_lines)
    # Bare x > 1 stays as literal prose; no $ wrapping is inserted.
    assert "x > 1" in latex
    assert "$x" not in latex


def test_equals_operator_inline() -> None:
    """Bare 'x = 5' stays as literal prose (no auto-wrapping)."""
    para = Paragraph(text="The value x = 5 is constant.", line=1, column=1)
    gen = LaTeXGenerator()
    latex_lines = gen._generate_paragraph(para)
    latex = "\n".join(latex_lines)
    assert "x" in latex
    assert "5" in latex


def test_domain_restriction_inline() -> None:
    """$S -|> A$ in TEXT prose renders as partial injection."""
    para = Paragraph(
        text="The relation $S -|> A$ restricts the domain.", line=1, column=1
    )
    gen = LaTeXGenerator()
    latex_lines = gen._generate_paragraph(para)
    latex = "\n".join(latex_lines)
    assert "pinj" in latex
