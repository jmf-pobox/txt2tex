"""Tests for automatic keyword conversion elem TEXT blocks.

This feature automatically converts Z notation keywords to their symbols:
- forall → ∀
- exists → ∃
- exists1 → ∃₁
- emptyset → ∅

Keywords are converted elem:
1. TEXT blocks (prose paragraphs)
2. Proof tree justifications
3. EQUIV block justifications

Keywords are NOT converted elem:
- PURETEXT blocks (intentionally preserved for teaching)
- LaTeX commands (\\forall, \\exists, etc.)
"""

from __future__ import annotations

from txt2tex.ast_nodes import Document, Paragraph, PureParagraph
from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser


class TestTextBlockKeywordConversion:
    """Test that bare English keywords pass through as text in TEXT blocks.

    Since DAT #11 / engine bug #136, math keywords like 'forall', 'exists',
    'emptyset' in TEXT prose are NOT converted to math glyphs.  Math
    substitution is opt-in: use $...$ to get symbols, e.g. $\\forall$.
    """

    def test_forall_stays_as_prose(self):
        """Test 'forall' stays as English text in TEXT blocks (no conversion)."""
        text = "=== Test ===\n\nTEXT: Prove that forall x holds for all N."
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "forall" in latex
        assert "$\\forall$" not in latex

    def test_exists_stays_as_prose(self):
        """Test 'exists' stays as English text in TEXT blocks (no conversion)."""
        text = "=== Test ===\n\nTEXT: There exists a natural number n such that n > 10."
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "exists" in latex
        assert "$\\exists$" not in latex

    def test_exists1_stays_as_prose(self):
        """Test 'exists1' stays as English text in TEXT blocks (no conversion)."""
        text = "=== Test ===\n\nTEXT: The exists1 quantifier means unique existence."
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "exists1" in latex
        assert "$\\exists_1$" not in latex

    def test_emptyset_stays_as_prose(self):
        """Test 'emptyset' stays as English text in TEXT blocks (no conversion)."""
        text = "=== Test ===\n\nTEXT: The set S is not equal to emptyset."
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "emptyset" in latex
        assert "$\\emptyset$" not in latex

    def test_dollar_math_still_works(self):
        """Test that $...$ inline math still converts keywords inside TEXT blocks."""
        text = "=== Test ===\n\nTEXT: The quantifier $\\exists$ is used here."
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "$\\exists$" in latex

    def test_multiple_keywords_stay_as_prose(self):
        """Test multiple keywords in same TEXT block stay as English text."""
        text = "=== Test ===\n\nTEXT: For all x, exists y such that x is in some set."
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "For all" in latex
        assert "exists" in latex

    def test_latex_commands_not_converted(self):
        """Test that LaTeX commands like \\forall pass through unchanged."""
        text = (
            "=== Test ===\n\n"
            "TEXT: The LaTeX command \\forall is used for universal quantification."
        )
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "forall" in latex

    def test_non_keyword_words_unaffected(self):
        """Test non-keyword words are not altered."""
        text = "=== Test ===\n\nTEXT: The forall keyword is present but forallx is not."
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "forall" in latex
        assert "forallx" in latex


class TestProofJustificationKeywordConversion:
    """Test keyword conversion elem proof tree justifications."""

    def test_forall_in_proof_justification(self):
        """Test 'forall' converts elem proof justifications."""
        text = "=== Test ===\n\nPROOF:\n  forall x | P(x)\n    P(a) [forall elim]"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "\\forall" in latex
        assert "elim" in latex

    def test_exists_in_proof_justification(self):
        """Test 'exists' converts elem proof justifications."""
        text = "=== Test ===\n\nPROOF:\n  exists x | P(x)\n    P(a) [exists intro]"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "\\exists" in latex
        assert "intro" in latex

    def test_emptyset_in_proof_justification(self):
        """Test 'emptyset' converts elem proof justifications."""
        text = (
            "=== Test ===\n\nPROOF:\n  S = emptyset\n    x notin S [emptyset property]"
        )
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "\\emptyset" in latex


