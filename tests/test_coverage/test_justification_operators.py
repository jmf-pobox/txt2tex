"""Tests for Phase 25: Operator conversion in justifications (EQUIV and PROOF).

Tests that relation operators, function type operators, and other mathematical
operators are properly converted to LaTeX symbols when used in justifications.
"""

from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser


class TestEquivJustificationOperators:
    """Test operator conversion in EQUIV chain justifications."""

    def test_relation_operators_in_justifications(self) -> None:
        """Test relation operators (o9, |->, <->, etc.) in justifications."""
        text = """EQUIV:
R o9 S
S o9 R [definition of o9]"""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # The justification should have o9 converted to \circ
        assert r"\mbox{definition of $\circ$}" in latex

    def test_maplet_in_justifications(self) -> None:
        """Test maplet operator (|->) in justifications."""
        text = """EQUIV:
x |-> y in R
y |-> x in R [definition of |->]"""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # The justification should have |-> converted to \mapsto
        assert r"\mbox{definition of $\mapsto$}" in latex

    def test_function_type_operators_in_justifications(self) -> None:
        """Test function type operators (->
        , +->
        , etc.) in justifications."""
        text = """EQUIV:
f : X -> Y
f : X -> Y [definition of ->]"""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # The justification should have -> converted to \fun
        assert r"\mbox{definition of $\fun$}" in latex

    def test_partial_function_in_justifications(self) -> None:
        """Test partial function operator (+->) in justifications."""
        text = """EQUIV:
f : X +-> Y
f : X +-> Y [definition of +->]"""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # The justification should have +-> converted to \pfun
        assert r"\mbox{definition of $\pfun$}" in latex

    def test_injection_in_justifications(self) -> None:
        """Test injection operator (>->) in justifications."""
        text = """EQUIV:
f : X >-> Y
f : X >-> Y [definition of >->]"""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # The justification should have >-> converted to \inj
        assert r"\mbox{definition of $\inj$}" in latex

    def test_surjection_in_justifications(self) -> None:
        """Test surjection operator (-->>) in justifications."""
        text = """EQUIV:
f : X -->> Y
f : X -->> Y [definition of -->>]"""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # The justification should have -->> converted to \surj
        assert r"\mbox{definition of $\surj$}" in latex

    def test_bijection_in_justifications(self) -> None:
        """Test bijection operator (>->>) in justifications."""
        text = """EQUIV:
f : X >->> Y
f : X >->> Y [definition of >->>]"""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # The justification should have >->> converted to \bij
        assert r"\mbox{definition of $\bij$}" in latex

    def test_domain_restriction_in_justifications(self) -> None:
        """Test domain restriction operator (<|) in justifications."""
        text = """EQUIV:
S <| R
S <| R [definition of <|]"""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # The justification should have <| converted to \dres
        assert r"\mbox{definition of $\dres$}" in latex

    def test_range_restriction_in_justifications(self) -> None:
        """Test range restriction operator (|>) in justifications."""
        text = """EQUIV:
R |> T
R |> T [definition of |>]"""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # The justification should have |> converted to \rres
        assert r"\mbox{definition of $\rres$}" in latex

    def test_domain_corestriction_in_justifications(self) -> None:
        """Test domain corestriction operator (<<|) in justifications."""
        text = """EQUIV:
S <<| R
S <<| R [definition of <<|]"""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # The justification should have <<| converted to \ndres
        assert r"\mbox{definition of $\ndres$}" in latex

    def test_range_corestriction_in_justifications(self) -> None:
        """Test range corestriction operator (|>>) in justifications."""
        text = """EQUIV:
R |>> T
R |>> T [definition of |>>]"""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # The justification should have |>> converted to \nrres
        assert r"\mbox{definition of $\nrres$}" in latex

    def test_relation_type_in_justifications(self) -> None:
        """Test relation type operator (<->) in justifications."""
        text = """EQUIV:
R in X <-> Y
R in X <-> Y [definition of <->]"""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # The justification should have <-> converted to \rel
        assert r"\mbox{definition of $\rel$}" in latex

    def test_override_in_justifications(self) -> None:
        """Test override operator (++) in justifications."""
        text = """EQUIV:
f ++ g
g ++ f [definition of ++]"""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # The justification should have ++ converted to \oplus
        assert r"\mbox{definition of $\oplus$}" in latex

    def test_relation_functions_in_justifications(self) -> None:
        """Test relation functions (dom, ran, comp, inv, id) in justifications."""
        text = """EQUIV:
dom R
ran R [definition of dom and ran]"""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # The justification should have dom and ran converted
        assert r"\mbox{definition of $\dom$ $\land$ $\ran$}" in latex

    def test_mixed_logical_and_relation_operators(self) -> None:
        """Test mix of logical and relation operators in justifications."""
        text = """EQUIV:
x |-> y in R and y |-> z in S
z |-> x in S o9 R [definition of o9 and |->]"""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # The justification should have both o9 and |-> converted
        assert r"\mbox{definition of $\circ$ $\land$ $\mapsto$}" in latex


