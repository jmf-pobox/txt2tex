"""Tests for operator conversion in TEXT blocks via explicit $...$ spans.

In escape-only mode operators in bare prose pass through unchanged.
Use $whiteboard-expr$ to trigger conversion via the full parser pipeline.
"""

from __future__ import annotations

from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser


class TestTextBlockRelationOperators:
    """Test relation operator conversion in TEXT blocks via $...$."""

    def test_o9_composition_in_text(self) -> None:
        """$R o9 S$ in TEXT emits \\semi (forward composition)."""
        text = "TEXT: The composition $R o9 S$ is defined."
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "\\semi" in latex

    def test_maplet_in_text(self) -> None:
        """$x |-> y$ in TEXT emits \\mapsto."""
        text = "TEXT: The maplet $x |-> y$ represents a pair."
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "\\mapsto" in latex
        assert "|->" not in latex

    def test_relation_type_in_text(self) -> None:
        """$X <-> Y$ in TEXT emits \\rel."""
        text = "TEXT: A relation R in $X <-> Y$."
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "\\rel" in latex
        assert "<->" not in latex

    def test_domain_restriction_in_text(self) -> None:
        """$S <| R$ in TEXT emits \\dres."""
        text = "TEXT: Domain restriction $S <| R$."
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "\\dres" in latex

    def test_range_restriction_in_text(self) -> None:
        """$R |> T$ in TEXT emits \\rres."""
        text = "TEXT: Range restriction $R |> T$."
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "\\rres" in latex

    def test_domain_corestriction_in_text(self) -> None:
        """$S <<| R$ in TEXT emits \\ndres."""
        text = "TEXT: Domain corestriction $S <<| R$."
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "\\ndres" in latex

    def test_range_corestriction_in_text(self) -> None:
        """$R |>> T$ in TEXT emits \\nrres."""
        text = "TEXT: Range corestriction $R |>> T$."
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "\\nrres" in latex


class TestTextBlockFunctionOperators:
    """Test function operator conversion in TEXT blocks via $...$."""

    def test_total_function_in_text(self) -> None:
        """$X -> Y$ in TEXT emits \\fun."""
        text = "TEXT: A function $X -> Y$."
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "\\fun" in latex

    def test_partial_function_in_text(self) -> None:
        """$X +-> Y$ in TEXT emits \\pfun."""
        text = "TEXT: A partial function $X +-> Y$."
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "\\pfun" in latex
        assert "+->" not in latex

    def test_injection_in_text(self) -> None:
        """$X >-> Y$ in TEXT emits \\inj."""
        text = "TEXT: An injection $X >-> Y$."
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "\\inj" in latex
        assert ">->" not in latex

    def test_partial_injection_in_text(self) -> None:
        """$X >+> Y$ in TEXT emits \\pinj."""
        text = "TEXT: A partial injection $X >+> Y$."
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "\\pinj" in latex
        assert ">+>" not in latex

    def test_surjection_in_text(self) -> None:
        """$X -->> Y$ in TEXT emits \\surj."""
        text = "TEXT: A surjection $X -->> Y$."
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "\\surj" in latex
        assert "-->>" not in latex

    def test_partial_surjection_in_text(self) -> None:
        """$X +->> Y$ in TEXT emits \\psurj."""
        text = "TEXT: A partial surjection $X +->> Y$."
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "\\psurj" in latex
        assert "+->>" not in latex

    def test_bijection_in_text(self) -> None:
        """$X >->> Y$ in TEXT emits \\bij."""
        text = "TEXT: A bijection $X >->> Y$."
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "\\bij" in latex
        assert ">->>" not in latex


class TestTextBlockSequenceOperators:
    """Test sequence operator conversion in TEXT blocks via $...$."""

    def test_override_in_text(self) -> None:
        """$f ++ g$ in TEXT emits \\oplus."""
        text = "TEXT: The override $f ++ g$ combines functions."
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "\\oplus" in latex

    def test_concatenation_unicode_in_text(self) -> None:
        """Unicode ⌢ in bare prose passes through literally in escape-only mode."""
        text = "TEXT: The concatenation s ⌢ t joins sequences."
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        # In escape-only mode, Unicode ⌢ passes through as the literal glyph.
        # It must NOT be converted to the \cat macro (that only fires for $⌢$).
        assert "⌢" in latex
        assert r"\cat" not in latex


class TestTextBlockOperatorOrdering:
    """Test that multi-character operators are not misidentified."""

    def test_maplet_not_split_by_arrow(self) -> None:
        """$x |-> y$ emits \\mapsto, not a split | and ->."""
        text = "TEXT: The maplet $x |-> y$ in R."
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
        """$S <<| R$ emits \\ndres, not a split < and <|."""
        text = "TEXT: Domain corestriction $S <<| R$."
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "\\ndres" in latex
        assert "<$\\dres$" not in latex

    def test_range_corestriction_not_split(self) -> None:
        """$R |>> T$ emits \\nrres, not a split | and >>."""
        text = "TEXT: Range corestriction $R |>> T$."
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "\\nrres" in latex

    def test_partial_function_not_split(self) -> None:
        """$X +-> Y$ emits \\pfun, not a split + and ->."""
        text = "TEXT: Partial function $X +-> Y$."
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
    """Test realistic prose with operators in explicit $...$ spans."""

    def test_composition_in_prose(self) -> None:
        """$x |-> z$ and $R o9 S$ in TEXT both convert correctly.

        o9 emits \\semi (fuzz forward composition), not \\circ.
        """
        text = "TEXT: Given $x |-> z$ in $R o9 S$ we can apply the definition."
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "\\mapsto" in latex
        assert "\\semi" in latex

    def test_nested_composition_in_prose(self) -> None:
        """$(R o9 S) o9 T$ in TEXT emits \\semi for each composition.

        o9 emits \\semi (fuzz forward composition), not \\circ.
        """
        text = "TEXT: The composition $R o9 S o9 T$ is associative."
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "\\semi" in latex

    def test_mixed_operators_in_prose(self) -> None:
        """Multiple $...$ spans for different operators in the same TEXT block.

        o9 emits \\semi (fuzz forward composition), not \\circ.
        """
        text = "TEXT: For R in $X <-> Y$ and $x |-> y$ in $R o9 S$."
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "\\rel" in latex
        assert "\\mapsto" in latex
        assert "\\semi" in latex
        assert "<->" not in latex
        assert "|->" not in latex
