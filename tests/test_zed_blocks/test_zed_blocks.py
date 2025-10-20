"""Tests for Zed blocks (unboxed Z notation paragraphs)."""

from __future__ import annotations

from txt2tex.ast_nodes import (
    BinaryOp,
    Document,
    Identifier,
    Quantifier,
    Zed,
)
from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser


class TestZedBlockParsing:
    """Tests for parsing zed blocks."""

    def test_simple_predicate(self) -> None:
        """Test parsing zed block with simple predicate."""
        lexer = Lexer("zed x > 0 end")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Document)
        zed_block = ast.items[0]
        assert isinstance(zed_block, Zed)
        assert isinstance(zed_block.content, BinaryOp)
        assert zed_block.content.operator == ">"

    def test_forall_quantifier(self) -> None:
        """Test zed block with forall quantifier."""
        lexer = Lexer("zed forall x : N | x >= 0 end")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Document)
        zed_block = ast.items[0]
        assert isinstance(zed_block, Zed)
        assert isinstance(zed_block.content, Quantifier)
        assert zed_block.content.quantifier == "forall"

    def test_exists_quantifier(self) -> None:
        """Test zed block with exists quantifier."""
        lexer = Lexer("zed exists n : N | n * n = 4 end")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Document)
        zed_block = ast.items[0]
        assert isinstance(zed_block, Zed)
        assert isinstance(zed_block.content, Quantifier)
        assert zed_block.content.quantifier == "exists"

    def test_exists1_quantifier(self) -> None:
        """Test zed block with exists1 (unique existence) quantifier."""
        lexer = Lexer("zed exists1 x : N | x * x = 4 and x > 0 end")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Document)
        zed_block = ast.items[0]
        assert isinstance(zed_block, Zed)
        assert isinstance(zed_block.content, Quantifier)
        assert zed_block.content.quantifier == "exists1"

    def test_mu_expression(self) -> None:
        """Test zed block with mu (definite description) operator."""
        lexer = Lexer("zed (mu n : N | n > 0) end")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Document)
        zed_block = ast.items[0]
        assert isinstance(zed_block, Zed)
        # The content is the parenthesized mu expression
        assert isinstance(zed_block.content, Quantifier)
        assert zed_block.content.quantifier == "mu"

    def test_complex_predicate(self) -> None:
        """Test zed block with complex predicate combining operators."""
        lexer = Lexer("zed x in S and y notin T => x <> y end")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Document)
        zed_block = ast.items[0]
        assert isinstance(zed_block, Zed)
        assert isinstance(zed_block.content, BinaryOp)
        assert zed_block.content.operator == "=>"

    def test_nested_quantifiers(self) -> None:
        """Test zed block with nested quantifiers."""
        lexer = Lexer("zed forall x : N | exists y : N | x + y = 10 end")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Document)
        zed_block = ast.items[0]
        assert isinstance(zed_block, Zed)
        assert isinstance(zed_block.content, Quantifier)
        assert zed_block.content.quantifier == "forall"
        # The body should be another quantifier
        assert isinstance(zed_block.content.body, Quantifier)
        assert zed_block.content.body.quantifier == "exists"

    def test_multiline_zed_block(self) -> None:
        """Test zed block with content on multiple lines."""
        lexer = Lexer("""zed
forall x : N |
  x >= 0
end""")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Document)
        zed_block = ast.items[0]
        assert isinstance(zed_block, Zed)
        assert isinstance(zed_block.content, Quantifier)

    def test_identifier_in_zed(self) -> None:
        """Test zed block with simple identifier."""
        lexer = Lexer("zed S end")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Document)
        zed_block = ast.items[0]
        assert isinstance(zed_block, Zed)
        assert isinstance(zed_block.content, Identifier)
        assert zed_block.content.name == "S"

    def test_set_membership(self) -> None:
        """Test zed block with set membership predicate."""
        lexer = Lexer("zed x in {1, 2, 3} end")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Document)
        zed_block = ast.items[0]
        assert isinstance(zed_block, Zed)
        assert isinstance(zed_block.content, BinaryOp)
        assert zed_block.content.operator == "in"


