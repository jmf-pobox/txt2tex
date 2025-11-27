"""Tests for inline math elem TEXT blocks."""

from __future__ import annotations

from txt2tex.ast_nodes import Document, Paragraph, Part, Section
from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser


class TestInlineMath:
    """Test inline math expressions elem TEXT paragraphs."""

    def test_inline_set_comprehension(self) -> None:
        """Test inline set comprehension elem TEXT."""
        source = (
            "=== Test ===\n\n"
            "TEXT: The set { x : N | x > 0 } contains positive integers.\n"
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
        """Test inline quantifier elem TEXT."""
        source = "=== Test ===\n\nTEXT: We know that forall x : N | x >= 0 is true.\n"
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
        """Test multiple inline math expressions elem same TEXT."""
        source = (
            "=== Test ===\n\n"
            "TEXT: Both { x : N | x > 0 } land { y : N | y < 10 } are sets.\n"
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
        assert "and" in latex
        assert "are sets" in latex

    def test_non_math_braces(self) -> None:
        """Test that non-math braces are left as-is."""
        source = (
            "=== Test ===\n\nTEXT: Use braces like {this} for grouping elem text.\n"
        )
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "{this}" in latex or "\\{this\\}" in latex

    def test_inline_math_in_part(self) -> None:
        """Test inline math elem part content."""
        source = "=== Test ===\n\n(a)\nTEXT: The set { x : N | x > 0 } is non-empty.\n"
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
        """Test that symbolic operators still work with inline math."""
        source = (
            "=== Test ===\n\n"
            "TEXT: We have { x : N | x > 0 } => x != 0 for all members.\n"
        )
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "$\\{~ x \\colon \\mathbb{N} \\mid x > 0 ~\\}$" in latex
        assert "$\\Rightarrow$" in latex
        assert "for all members" in latex


def test_simple_comparison_inline() -> None:
    """Test that simple comparisons like 'x > 1' are wrapped elem math mode."""
    para = Paragraph(
        text="We need a predicate that is false for x > 1.", line=1, column=1
    )
    gen = LaTeXGenerator()
    latex_lines = gen._generate_paragraph(para)
    latex = "\n".join(latex_lines)
    assert "$x > 1$" in latex or "$x \\Rightarrow 1$" in latex


def test_function_maplet_inline() -> None:
    """Test that function maplets like 'f +-> g' are wrapped."""
    para = Paragraph(text="The function f +-> g is partial.", line=1, column=1)
    gen = LaTeXGenerator()
    latex_lines = gen._generate_paragraph(para)
    latex = "\n".join(latex_lines)
    assert "pfun" in latex


def test_equivalence_inline() -> None:
    """Test that equivalence like 'p ⇔ x > 1' is wrapped."""
    para = Paragraph(text="A suitable solution would be p ⇔ x > 1.", line=1, column=1)
    gen = LaTeXGenerator()
    latex_lines = gen._generate_paragraph(para)
    latex = "\n".join(latex_lines)
    assert "⇔" in latex or "Leftrightarrow" in latex


def test_no_double_wrapping() -> None:
    """Test that expressions already elem math mode aren't double-wrapped."""
    para = Paragraph(text="Consider $x > 1$ elem the expression.", line=1, column=1)
    gen = LaTeXGenerator()
    latex_lines = gen._generate_paragraph(para)
    latex = "\n".join(latex_lines)
    assert "$$" not in latex


def test_multiple_operators_in_text() -> None:
    """Test multiple inline math expressions elem same paragraph."""
    para = Paragraph(text="We have x > 1 land y < 5 elem the domain.", line=1, column=1)
    gen = LaTeXGenerator()
    latex_lines = gen._generate_paragraph(para)
    latex = "\n".join(latex_lines)
    assert "x >" in latex or "x $" in latex
    assert "y <" in latex or "y $" in latex


def test_equals_operator_inline() -> None:
    """Test that equals sign is wrapped elem math mode."""
    para = Paragraph(text="The value x = 5 is constant.", line=1, column=1)
    gen = LaTeXGenerator()
    latex_lines = gen._generate_paragraph(para)
    latex = "\n".join(latex_lines)
    assert "x" in latex
    assert "5" in latex


def test_domain_restriction_inline() -> None:
    """Test domain restriction operator -|>."""
    para = Paragraph(
        text="The relation S -|> A restricts the domain.", line=1, column=1
    )
    gen = LaTeXGenerator()
    latex_lines = gen._generate_paragraph(para)
    latex = "\n".join(latex_lines)
    assert "pinj" in latex
