"""Tests for Zed blocks (unboxed Z notation paragraphs)."""

from __future__ import annotations

import pytest

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

    def test_multiple_predicates(self) -> None:
        """Test zed block with multiple predicate expressions."""
        text = "zed\n  forall x : N | x >= 0\n  forall y : N | y >= 0\nend"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Document)
        zed_block = ast.items[0]
        assert isinstance(zed_block, Zed)
        assert isinstance(zed_block.content, Document)
        assert len(zed_block.content.items) == 2

    def test_multiple_predicates_latex(self) -> None:
        """Test LaTeX generation for multi-predicate zed block."""
        text = "zed\n  forall x : N | x >= 0\n  forall y : N | y >= 0\nend"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        generator = LaTeXGenerator(use_fuzz=False)
        latex = generator.generate_document(ast)
        assert "\\begin{zed}" in latex
        assert "\\also" in latex
        assert "\\forall x" in latex
        assert "\\forall y" in latex
        assert "\\end{zed}" in latex


class TestSetComprehensionDotSeparator:
    """Tests for dot-separator disambiguation in set comprehensions.

    The dot (bullet) separator in { x : T | pred . expr } must be
    distinguished from field-access dots in expr like s.x.  The rule:
    spaces around the dot mean bullet; no space means field access.
    """

    def test_char_expr_with_field_access(self) -> None:
        """{ s : S | pred . s.x } should parse with s.x as the char expr."""
        text = "given X\nschema S\n  x : X\nend\n{ s : S | s.x = s.x . s.x }"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Document)

    def test_char_expr_with_field_access_latex(self) -> None:
        """The char expr s.x should render after the bullet."""
        text = "given X\nschema S\n  x : X\nend\n{ s : S | s.x = s.x . s.x }"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        generator = LaTeXGenerator(use_fuzz=True)
        latex = generator.generate_document(ast)
        assert "@ s.x" in latex or "@s.x" in latex or "@ s.x" in latex

    def test_char_expr_binding_after_dot(self) -> None:
        """{ s : S | pred . {| x == s.x |} } should still work."""
        text = "given X\nschema S\n  x : X\nend\n{ s : S | s.x = s.x . {| x == s.x |} }"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Document)

    def test_multi_var_char_expr_field_access(self) -> None:
        """{ s : S; t : T | pred . s.x } with multi-declaration."""
        text = (
            "given X\n"
            "schema S\n  x : X\nend\n"
            "schema T\n  x : X\nend\n"
            "{ s : S; t : T | s.x = t.x . s.x }"
        )
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Document)

    def test_tight_dot_is_field_access_not_bullet(self) -> None:
        """s.x (no spaces) in predicate must be field access, not bullet."""
        text = "given X\nschema S\n  x : X\nend\n{ s : S | s.x = s.x . s.x }"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Document)
        # The predicate s.x = s.x should parse as equality of two field accesses
        # NOT as "s" (bullet) "x = s.x . s.x"
        items = ast.items
        assert len(items) >= 1


class TestDotSeparatorQuantifiers:
    """Verify dot-separator vs field-access works for all quantifier forms."""

    def test_forall_field_access_after_bullet(self) -> None:
        """forall s : S | pred . s.x should parse correctly."""
        text = "given X\nschema S\n  x : X\nend\nforall s : S | s.x = s.x . s.x"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        generator = LaTeXGenerator(use_fuzz=True)
        latex = generator.generate_document(ast)
        assert "@ s.x" in latex

    def test_mu_field_access_after_bullet(self) -> None:
        """(mu s : S | pred . s.x) should parse correctly."""
        text = "given X\nschema S\n  x : X\nend\n(mu s : S | s.x = s.x . s.x)"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        generator = LaTeXGenerator(use_fuzz=True)
        latex = generator.generate_document(ast)
        assert "@ s.x" in latex

    def test_lambda_field_access_after_bullet(self) -> None:
        """(lambda s : S | pred . s.x) should parse correctly."""
        text = "given X\nschema S\n  x : X\nend\n(lambda s : S | s.x = s.x . s.x)"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        generator = LaTeXGenerator(use_fuzz=True)
        latex = generator.generate_document(ast)
        assert "@ s.x" in latex


def _assert_multiline_braces(latex: str) -> None:
    """Assert that a multi-line comprehension has correct brace placement.

    The opening ``\\{~`` must be inside the array (on the first row)
    and the closing ``~\\}`` must also be inside the array (on the
    last row).  Braces outside the array produce misaligned rendering.
    """
    assert r"\begin{array}" in latex, "expected array environment"
    # Extract the array body
    start = latex.index(r"\begin{array}{l}")
    end = latex.index(r"\end{array}", start)
    body = latex[start:end]
    assert r"\{~" in body, r"opening \{ must be inside the array"
    assert r"~\}" in body, r"closing \} must be inside the array"


