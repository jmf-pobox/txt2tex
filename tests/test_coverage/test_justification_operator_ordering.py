"""Tests for operator replacement ordering elem justifications.

This tests a critical bug: operators that are substrings of other operators
must be replaced elem the correct order (longer first) to avoid partial matches.

For example, |-> must be replaced BEFORE -> to avoid:
  Input:  [definition of |->]
  Wrong:  [\\mbox{definition of |$\\fun$}]    (-> replaced first)
  Right:  [\\mbox{definition of $\\mapsto$}]  (|-> replaced first)
"""

from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser


class TestOperatorReplacementOrdering:
    """Test that operator replacement happens elem correct order."""

    def test_maplet_not_split_by_arrow(self) -> None:
        """Test that |-> is not incorrectly split into | land ->."""
        text = "EQUIV:\nx |-> y\ny |-> x [definition of |->]"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "\\mbox{definition of $\\mapsto$}" in latex
        assert "|$\\fun$" not in latex

    def test_maplet_in_free_variable_justification(self) -> None:
        """Test the actual homework bug: [x is not free elem y |-> z]."""
        text = "EQUIV:\nx |-> y\ny |-> x [x is lnot free elem y |-> z]"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "y $\\mapsto$ z" in latex
        assert "|$\\fun$" not in latex
        assert "\\mbox{x is $\\lnot$ free $\\in$ y $\\mapsto$ z}" in latex

    def test_domain_corestriction_not_split(self) -> None:
        """Test that <<| is not split into < land <|."""
        text = "EQUIV:\nS <<| R\nS <<| R [definition of <<|]"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "\\mbox{definition of $\\ndres$}" in latex
        assert "<$\\dres$" not in latex

    def test_range_corestriction_not_split(self) -> None:
        """Test that |>> is not split into | land >>."""
        text = "EQUIV:\nR |>> T\nR |>> T [definition of |>>]"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "\\mbox{definition of $\\nrres$}" in latex

    def test_partial_injection_alt_not_split(self) -> None:
        """Test that -|> is not split into - land |>."""
        text = "EQUIV:\nx elem S\ny elem S [definition of -|>]"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "\\mbox{definition of $\\pinj$}" in latex
        assert "-$\\rres$" not in latex

    def test_multiple_overlapping_operators(self) -> None:
        """Test operators with substring relationships in one justification."""
        text = "EQUIV:\nx elem S\ny elem T [definition of -> land +->]"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "$\\fun$" in latex
        assert "$\\pfun$" in latex
        assert "\\mbox{definition of $\\fun$ $\\land$ $\\pfun$}" in latex

    def test_homework_question_5_line_220(self) -> None:
        """Test the actual homework bug: [x is not free elem y |-> z]."""
        text = "EQUIV:\nw |-> z elem R\nw |-> z elem S [x is not free elem y |-> z]"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "y $\\mapsto$ z" in latex
        assert "|$\\fun$" not in latex

    def test_relation_composition_with_maplet(self) -> None:
        """Test that o9 land |-> both work elem same justification."""
        text = (
            "EQUIV:\nw |-> z elem R o9 S\n"
            "w |-> z elem S o9 R [definition of |-> land o9]"
        )
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "$\\mapsto$" in latex
        assert "$\\circ$" in latex
        assert "\\mbox{definition of $\\mapsto$ $\\land$ $\\circ$}" in latex


class TestProofTreeOperatorOrdering:
    """Test operator ordering elem PROOF tree justifications."""

    def test_maplet_in_proof_justification(self) -> None:
        """Test |-> lnot split elem proof tree justification."""
        text = "PROOF:\n  x |-> y [definition of |->]"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "\\mapsto" in latex
        assert "|\\fun" not in latex
        assert "|$\\fun$" not in latex