class TestZedBlockLaTeXGeneration:
    """Tests for LaTeX generation from zed blocks."""

    def test_simple_predicate_latex(self) -> None:
        """Test LaTeX generation for simple predicate."""
        lexer = Lexer("zed x > 0 end")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        generator = LaTeXGenerator(use_fuzz=False)
        latex = generator.generate_document(ast)
        assert r"\begin{zed}" in latex
        assert r"\end{zed}" in latex
        assert "x > 0" in latex

    def test_forall_quantifier_latex(self) -> None:
        """Test LaTeX generation for forall quantifier."""
        lexer = Lexer("zed forall x : N | x >= 0 end")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        generator = LaTeXGenerator(use_fuzz=False)
        latex = generator.generate_document(ast)
        assert r"\begin{zed}" in latex
        assert r"\forall" in latex
        assert r"\end{zed}" in latex

    def test_exists_quantifier_latex(self) -> None:
        """Test LaTeX generation for exists quantifier."""
        lexer = Lexer("zed exists n : N | n * n = 4 end")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        generator = LaTeXGenerator(use_fuzz=False)
        latex = generator.generate_document(ast)
        assert r"\begin{zed}" in latex
        assert r"\exists" in latex
        assert r"\end{zed}" in latex

    def test_mu_expression_latex(self) -> None:
        """Test LaTeX generation for mu expression."""
        lexer = Lexer("zed (mu n : N | n > 0) end")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        generator = LaTeXGenerator(use_fuzz=False)
        latex = generator.generate_document(ast)
        assert r"\begin{zed}" in latex
        assert r"\mu" in latex
        assert r"\end{zed}" in latex

    def test_complex_predicate_latex(self) -> None:
        """Test LaTeX generation for complex predicate."""
        lexer = Lexer("zed x in S and y notin T => x <> y end")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        generator = LaTeXGenerator(use_fuzz=False)
        latex = generator.generate_document(ast)
        assert r"\begin{zed}" in latex
        assert r"\in" in latex
        assert r"\Rightarrow" in latex
        assert r"\end{zed}" in latex

    def test_fuzz_mode_latex(self) -> None:
        """Test LaTeX generation with fuzz mode enabled."""
        lexer = Lexer("zed forall x : N | x >= 0 end")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        generator = LaTeXGenerator(use_fuzz=True)
        latex = generator.generate_document(ast)
        assert r"\begin{zed}" in latex
        assert r"\forall" in latex
        # In fuzz mode, N should be \nat
        assert r"\nat" in latex
        assert r"\end{zed}" in latex

    def test_multiple_zed_blocks(self) -> None:
        """Test LaTeX generation for multiple zed blocks in document."""
        lexer = Lexer("""zed x > 0 end

zed y < 10 end""")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        generator = LaTeXGenerator(use_fuzz=False)
        latex = generator.generate_document(ast)
        # Should have two zed environments
        assert latex.count(r"\begin{zed}") == 2
        assert latex.count(r"\end{zed}") == 2

    def test_nested_quantifiers_latex(self) -> None:
        """Test LaTeX generation for nested quantifiers."""
        lexer = Lexer("zed forall x : N | exists y : N | x + y = 10 end")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        generator = LaTeXGenerator(use_fuzz=False)
        latex = generator.generate_document(ast)
        assert r"\begin{zed}" in latex
        assert r"\forall" in latex
        assert r"\exists" in latex
        assert r"\end{zed}" in latex

    def test_identifier_latex(self) -> None:
        """Test LaTeX generation for identifier in zed block."""
        lexer = Lexer("zed S end")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        generator = LaTeXGenerator(use_fuzz=False)
        latex = generator.generate_document(ast)
        assert r"\begin{zed}" in latex
        assert "S" in latex
        assert r"\end{zed}" in latex