class TestEquivJustificationKeywordConversion:
    """Test keyword conversion elem EQUIV block justifications."""

    def test_forall_in_equiv_justification(self):
        """Test 'forall' converts elem EQUIV justifications."""
        text = (
            "=== Test ===\n\nEQUIV:\nforall x | P(x)\n<=> P(a) [forall instantiation]"
        )
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "\\forall" in latex

    def test_exists_in_equiv_justification(self):
        """Test 'exists' converts elem EQUIV justifications."""
        text = (
            "=== Test ===\n\nEQUIV:\nexists x | P(x)\n<=> P(a) land Q(a) [exists intro]"
        )
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "\\exists" in latex


class TestPuretextNoConversion:
    """Test that PURETEXT blocks do NOT convert keywords."""

    def test_puretext_preserves_forall(self):
        """Test PURETEXT preserves literal 'forall' for teaching."""
        text = "PURETEXT: The syntax is forall x : T | predicate"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        result = parser.parse()
        assert isinstance(result, Document)
        assert len(result.items) == 1
        assert isinstance(result.items[0], PureParagraph)
        assert "forall" in result.items[0].text
        gen = LaTeXGenerator()
        latex = gen.generate_document(result)
        assert "forall" in latex

    def test_puretext_preserves_exists(self):
        """Test PURETEXT preserves literal 'exists' for teaching."""
        text = "PURETEXT: Use exists x : N | x > 0 for existential."
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        result = parser.parse()
        assert isinstance(result, Document)
        assert isinstance(result.items[0], PureParagraph)
        assert "exists" in result.items[0].text

    def test_puretext_preserves_emptyset(self):
        """Test PURETEXT preserves literal 'emptyset' for teaching."""
        text = "PURETEXT: The symbol emptyset represents the empty set."
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        result = parser.parse()
        assert isinstance(result, Document)
        assert isinstance(result.items[0], PureParagraph)
        assert "emptyset" in result.items[0].text


class TestMixedTextAndPuretext:
    """Test mixing TEXT and PURETEXT blocks."""

    def test_both_preserve_keywords_as_text(self):
        """Test both TEXT and PURETEXT preserve keywords as literal text.

        Since DAT #11, TEXT blocks no longer auto-convert keywords.
        Both TEXT and PURETEXT now pass 'forall' through as English text.
        """
        text = (
            "TEXT: For any set S, forall x in S means all elements.\n\n"
            "PURETEXT: The syntax forall x : T | predicate shows literal notation.\n"
        )
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        result = parser.parse()
        assert isinstance(result, Document)
        assert len(result.items) == 2
        assert isinstance(result.items[0], Paragraph)
        assert isinstance(result.items[1], PureParagraph)
        assert "forall" in result.items[1].text
        gen = LaTeXGenerator()
        latex = gen.generate_document(result)
        # Neither TEXT nor PURETEXT converts bare 'forall'.
        assert "forall" in latex
        assert "$\\forall$" not in latex


class TestEdgeCases:
    """Test edge cases for prose text in TEXT blocks."""

    def test_exists1_stays_as_prose(self):
        """Test 'exists1+' stays as literal text (no math conversion)."""
        text = "=== Test ===\n\nTEXT: The notation exists1+ means at least one."
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "exists1+" in latex
        assert "$\\exists$" not in latex

    def test_all_variants_stay_as_prose(self):
        """Test all keyword variants stay as text (no math conversion)."""
        text = (
            "=== Test ===\n\n"
            "TEXT: The keyword forall is different from Forall and FORALL."
        )
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "forall" in latex
        assert "Forall" in latex
        assert "FORALL" in latex
        assert "$\\forall$" not in latex

    def test_keyword_at_start_of_paragraph_stays_as_prose(self):
        """Test keyword at start of TEXT block stays as English text."""
        text = "=== Test ===\n\nTEXT: forall x in N, the property P(x) holds."
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "forall" in latex
        assert "$\\forall$" not in latex

    def test_keyword_at_end_of_paragraph_stays_as_prose(self):
        """Test keyword at end of TEXT block stays as English text."""
        text = "=== Test ===\n\nTEXT: This statement is true for forall."
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "forall" in latex
        assert "$\\forall$" not in latex
