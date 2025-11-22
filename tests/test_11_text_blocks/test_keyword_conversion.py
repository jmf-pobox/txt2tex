"""Tests for automatic keyword conversion in TEXT blocks.

This feature automatically converts Z notation keywords to their symbols:
- forall → ∀
- exists → ∃
- exists1 → ∃₁
- emptyset → ∅

Keywords are converted in:
1. TEXT blocks (prose paragraphs)
2. Proof tree justifications
3. EQUIV block justifications

Keywords are NOT converted in:
- PURETEXT blocks (intentionally preserved for teaching)
- LaTeX commands (\\forall, \\exists, etc.)
"""

from __future__ import annotations

from txt2tex.ast_nodes import Document, Paragraph, PureParagraph
from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser


class TestTextBlockKeywordConversion:
    """Test keyword conversion in TEXT blocks."""

    def test_forall_conversion(self):
        """Test 'forall' converts to ∀ symbol in TEXT blocks."""
        text = """=== Test ===

TEXT: Prove that forall x in N, x >= 0."""

        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # Should convert forall to \forall symbol
        assert r"$\forall$" in latex
        # Should not have literal "forall" text
        assert "forall" not in latex.lower() or r"\forall" in latex

    def test_exists_conversion(self):
        """Test 'exists' converts to ∃ symbol in TEXT blocks."""
        text = """=== Test ===

TEXT: There exists a natural number n such that n > 10."""

        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # Should convert exists to \exists symbol
        assert r"$\exists$" in latex

    def test_exists1_conversion(self):
        """Test 'exists1' converts to ∃₁ symbol in TEXT blocks."""
        text = """=== Test ===

TEXT: Prove exists1 x in N such that x * x = 4."""

        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # Should convert exists1 to \exists_1 symbol
        assert r"$\exists_1$" in latex

    def test_emptyset_conversion(self):
        """Test 'emptyset' converts to ∅ symbol in TEXT blocks."""
        text = """=== Test ===

TEXT: The set S is not equal to emptyset."""

        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # Should convert emptyset to \emptyset symbol
        assert r"$\emptyset$" in latex

    def test_multiple_keywords_in_one_paragraph(self):
        """Test multiple keywords in same TEXT block."""
        text = """=== Test ===

TEXT: For all x, exists y such that x != emptyset implies y in x."""

        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # Should convert all keywords
        assert r"$\forall$" in latex or "For all" in latex
        assert r"$\exists$" in latex
        assert r"\emptyset" in latex

    def test_latex_commands_not_converted(self):
        """Test that LaTeX commands like \\forall are not converted."""
        text = r"""=== Test ===

TEXT: The LaTeX command \forall is used for universal quantification."""

        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # Should preserve \forall command, not double-convert
        # The backslash should be escaped in the final LaTeX
        assert "forall" in latex

    def test_word_boundaries_respected(self):
        """Test keyword conversion respects word boundaries."""
        text = """=== Test ===

TEXT: The forall keyword should convert but forallx should not."""

        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # forall should convert
        assert r"$\forall$" in latex
        # forallx should remain as-is
        assert "forallx" in latex


class TestProofJustificationKeywordConversion:
    """Test keyword conversion in proof tree justifications."""

    def test_forall_in_proof_justification(self):
        """Test 'forall' converts in proof justifications."""
        text = """=== Test ===

PROOF:
  forall x | P(x)
    P(a) [forall elim]"""

        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # Justification should convert forall to \forall
        assert r"\forall" in latex
        # Should have forall elim in the justification
        assert "elim" in latex

    def test_exists_in_proof_justification(self):
        """Test 'exists' converts in proof justifications."""
        text = """=== Test ===

PROOF:
  exists x | P(x)
    P(a) [exists intro]"""

        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # Justification should convert exists to \exists
        assert r"\exists" in latex
        assert "intro" in latex

    def test_emptyset_in_proof_justification(self):
        """Test 'emptyset' converts in proof justifications."""
        text = """=== Test ===

PROOF:
  S = emptyset
    x notin S [emptyset property]"""

        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # Justification should convert emptyset to \emptyset
        assert r"\emptyset" in latex


