r"""Tests for operator replacement ordering in justifications.

This tests a critical bug: operators that are substrings of other operators
must be replaced in the correct order (longer first) to avoid partial matches.

For example, |-> must be replaced BEFORE -> to avoid:
  Input:  [definition of |->]
  Wrong:  [\mbox{definition of |$\fun$}]    (-> replaced first)
  Right:  [\mbox{definition of $\mapsto$}]  (|-> replaced first)
"""

from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser


class TestOperatorReplacementOrdering:
    """Test that operator replacement happens in correct order."""

    def test_maplet_not_split_by_arrow(self) -> None:
        """Test that |-> is not incorrectly split into | and ->."""
        text = """EQUIV:
x |-> y
y |-> x [definition of |->]"""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # Should have mapsto, not fun (which would indicate -> was replaced first)
        assert r"\mbox{definition of $\mapsto$}" in latex
        # Should NOT have |$\fun$ which would indicate wrong order
        assert r"|$\fun$" not in latex

    def test_maplet_in_free_variable_justification(self) -> None:
        """Test the actual homework bug: [x is not free in y |-> z]."""
        text = """EQUIV:
x |-> y
y |-> x [x is not free in y |-> z]"""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # Should have proper mapsto symbol
        assert r"y $\mapsto$ z" in latex
        # Should NOT have the bug pattern |$\fun$
        assert r"|$\fun$" not in latex
        # Verify full justification
        assert r"\mbox{x is $\lnot$ free in y $\mapsto$ z}" in latex

    def test_domain_corestriction_not_split(self) -> None:
        """Test that <<| is not split into < and <|."""
        text = """EQUIV:
S <<| R
S <<| R [definition of <<|]"""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # Should have ndres (domain corestriction)
        assert r"\mbox{definition of $\ndres$}" in latex
        # Should NOT have <$\dres$ which would indicate wrong order
        assert r"<$\dres$" not in latex

    def test_range_corestriction_not_split(self) -> None:
        """Test that |>> is not split into | and >>."""
        text = """EQUIV:
R |>> T
R |>> T [definition of |>>]"""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # Should have nrres (range corestriction)
        assert r"\mbox{definition of $\nrres$}" in latex

    def test_partial_injection_alt_not_split(self) -> None:
        """Test that -|> is not split into - and |>."""
        text = """EQUIV:
x in S
y in S [definition of -|>]"""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # Should have pinj (partial injection)
        assert r"\mbox{definition of $\pinj$}" in latex
        # Should NOT have -$\rres$ which would indicate wrong order
        assert r"-$\rres$" not in latex

    def test_multiple_overlapping_operators(self) -> None:
        """Test multiple operators with substring relationships in one justification."""
        text = """EQUIV:
x in S
y in T [definition of -> and +->]"""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # Should have both fun and pfun correctly
        assert r"$\fun$" in latex
        assert r"$\pfun$" in latex
        # Verify they appear in order in the justification
        assert r"\mbox{definition of $\fun$ $\land$ $\pfun$}" in latex

    def test_homework_question_5_line_220(self) -> None:
        """Test the actual homework bug: [x is not free in y |-> z]."""
        text = """EQUIV:
w |-> z in R
w |-> z in S [x is not free in y |-> z]"""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # Should have proper mapsto in the justification
        assert r"y $\mapsto$ z" in latex
        # Should NOT have |$\fun$ bug pattern
        assert r"|$\fun$" not in latex

    def test_relation_composition_with_maplet(self) -> None:
        """Test that o9 and |-> both work in same justification."""
        text = """EQUIV:
w |-> z in R o9 S
w |-> z in S o9 R [definition of |-> and o9]"""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # Should have both mapsto and circ
        assert r"$\mapsto$" in latex
        assert r"$\circ$" in latex
        # Verify in justification
        assert r"\mbox{definition of $\mapsto$ $\land$ $\circ$}" in latex


class TestProofTreeOperatorOrdering:
    """Test operator ordering in PROOF tree justifications."""

    def test_maplet_in_proof_justification(self) -> None:
        """Test |-> not split in proof tree justification."""
        text = """PROOF:
  x |-> y [definition of |->]"""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # Should have mapsto
        assert r"\mapsto" in latex
        # Should NOT have |$\fun$ or |\fun bug pattern
        assert r"|\fun" not in latex
        assert r"|$\fun$" not in latex
