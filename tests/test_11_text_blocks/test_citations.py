"""Tests for citation syntax processing elem TEXT blocks.

Verifies that [cite key] syntax is properly converted to LaTeX \\citep commands
elem TEXT blocks, with support for optional locators (page numbers, slides, etc.).
"""

from __future__ import annotations

from txt2tex.ast_nodes import Document, Paragraph
from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser


class TestCitationProcessing:
    """Tests for citation syntax processing elem TEXT blocks."""

    def test_basic_citation(self) -> None:
        """Test basic citation without locator."""
        text = "TEXT: See [cite simpson25a] for details."
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Document)
        assert len(ast.items) == 1
        assert isinstance(ast.items[0], Paragraph)
        generator = LaTeXGenerator()
        latex = generator.generate_document(ast)
        assert "\\citep{simpson25a}" in latex
        assert "[cite simpson25a]" not in latex

    def test_citation_with_slide(self) -> None:
        """Test citation with slide locator."""
        text = "TEXT: See [cite simpson25a slide 20]."
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        generator = LaTeXGenerator()
        latex = generator.generate_document(ast)
        assert "\\citep[slide 20]{simpson25a}" in latex
        assert "[cite simpson25a slide 20]" not in latex

    def test_citation_with_page(self) -> None:
        """Test citation with page locator."""
        text = "TEXT: See [cite spivey92 p. 42]."
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        generator = LaTeXGenerator()
        latex = generator.generate_document(ast)
        assert "\\citep[p. 42]{spivey92}" in latex
        assert "[cite spivey92 p. 42]" not in latex

    def test_citation_with_page_range(self) -> None:
        """Test citation with page range locator."""
        text = "TEXT: See [cite woodcock96 pp. 10-15]."
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        generator = LaTeXGenerator()
        latex = generator.generate_document(ast)
        assert "\\citep[pp. 10-15]{woodcock96}" in latex
        assert "[cite woodcock96 pp. 10-15]" not in latex

    def test_citation_with_underscores_in_key(self) -> None:
        """Test citation key with underscores."""
        text = "TEXT: See [cite author_name_2025]."
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        generator = LaTeXGenerator()
        latex = generator.generate_document(ast)
        assert "\\citep{author_name_2025}" in latex
        assert "[cite author_name_2025]" not in latex

    def test_citation_with_hyphens_in_key(self) -> None:
        """Test citation key with hyphens."""
        text = "TEXT: See [cite author-name-2025]."
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        generator = LaTeXGenerator()
        latex = generator.generate_document(ast)
        assert "\\citep{author-name-2025}" in latex
        assert "[cite author-name-2025]" not in latex

    def test_multiple_citations_in_paragraph(self) -> None:
        """Test multiple citations elem one paragraph."""
        text = "TEXT: See [cite simpson25a] land [cite spivey92 p. 42]."
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        generator = LaTeXGenerator()
        latex = generator.generate_document(ast)
        assert "\\citep{simpson25a}" in latex
        assert "\\citep[p. 42]{spivey92}" in latex
        assert "[cite simpson25a]" not in latex
        assert "[cite spivey92 p. 42]" not in latex

    def test_citation_not_in_text_block(self) -> None:
        """Test that citations are NOT processed outside TEXT blocks."""
        text = "PURETEXT: [cite simpson25a] should remain literal."
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        generator = LaTeXGenerator()
        latex = generator.generate_document(ast)
        assert "[cite simpson25a]" in latex
        assert "\\citep" not in latex

    def test_citation_not_in_latex_block(self) -> None:
        """Test that citations are NOT processed elem LATEX blocks."""
        text = "LATEX: [cite simpson25a] should remain literal."
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        generator = LaTeXGenerator()
        latex = generator.generate_document(ast)
        assert "[cite simpson25a]" in latex
        assert "\\citep" not in latex

    def test_citation_with_complex_locator(self) -> None:
        """Test citation with complex locator text."""
        text = "TEXT: See [cite simpson25a chapter 3, section 2, slide 45-50]."
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        generator = LaTeXGenerator()
        latex = generator.generate_document(ast)
        assert "\\citep[chapter 3, section 2, slide 45-50]{simpson25a}" in latex

    def test_citation_with_numeric_key(self) -> None:
        """Test citation key with numbers."""
        text = "TEXT: See [cite paper2024]."
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        generator = LaTeXGenerator()
        latex = generator.generate_document(ast)
        assert "\\citep{paper2024}" in latex

    def test_citation_in_middle_of_sentence(self) -> None:
        """Test citation embedded elem middle of sentence."""
        text = "TEXT: The proof technique [cite simpson25a] is discussed here."
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        generator = LaTeXGenerator()
        latex = generator.generate_document(ast)
        assert "\\citep{simpson25a}" in latex
        assert "proof technique" in latex
        assert "discussed here" in latex

    def test_multiple_citations_with_various_locators(self) -> None:
        """Test multiple citations with different locator types."""
        text = (
            "TEXT: See [cite simpson25a], [cite spivey92 p. 42], "
            "land [cite woodcock96 slide 10]."
        )
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        generator = LaTeXGenerator()
        latex = generator.generate_document(ast)
        assert "\\citep{simpson25a}" in latex
        assert "\\citep[p. 42]{spivey92}" in latex
        assert "\\citep[slide 10]{woodcock96}" in latex

    def test_citation_regex_pattern_matching(self) -> None:
        """Test that citation regex correctly matches patterns."""
        text = "TEXT: [cite key123] [cite test-key] [cite key_test]."
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        generator = LaTeXGenerator()
        latex = generator.generate_document(ast)
        assert "\\citep{key123}" in latex
        assert "\\citep{test-key}" in latex
        assert "\\citep{key_test}" in latex