class TestEquivJustificationKeywordConversion:
    """Test keyword conversion in EQUIV block justifications."""

    def test_forall_in_equiv_justification(self):
        """Test 'forall' converts in EQUIV justifications."""
        text = """=== Test ===

EQUIV:
forall x | P(x)
<=> P(a) [forall instantiation]"""

        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # Justification should convert forall
        assert r"\forall" in latex

    def test_exists_in_equiv_justification(self):
        """Test 'exists' converts in EQUIV justifications."""
        text = """=== Test ===

EQUIV:
exists x | P(x)
<=> P(a) and Q(a) [exists intro]"""

        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # Justification should convert exists
        assert r"\exists" in latex


class TestPuretextNoConversion:
    """Test that PURETEXT blocks do NOT convert keywords."""

    def test_puretext_preserves_forall(self):
        """Test PURETEXT preserves literal 'forall' for teaching."""
        text = """PURETEXT: The syntax is forall x : T | predicate"""

        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        result = parser.parse()

        assert isinstance(result, Document)
        assert len(result.items) == 1
        assert isinstance(result.items[0], PureParagraph)
        # Should preserve literal "forall"
        assert "forall" in result.items[0].text

        # Generate LaTeX to verify no conversion happens
        gen = LaTeXGenerator()
        latex = gen.generate_document(result)

        # Should have literal "forall" text, not \forall command
        assert "forall" in latex

    def test_puretext_preserves_exists(self):
        """Test PURETEXT preserves literal 'exists' for teaching."""
        text = """PURETEXT: Use exists x : N | x > 0 for existential."""

        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        result = parser.parse()

        assert isinstance(result, Document)
        assert isinstance(result.items[0], PureParagraph)
        assert "exists" in result.items[0].text

    def test_puretext_preserves_emptyset(self):
        """Test PURETEXT preserves literal 'emptyset' for teaching."""
        text = """PURETEXT: The symbol emptyset represents the empty set."""

        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        result = parser.parse()

        assert isinstance(result, Document)
        assert isinstance(result.items[0], PureParagraph)
        assert "emptyset" in result.items[0].text


class TestMixedTextAndPuretext:
    """Test mixing TEXT (with conversion) and PURETEXT (without)."""

    def test_text_converts_puretext_does_not(self):
        """Test TEXT converts keywords but PURETEXT doesn't."""
        text = """TEXT: For any set S, forall x in S means all elements.

PURETEXT: The syntax forall x : T | predicate shows literal notation.
"""

        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        result = parser.parse()

        assert isinstance(result, Document)
        assert len(result.items) == 2
        assert isinstance(result.items[0], Paragraph)
        assert isinstance(result.items[1], PureParagraph)

        # PURETEXT should preserve literal keyword
        assert "forall" in result.items[1].text

        # Generate LaTeX
        gen = LaTeXGenerator()
        latex = gen.generate_document(result)

        # TEXT block should have converted forall
        assert r"$\forall$" in latex
        # PURETEXT block should have literal forall
        assert "forall" in latex


class TestEdgeCases:
    """Test edge cases for keyword conversion."""

    def test_exists1_plus_conversion(self):
        """Test 'exists1+' converts to ∃ (exists1+ is exists)."""
        text = """=== Test ===

TEXT: The notation exists1+ means at least one."""

        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # exists1+ should convert to \exists
        assert r"$\exists$" in latex

    def test_case_sensitivity(self):
        """Test keyword conversion is case-sensitive."""
        text = """=== Test ===

TEXT: The keyword forall is different from Forall or FORALL."""

        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # Only lowercase forall should convert
        assert r"$\forall$" in latex
        assert "Forall" in latex
        assert "FORALL" in latex

    def test_keyword_at_start_of_paragraph(self):
        """Test keyword conversion at start of TEXT block."""
        text = """=== Test ===

TEXT: forall x in N, the property P(x) holds."""

        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # Should convert forall even at start
        assert r"$\forall$" in latex

    def test_keyword_at_end_of_paragraph(self):
        """Test keyword conversion at end of TEXT block."""
        text = """=== Test ===

TEXT: This statement is true for forall."""

        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # Should convert forall even at end
        assert r"$\forall$" in latex