class TestProofJustificationOperators:
    """Test operator conversion in PROOF tree justifications."""

    def test_relation_operator_in_proof_justification(self) -> None:
        """Test relation operator (o9) in proof tree justification."""
        text = """PROOF:
  R o9 S [definition of o9]"""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # The justification should have o9 converted to \circ
        assert r"\circ" in latex
        assert r"\mathrm{definition}" in latex

    def test_maplet_in_proof_justification(self) -> None:
        """Test maplet (|->) in proof tree justification."""
        text = """PROOF:
  x |-> y [definition of |->]"""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # The justification should have |-> converted to \mapsto
        assert r"\mapsto" in latex
        assert r"\mathrm{definition}" in latex

    def test_function_operator_in_proof_justification(self) -> None:
        """Test function type operator (->) in proof tree justification."""
        text = """PROOF:
  f : X -> Y [definition of ->]"""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # The justification should have -> converted to \fun
        assert r"\fun" in latex
        assert r"\mathrm{definition}" in latex

    def test_mixed_operators_in_proof_discharge(self) -> None:
        """Test operators in proof tree with discharge notation."""
        text = """PROOF:
  R o9 S [=> intro from 1]
    [1] P [assumption]"""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # The justification should have => converted (for intro pattern)
        assert r"\Rightarrow" in latex
        assert r"\textrm{-intro}" in latex

    def test_relation_function_in_proof_justification(self) -> None:
        """Test relation function (dom) in proof tree justification."""
        text = """PROOF:
  dom R subset X [definition of dom]"""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # The justification should have dom converted to \dom
        assert r"\dom" in latex
        assert r"\mathrm{definition}" in latex


class TestComplexJustificationScenarios:
    """Test complex scenarios with multiple operators and edge cases."""

    def test_user_homework_question_5(self) -> None:
        """Test the actual homework scenario from Question 5."""
        text = """EQUIV:
w |-> z in (R o9 S) o9 T
(exists y : Y | w |-> y in (R o9 S) and y |-> z in T) [definition of o9]"""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # The justification should have o9 converted to \circ
        assert r"\mbox{definition of $\circ$}" in latex
        # Should NOT have literal "o9" in justification
        assert r"\mbox{definition of o9}" not in latex

    def test_multiple_operators_in_one_justification(self) -> None:
        """Test multiple different operators in a single justification."""
        text = """EQUIV:
x |-> y in R and R in X <-> Y
y |-> x in R and R in Y <-> X [definition of |-> and <->]"""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # Both |-> and <-> should be converted
        assert r"$\mapsto$" in latex
        assert r"$\rel$" in latex
        assert r"\land" in latex  # 'and' should also be converted

    def test_operator_precedence_in_justifications(self) -> None:
        """Test that longer operators are matched before shorter ones."""
        # This tests that |>> is matched before |> and <<| before <|
        text = """EQUIV:
R |>> T
R |>> T [definition of |>>]

S <<| R
S <<| R [definition of <<|]"""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # Should match full operators, not partial
        assert r"\mbox{definition of $\nrres$}" in latex
        assert r"\mbox{definition of $\ndres$}" in latex
        # Should not have incorrect partial matches
        assert r"\rres>" not in latex
        assert r"<\dres" not in latex

    def test_function_type_precedence_in_justifications(self) -> None:
        """Test that longer function type operators are matched correctly."""
        # Tests that >->> is matched before >-> and +-> before ->
        text = """EQUIV:
f : X >->> Y
f : X >->> Y [definition of >->>]

g : X +-> Y
g : X +-> Y [definition of +->]"""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # Should match full operators
        assert r"\mbox{definition of $\bij$}" in latex
        assert r"\mbox{definition of $\pfun$}" in latex
        # Should not have incorrect partial matches
        assert r"\inj>" not in latex
        assert r"\fun" not in latex or r"$\pfun$" in latex  # \pfun contains \fun
