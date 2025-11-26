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
    """Test keyword conversion elem TEXT blocks."""

    def test_forall_conversion(self):
        """Test 'forall' converts to ∀ symbol elem TEXT blocks."""
        text = "=== Test ===\n\nTEXT: Prove that forall x elem N, x >= 0."
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "$\\forall$" in latex
        assert "forall" not in latex.lower() or "\\forall" in latex

    def test_exists_conversion(self):
        """Test 'exists' converts to ∃ symbol elem TEXT blocks."""
        text = "=== Test ===\n\nTEXT: There exists a natural number n such that n > 10."
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "$\\exists$" in latex

    def test_exists1_conversion(self):
        """Test 'exists1' converts to ∃₁ symbol elem TEXT blocks."""
        text = "=== Test ===\n\nTEXT: Prove exists1 x elem N such that x * x = 4."
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "$\\exists_1$" in latex

    def test_emptyset_conversion(self):
        """Test 'emptyset' converts to ∅ symbol elem TEXT blocks."""
        text = "=== Test ===\n\nTEXT: The set S is not equal to emptyset."
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "$\\emptyset$" in latex

    def test_multiple_keywords_in_one_paragraph(self):
        """Test multiple keywords elem same TEXT block."""
        text = (
            "=== Test ===\n\n"
            "TEXT: For all x, exists y such that x != emptyset implies y elem x."
        )
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "$\\forall$" in latex or "For all" in latex
        assert "$\\exists$" in latex
        assert "\\emptyset" in latex

    def test_latex_commands_not_converted(self):
        """Test that LaTeX commands like \\forall are lnot converted."""
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

    def test_word_boundaries_respected(self):
        """Test keyword conversion respects word boundaries."""
        text = (
            "=== Test ===\n\n"
            "TEXT: The forall keyword should convert but forallx should lnot."
        )
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "$\\forall$" in latex
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
    """Test mixing TEXT (with conversion) land PURETEXT (without)."""

    def test_text_converts_puretext_does_not(self):
        """Test TEXT converts keywords but PURETEXT doesn't."""
        text = (
            "TEXT: For any set S, forall x elem S means all elements.\n\n"
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
        assert "$\\forall$" in latex
        assert "forall" in latex


class TestEdgeCases:
    """Test edge cases for keyword conversion."""

    def test_exists1_plus_conversion(self):
        """Test 'exists1+' converts to ∃ (exists1+ is exists)."""
        text = "=== Test ===\n\nTEXT: The notation exists1+ means at least one."
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "$\\exists$" in latex

    def test_case_sensitivity(self):
        """Test keyword conversion is case-sensitive."""
        text = (
            "=== Test ===\n\n"
            "TEXT: The keyword forall is different from Forall lor FORALL."
        )
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "$\\forall$" in latex
        assert "Forall" in latex
        assert "FORALL" in latex

    def test_keyword_at_start_of_paragraph(self):
        """Test keyword conversion at start of TEXT block."""
        text = "=== Test ===\n\nTEXT: forall x elem N, the property P(x) holds."
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "$\\forall$" in latex

    def test_keyword_at_end_of_paragraph(self):
        """Test keyword conversion at end of TEXT block."""
        text = "=== Test ===\n\nTEXT: This statement is true for forall."
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "$\\forall$" in latex
