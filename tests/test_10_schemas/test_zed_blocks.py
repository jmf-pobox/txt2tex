"""Tests for Zed blocks (unboxed Z notation paragraphs)."""

from __future__ import annotations

from txt2tex.ast_nodes import (
    Abbreviation,
    BinaryOp,
    Document,
    FreeType,
    GivenType,
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
        lexer = Lexer("zed exists1 x : N | x * x = 4 land x > 0 end")
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
        assert isinstance(zed_block.content, Quantifier)
        assert zed_block.content.quantifier == "mu"

    def test_complex_predicate(self) -> None:
        """Test zed block with complex predicate combining operators."""
        lexer = Lexer("zed x elem S land y notin T => x <> y end")
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
        assert isinstance(zed_block.content.body, Quantifier)
        assert zed_block.content.body.quantifier == "exists"

    def test_multiline_zed_block(self) -> None:
        """Test zed block with content on multiple lines."""
        lexer = Lexer("zed\nforall x : N |\n  x >= 0\nend")
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
        lexer = Lexer("zed x elem {1, 2, 3} end")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Document)
        zed_block = ast.items[0]
        assert isinstance(zed_block, Zed)
        assert isinstance(zed_block.content, BinaryOp)
        assert zed_block.content.operator == "elem"


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
        assert "\\begin{zed}" in latex
        assert "\\end{zed}" in latex
        assert "x > 0" in latex

    def test_forall_quantifier_latex(self) -> None:
        """Test LaTeX generation for forall quantifier."""
        lexer = Lexer("zed forall x : N | x >= 0 end")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        generator = LaTeXGenerator(use_fuzz=False)
        latex = generator.generate_document(ast)
        assert "\\begin{zed}" in latex
        assert "\\forall" in latex
        assert "\\end{zed}" in latex

    def test_exists_quantifier_latex(self) -> None:
        """Test LaTeX generation for exists quantifier."""
        lexer = Lexer("zed exists n : N | n * n = 4 end")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        generator = LaTeXGenerator(use_fuzz=False)
        latex = generator.generate_document(ast)
        assert "\\begin{zed}" in latex
        assert "\\exists" in latex
        assert "\\end{zed}" in latex

    def test_mu_expression_latex(self) -> None:
        """Test LaTeX generation for mu expression."""
        lexer = Lexer("zed (mu n : N | n > 0) end")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        generator = LaTeXGenerator(use_fuzz=False)
        latex = generator.generate_document(ast)
        assert "\\begin{zed}" in latex
        assert "\\mu" in latex
        assert "\\end{zed}" in latex

    def test_complex_predicate_latex(self) -> None:
        """Test LaTeX generation for complex predicate."""
        lexer = Lexer("zed x elem S land y notin T => x <> y end")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        generator = LaTeXGenerator(use_fuzz=False)
        latex = generator.generate_document(ast)
        assert "\\begin{zed}" in latex
        assert "\\in" in latex
        assert "\\Rightarrow" in latex
        assert "\\end{zed}" in latex

    def test_fuzz_mode_latex(self) -> None:
        """Test LaTeX generation with fuzz mode enabled."""
        lexer = Lexer("zed forall x : N | x >= 0 end")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        generator = LaTeXGenerator(use_fuzz=True)
        latex = generator.generate_document(ast)
        assert "\\begin{zed}" in latex
        assert "\\forall" in latex
        assert "\\nat" in latex
        assert "\\end{zed}" in latex

    def test_multiple_zed_blocks(self) -> None:
        """Test LaTeX generation for multiple zed blocks elem document."""
        lexer = Lexer("zed x > 0 end\n\nzed y < 10 end")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        generator = LaTeXGenerator(use_fuzz=False)
        latex = generator.generate_document(ast)
        assert latex.count("\\begin{zed}") == 2
        assert latex.count("\\end{zed}") == 2

    def test_nested_quantifiers_latex(self) -> None:
        """Test LaTeX generation for nested quantifiers."""
        lexer = Lexer("zed forall x : N | exists y : N | x + y = 10 end")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        generator = LaTeXGenerator(use_fuzz=False)
        latex = generator.generate_document(ast)
        assert "\\begin{zed}" in latex
        assert "\\forall" in latex
        assert "\\exists" in latex
        assert "\\end{zed}" in latex

    def test_identifier_latex(self) -> None:
        """Test LaTeX generation for identifier elem zed block."""
        lexer = Lexer("zed S end")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        generator = LaTeXGenerator(use_fuzz=False)
        latex = generator.generate_document(ast)
        assert "\\begin{zed}" in latex
        assert "S" in latex
        assert "\\end{zed}" in latex


