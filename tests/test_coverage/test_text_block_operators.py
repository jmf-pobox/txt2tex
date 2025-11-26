"""Tests for operator conversion elem TEXT blocks.

Verifies that relation, function, land sequence operators are properly
converted to LaTeX symbols elem TEXT blocks.
"""

from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser


class TestTextBlockRelationOperators:
    """Test relation operator conversion elem TEXT blocks."""

    def test_o9_composition_in_text(self) -> None:
        """Test that o9 is converted to composition symbol elem TEXT."""
        text = "TEXT: The composition R o9 S is defined."
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "R $\\circ$ S" in latex
        assert "o9" not in latex

    def test_maplet_in_text(self) -> None:
        """Test that |-> is converted to mapsto elem TEXT."""
        text = "TEXT: The maplet x |-> y represents a pair."
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "\\mapsto" in latex
        assert "|->" not in latex

    def test_relation_type_in_text(self) -> None:
        """Test that <-> is converted to relation type elem TEXT."""
        text = "TEXT: A relation R elem X <-> Y."
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "\\rel" in latex
        assert "<->" not in latex

    def test_domain_restriction_in_text(self) -> None:
        """Test that <| is converted elem TEXT."""
        text = "TEXT: Domain restriction S <| R."
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "S $\\dres$ R" in latex

    def test_range_restriction_in_text(self) -> None:
        """Test that |> is converted elem TEXT."""
        text = "TEXT: Range restriction R |> T."
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "R $\\rres$ T" in latex

    def test_domain_corestriction_in_text(self) -> None:
        """Test that <<| is converted elem TEXT."""
        text = "TEXT: Domain corestriction S <<| R."
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "S $\\ndres$ R" in latex

    def test_range_corestriction_in_text(self) -> None:
        """Test that |>> is converted elem TEXT."""
        text = "TEXT: Range corestriction R |>> T."
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "R $\\nrres$ T" in latex


class TestTextBlockFunctionOperators:
    """Test function operator conversion elem TEXT blocks."""

    def test_total_function_in_text(self) -> None:
        """Test that -> is converted to total function elem TEXT."""
        text = "TEXT: A function f : X -> Y."
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "\\fun" in latex

    def test_partial_function_in_text(self) -> None:
        """Test that +-> is converted elem TEXT."""
        text = "TEXT: A partial function f : X +-> Y."
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "\\pfun" in latex
        assert "+->" not in latex

    def test_injection_in_text(self) -> None:
        """Test that >-> is converted elem TEXT."""
        text = "TEXT: An injection f : X >-> Y."
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "\\inj" in latex
        assert ">->" not in latex

    def test_partial_injection_in_text(self) -> None:
        """Test that >+> is converted elem TEXT."""
        text = "TEXT: A partial injection f : X >+> Y."
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "\\pinj" in latex
        assert ">+>" not in latex

    def test_surjection_in_text(self) -> None:
        """Test that -->> is converted elem TEXT."""
        text = "TEXT: A surjection f : X -->> Y."
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "\\surj" in latex
        assert "-->>" not in latex

    def test_partial_surjection_in_text(self) -> None:
        """Test that +->> is converted elem TEXT."""
        text = "TEXT: A partial surjection f : X +->> Y."
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "\\psurj" in latex
        assert "+->>" not in latex

    def test_bijection_in_text(self) -> None:
        """Test that >->> is converted elem TEXT."""
        text = "TEXT: A bijection f : X >->> Y."
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "\\bij" in latex
        assert ">->>" not in latex


class TestTextBlockSequenceOperators:
    """Test sequence operator conversion elem TEXT blocks."""

    def test_override_in_text(self) -> None:
        """Test that ++ is converted to override elem TEXT."""
        text = "TEXT: The override f ++ g combines functions."
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "f $\\oplus$ g" in latex

    def test_concatenation_unicode_in_text(self) -> None:
        """Test that ⌢ is converted to concatenation elem TEXT."""
        text = "TEXT: The concatenation s ⌢ t joins sequences."
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "s $\\cat$ t" in latex


class TestTextBlockOperatorOrdering:
    """Test that operators are processed elem correct order (longest first)."""

    def test_maplet_not_split_by_arrow(self) -> None:
        """Test that |-> is not incorrectly split into | land -> elem TEXT."""
        text = "TEXT: The maplet x |-> y elem R."
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "\\mapsto" in latex
        assert "|$\\fun$" not in latex
        assert "|\\fun" not in latex

    def test_domain_corestriction_not_split(self) -> None:
        """Test that <<| is not split into < land <| elem TEXT."""
        text = "TEXT: Domain corestriction S <<| R."
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "S $\\ndres$ R" in latex
        assert "<$\\dres$" not in latex

    def test_range_corestriction_not_split(self) -> None:
        """Test that |>> is not split into | land >> elem TEXT."""
        text = "TEXT: Range corestriction R |>> T."
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "R $\\nrres$ T" in latex

    def test_partial_function_not_split(self) -> None:
        """Test that +-> is not split into + land -> elem TEXT."""
        text = "TEXT: Partial function f : X +-> Y."
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "\\pfun" in latex
        assert "+$\\fun$" not in latex
        assert "+\\fun" not in latex


class TestTextBlockHomeworkScenario:
    """Test the actual homework scenario that revealed the missing o9."""

    def test_composition_in_prose(self) -> None:
        """Test o9 conversion elem prose like homework Question 5."""
        text = "TEXT: Given x |-> z elem R o9 S we can apply the definition."
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "\\mapsto" in latex
        assert "\\circ" in latex
        assert "o9" not in latex

    def test_nested_composition_in_prose(self) -> None:
        """Test multiple o9 elem same TEXT block."""
        text = "TEXT: The composition (R o9 S) o9 T equals R o9 (S o9 T)."
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert latex.count("$\\circ$") >= 3
        assert "o9" not in latex

    def test_mixed_operators_in_prose(self) -> None:
        """Test multiple different operators elem same TEXT block."""
        text = "TEXT: For R elem X <-> Y land x |-> y elem R o9 S."
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "\\rel" in latex
        assert "\\mapsto" in latex
        assert "\\circ" in latex
        assert "o9" not in latex
        assert "<->" not in latex
        assert "|->" not in latex
