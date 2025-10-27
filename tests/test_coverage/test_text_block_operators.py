"""Tests for operator conversion in TEXT blocks.

Verifies that relation, function, and sequence operators are properly
converted to LaTeX symbols in TEXT blocks.
"""

from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser


class TestTextBlockRelationOperators:
    """Test relation operator conversion in TEXT blocks."""

    def test_o9_composition_in_text(self) -> None:
        """Test that o9 is converted to composition symbol in TEXT."""
        text = """TEXT: The composition R o9 S is defined."""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # Should have \circ not literal o9
        assert r"R $\circ$ S" in latex
        assert "o9" not in latex

    def test_maplet_in_text(self) -> None:
        """Test that |-> is converted to mapsto in TEXT."""
        text = """TEXT: The maplet x |-> y represents a pair."""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # Should have mapsto (auto-formula may wrap extra context)
        assert r"\mapsto" in latex
        assert "|->" not in latex

    def test_relation_type_in_text(self) -> None:
        """Test that <-> is converted to relation type in TEXT."""
        text = """TEXT: A relation R in X <-> Y."""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # Should have \rel (auto-formula may wrap extra context)
        assert r"\rel" in latex
        assert "<->" not in latex

    def test_domain_restriction_in_text(self) -> None:
        """Test that <| is converted in TEXT."""
        text = """TEXT: Domain restriction S <| R."""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # Should have \dres
        assert r"S $\dres$ R" in latex

    def test_range_restriction_in_text(self) -> None:
        """Test that |> is converted in TEXT."""
        text = """TEXT: Range restriction R |> T."""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # Should have \rres
        assert r"R $\rres$ T" in latex

    def test_domain_corestriction_in_text(self) -> None:
        """Test that <<| is converted in TEXT."""
        text = """TEXT: Domain corestriction S <<| R."""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # Should have \ndres
        assert r"S $\ndres$ R" in latex

    def test_range_corestriction_in_text(self) -> None:
        """Test that |>> is converted in TEXT."""
        text = """TEXT: Range corestriction R |>> T."""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # Should have \nrres
        assert r"R $\nrres$ T" in latex


class TestTextBlockFunctionOperators:
    """Test function operator conversion in TEXT blocks."""

    def test_total_function_in_text(self) -> None:
        """Test that -> is converted to total function in TEXT."""
        text = """TEXT: A function f : X -> Y."""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # Should have \fun (auto-formula wraps entire type signature)
        assert r"\fun" in latex

    def test_partial_function_in_text(self) -> None:
        """Test that +-> is converted in TEXT."""
        text = """TEXT: A partial function f : X +-> Y."""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # Should have \pfun (auto-formula wraps entire type signature)
        assert r"\pfun" in latex
        assert "+->" not in latex

    def test_injection_in_text(self) -> None:
        """Test that >-> is converted in TEXT."""
        text = """TEXT: An injection f : X >-> Y."""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # Should have \inj (auto-formula wraps entire type signature)
        assert r"\inj" in latex
        assert ">->" not in latex

    def test_partial_injection_in_text(self) -> None:
        """Test that >+> is converted in TEXT."""
        text = """TEXT: A partial injection f : X >+> Y."""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # Should have \pinj (auto-formula wraps entire type signature)
        assert r"\pinj" in latex
        assert ">+>" not in latex

    def test_surjection_in_text(self) -> None:
        """Test that -->> is converted in TEXT."""
        text = """TEXT: A surjection f : X -->> Y."""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # Should have \surj (auto-formula wraps entire type signature)
        assert r"\surj" in latex
        assert "-->>" not in latex

    def test_partial_surjection_in_text(self) -> None:
        """Test that +->> is converted in TEXT."""
        text = """TEXT: A partial surjection f : X +->> Y."""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # Should have \psurj (auto-formula wraps entire type signature)
        assert r"\psurj" in latex
        assert "+->>" not in latex

    def test_bijection_in_text(self) -> None:
        """Test that >->> is converted in TEXT."""
        text = """TEXT: A bijection f : X >->> Y."""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # Should have \bij (auto-formula wraps entire type signature)
        assert r"\bij" in latex
        assert ">->>" not in latex


class TestTextBlockSequenceOperators:
    """Test sequence operator conversion in TEXT blocks."""

    def test_override_in_text(self) -> None:
        """Test that ++ is converted to override in TEXT."""
        text = """TEXT: The override f ++ g combines functions."""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # Should have \oplus
        assert r"f $\oplus$ g" in latex

    def test_concatenation_unicode_in_text(self) -> None:
        """Test that ⌢ is converted to concatenation in TEXT."""
        text = """TEXT: The concatenation s ⌢ t joins sequences."""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # Should have \cat
        assert r"s $\cat$ t" in latex


class TestTextBlockOperatorOrdering:
    """Test that operators are processed in correct order (longest first)."""

    def test_maplet_not_split_by_arrow(self) -> None:
        """Test that |-> is not incorrectly split into | and -> in TEXT."""
        text = """TEXT: The maplet x |-> y in R."""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # Should have mapsto, not | followed by \fun
        assert r"\mapsto" in latex
        assert r"|$\fun$" not in latex
        assert r"|\fun" not in latex

    def test_domain_corestriction_not_split(self) -> None:
        """Test that <<| is not split into < and <| in TEXT."""
        text = """TEXT: Domain corestriction S <<| R."""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # Should have \ndres not partial match
        assert r"S $\ndres$ R" in latex
        assert r"<$\dres$" not in latex

    def test_range_corestriction_not_split(self) -> None:
        """Test that |>> is not split into | and >> in TEXT."""
        text = """TEXT: Range corestriction R |>> T."""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # Should have \nrres
        assert r"R $\nrres$ T" in latex

    def test_partial_function_not_split(self) -> None:
        """Test that +-> is not split into + and -> in TEXT."""
        text = """TEXT: Partial function f : X +-> Y."""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # Should have \pfun not + followed by \fun
        assert r"\pfun" in latex
        assert r"+$\fun$" not in latex
        assert r"+\fun" not in latex


class TestTextBlockHomeworkScenario:
    """Test the actual homework scenario that revealed the missing o9."""

    def test_composition_in_prose(self) -> None:
        """Test o9 conversion in prose like homework Question 5."""
        text = """TEXT: Given x |-> z in R o9 S we can apply the definition."""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # Should have both mapsto and circ (auto-formula may wrap extra context)
        assert r"\mapsto" in latex
        assert r"\circ" in latex
        # Should NOT have literal o9
        assert "o9" not in latex

    def test_nested_composition_in_prose(self) -> None:
        """Test multiple o9 in same TEXT block."""
        text = """TEXT: The composition (R o9 S) o9 T equals R o9 (S o9 T)."""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # Should have circ for all compositions
        assert latex.count(r"$\circ$") >= 3
        # Should NOT have any literal o9
        assert "o9" not in latex

    def test_mixed_operators_in_prose(self) -> None:
        """Test multiple different operators in same TEXT block."""
        text = """TEXT: For R in X <-> Y and x |-> y in R o9 S."""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # Should have all operator conversions (auto-formula may wrap extra context)
        assert r"\rel" in latex
        assert r"\mapsto" in latex
        assert r"\circ" in latex
        assert "o9" not in latex
        assert "<->" not in latex
        assert "|->" not in latex