class TestZedBlockMixedContent:
    """Tests for zed blocks with mixed content (given, freetype, abbrev)."""

    def test_given_type_in_zed(self) -> None:
        """Test zed block with given type."""
        lexer = Lexer("zed given A, B end")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Document)
        zed_block = ast.items[0]
        assert isinstance(zed_block, Zed)
        assert isinstance(zed_block.content, Document)
        given = zed_block.content.items[0]
        assert isinstance(given, GivenType)
        assert given.names == ["A", "B"]

    def test_free_type_in_zed(self) -> None:
        """Test zed block with free type."""
        lexer = Lexer("zed Status ::= active | inactive end")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Document)
        zed_block = ast.items[0]
        assert isinstance(zed_block, Zed)
        assert isinstance(zed_block.content, Document)
        freetype = zed_block.content.items[0]
        assert isinstance(freetype, FreeType)
        assert freetype.name == "Status"
        assert len(freetype.branches) == 2

    def test_abbreviation_in_zed(self) -> None:
        """Test zed block with abbreviation."""
        lexer = Lexer("zed MaxSize == 100 end")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Document)
        zed_block = ast.items[0]
        assert isinstance(zed_block, Zed)
        assert isinstance(zed_block.content, Document)
        abbrev = zed_block.content.items[0]
        assert isinstance(abbrev, Abbreviation)
        assert abbrev.name == "MaxSize"

    def test_abbreviation_with_generic_params(self) -> None:
        """Test zed block with generic abbreviation."""
        lexer = Lexer("zed [X] Pair == X cross X end")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Document)
        zed_block = ast.items[0]
        assert isinstance(zed_block, Zed)
        assert isinstance(zed_block.content, Document)
        abbrev = zed_block.content.items[0]
        assert isinstance(abbrev, Abbreviation)
        assert abbrev.name == "Pair"
        assert abbrev.generic_params == ["X"]

    def test_compound_identifier_abbreviation(self) -> None:
        """Test zed block with compound identifier abbreviation (R+, R*, etc)."""
        lexer = Lexer("zed R+ == {a, b : N | b > a} end")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Document)
        zed_block = ast.items[0]
        assert isinstance(zed_block, Zed)
        assert isinstance(zed_block.content, Document)
        abbrev = zed_block.content.items[0]
        assert isinstance(abbrev, Abbreviation)
        assert abbrev.name == "R+"

    def test_mixed_given_and_freetype(self) -> None:
        """Test zed block with both given type land free type."""
        lexer = Lexer("zed\n  given A, B\n  Status ::= active | inactive\nend")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Document)
        zed_block = ast.items[0]
        assert isinstance(zed_block, Zed)
        assert isinstance(zed_block.content, Document)
        assert len(zed_block.content.items) == 2
        assert isinstance(zed_block.content.items[0], GivenType)
        assert isinstance(zed_block.content.items[1], FreeType)

    def test_mixed_freetype_and_abbreviation(self) -> None:
        """Test zed block with free type land abbreviation."""
        lexer = Lexer(
            "zed\n  Status ::= active | inactive\n  DefaultStatus == active\nend"
        )
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Document)
        zed_block = ast.items[0]
        assert isinstance(zed_block, Zed)
        assert isinstance(zed_block.content, Document)
        assert len(zed_block.content.items) == 2
        assert isinstance(zed_block.content.items[0], FreeType)
        assert isinstance(zed_block.content.items[1], Abbreviation)

    def test_all_three_constructs(self) -> None:
        """Test zed block with given, free type, land abbreviation."""
        text = (
            "zed\n  given Entry\n  Status ::= active | inactive\n"
            "  DefaultStatus == active\nend"
        )
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Document)
        zed_block = ast.items[0]
        assert isinstance(zed_block, Zed)
        assert isinstance(zed_block.content, Document)
        assert len(zed_block.content.items) == 3
        assert isinstance(zed_block.content.items[0], GivenType)
        assert isinstance(zed_block.content.items[1], FreeType)
        assert isinstance(zed_block.content.items[2], Abbreviation)

    def test_given_type_latex(self) -> None:
        """Test LaTeX generation for given type elem zed block."""
        lexer = Lexer("zed given A, B end")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        generator = LaTeXGenerator(use_fuzz=False)
        latex = generator.generate_document(ast)
        assert "\\begin{zed}" in latex
        assert "[A, B]" in latex
        assert "\\end{zed}" in latex

    def test_free_type_latex(self) -> None:
        """Test LaTeX generation for free type elem zed block."""
        lexer = Lexer("zed Status ::= active | inactive end")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        generator = LaTeXGenerator(use_fuzz=False)
        latex = generator.generate_document(ast)
        assert "\\begin{zed}" in latex
        assert "Status ::=" in latex
        assert "active | inactive" in latex
        assert "\\end{zed}" in latex

    def test_abbreviation_latex(self) -> None:
        """Test LaTeX generation for abbreviation elem zed block."""
        lexer = Lexer("zed MaxSize == 100 end")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        generator = LaTeXGenerator(use_fuzz=False)
        latex = generator.generate_document(ast)
        assert "\\begin{zed}" in latex
        assert "MaxSize ==" in latex
        assert "100" in latex
        assert "\\end{zed}" in latex

    def test_generic_abbreviation_latex(self) -> None:
        """Test LaTeX generation for generic abbreviation."""
        lexer = Lexer("zed [X] Pair == X cross X end")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        generator = LaTeXGenerator(use_fuzz=False)
        latex = generator.generate_document(ast)
        assert "\\begin{zed}" in latex
        assert "Pair[X] ==" in latex
        assert "\\cross" in latex
        assert "\\end{zed}" in latex

    def test_compound_identifier_latex(self) -> None:
        """Test LaTeX generation for compound identifier abbreviation."""
        lexer = Lexer("zed R+ == {a, b : N | b > a} end")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        generator = LaTeXGenerator(use_fuzz=False)
        latex = generator.generate_document(ast)
        assert "\\begin{zed}" in latex
        assert "R^+ ==" in latex
        assert "\\end{zed}" in latex

    def test_mixed_content_latex(self) -> None:
        """Test LaTeX generation for mixed content zed block."""
        text = (
            "zed\n  given Entry\n  Status ::= active | inactive\n"
            "  DefaultStatus == active\nend"
        )
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        generator = LaTeXGenerator(use_fuzz=False)
        latex = generator.generate_document(ast)
        assert "\\begin{zed}" in latex
        assert "[Entry]" in latex
        assert "Status ::=" in latex
        assert "DefaultStatus ==" in latex
        assert "\\end{zed}" in latex