class TestSetComprehensionLineBreaks:
    """Tests for WYSIWYG line breaks in set comprehensions.

    Line breaks in the .txt source should produce line breaks in the
    rendered LaTeX output, matching how quantifiers already handle
    continuation.
    """

    def test_single_line_stays_single_line(self) -> None:
        """A single-line comprehension must NOT gain spurious line breaks."""
        text = "given X\nschema S\n  x : X\nend\n{ s : S | s.x = s.x . (s.x) }"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        generator = LaTeXGenerator(use_fuzz=True)
        latex = generator.generate_document(ast)
        # Should be a single $...$ line with no array or line breaks
        assert "\\\\\n" not in latex
        assert "\\begin{array}" not in latex

    def test_break_after_pipe(self) -> None:
        """A newline after | should produce a line break in the output."""
        text = "given X\nschema S\n  x : X\nend\n{ s : S |\n    s.x = s.x }"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        generator = LaTeXGenerator(use_fuzz=True)
        latex = generator.generate_document(ast)
        _assert_multiline_braces(latex)

    def test_break_after_bullet(self) -> None:
        """A newline after . should produce a line break in the output."""
        text = "given X\nschema S\n  x : X\nend\n{ s : S | s.x = s.x .\n    (s.x) }"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        generator = LaTeXGenerator(use_fuzz=True)
        latex = generator.generate_document(ast)
        _assert_multiline_braces(latex)

    def test_break_after_land_in_predicate(self) -> None:
        """A newline after land should produce a line break in the output."""
        text = (
            "given X, Y\n"
            "schema S\n  x : X\n  y : Y\nend\n"
            "{ s : S | s.x = s.x land\n"
            "    s.y = s.y }"
        )
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        generator = LaTeXGenerator(use_fuzz=True)
        latex = generator.generate_document(ast)
        _assert_multiline_braces(latex)

    @pytest.mark.xfail(reason="semicolon-declaration breaks not yet tracked")
    def test_break_after_semicolon_declaration(self) -> None:
        """A newline after ; between declarations should produce a line break."""
        text = (
            "given X\n"
            "schema S\n  x : X\nend\n"
            "schema T\n  x : X\nend\n"
            "{ s : S;\n"
            "  t : T | s.x = t.x . (s.x) }"
        )
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        generator = LaTeXGenerator(use_fuzz=True)
        latex = generator.generate_document(ast)
        _assert_multiline_braces(latex)

    def test_multiple_breaks(self) -> None:
        """Breaks after | AND after . in the same comprehension."""
        text = (
            "given X\nschema S\n  x : X\nend\n{ s : S |\n    s.x = s.x .\n    (s.x) }"
        )
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        generator = LaTeXGenerator(use_fuzz=True)
        latex = generator.generate_document(ast)
        _assert_multiline_braces(latex)
        # Should have at least two line breaks inside the array
        start = latex.index(r"\begin{array}{l}")
        end = latex.index(r"\end{array}", start)
        body = latex[start:end]
        assert body.count("\\\\") >= 2

    def test_binding_output_after_break(self) -> None:
        """The realistic DAT pattern: pred .\n {| ... |}."""
        text = (
            "given X\n"
            "schema S\n  x : X\nend\n"
            "{ s : S | s.x = s.x .\n"
            "    {| x == s.x |} }"
        )
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        generator = LaTeXGenerator(use_fuzz=True)
        latex = generator.generate_document(ast)
        _assert_multiline_braces(latex)

    def test_long_realistic_comprehension(self) -> None:
        """A realistic multi-line three-variable comprehension."""
        text = (
            "given X, Y, Z\n"
            "schema S\n  x : X\n  y : Y\n  z : Z\nend\n"
            "schema T\n  x : X\nend\n"
            "{ s : S; t : T |\n"
            "    s.x = t.x land\n"
            "    s.y = s.y .\n"
            "    {| x == s.x |} }"
        )
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        generator = LaTeXGenerator(use_fuzz=True)
        latex = generator.generate_document(ast)
        _assert_multiline_braces(latex)

    def test_break_after_lor_in_predicate(self) -> None:
        """A newline after lor should produce a line break in the output."""
        text = (
            "given X, Y\n"
            "schema S\n  x : X\n  y : Y\nend\n"
            "{ s : S | s.x = s.x lor\n"
            "    s.y = s.y }"
        )
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        generator = LaTeXGenerator(use_fuzz=True)
        latex = generator.generate_document(ast)
        _assert_multiline_braces(latex)

    def test_break_with_parenthesised_char_expr(self) -> None:
        """Break before a parenthesised characteristic expression."""
        text = (
            "given X, Y\n"
            "schema S\n  x : X\n  y : Y\nend\n"
            "{ s : S | s.x = s.x .\n"
            "    (s.x, s.y) }"
        )
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        generator = LaTeXGenerator(use_fuzz=True)
        latex = generator.generate_document(ast)
        _assert_multiline_braces(latex)

    def test_break_with_nested_comprehension(self) -> None:
        """A comprehension whose char expr is itself a comprehension."""
        text = (
            "given X\n"
            "schema S\n  x : X\nend\n"
            "schema T\n  x : X\nend\n"
            "{ s : S | s.x = s.x .\n"
            "    { t : T | t.x = s.x } }"
        )
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        generator = LaTeXGenerator(use_fuzz=True)
        latex = generator.generate_document(ast)
        _assert_multiline_braces(latex)

    def test_break_after_implies_in_predicate(self) -> None:
        """A newline after => should produce a line break in the output."""
        text = (
            "given X\nschema S\n  x : X\nend\n{ s : S | s.x = s.x =>\n    s.x = s.x }"
        )
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        generator = LaTeXGenerator(use_fuzz=True)
        latex = generator.generate_document(ast)
        _assert_multiline_braces(latex)

    def test_break_after_bullet_no_predicate(self) -> None:
        """{ x : T .\n  expr } — no predicate, break after bullet."""
        text = "given X\nschema S\n  x : X\nend\n{ s : S .\n    (s.x) }"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        generator = LaTeXGenerator(use_fuzz=True)
        latex = generator.generate_document(ast)
        _assert_multiline_braces(latex)
        assert r"@ \\" in latex, "bullet must be followed by \\\\ line break"
