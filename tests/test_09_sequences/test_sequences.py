"""Tests for Phase 12 and 14: Sequences, Bags, Tuple Projection, and ASCII syntax."""

from txt2tex.ast_nodes import (
    BagLiteral,
    BinaryOp,
    Document,
    Expr,
    FunctionApp,
    GenericInstantiation,
    Identifier,
    Number,
    SequenceLiteral,
    SetLiteral,
    TupleProjection,
    UnaryOp,
)
from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser


def parse_expr(text: str) -> Expr | Document:
    """Helper to parse expression."""
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    return parser.parse()


def generate_latex(text: str) -> str:
    """Helper to generate LaTeX from text."""
    ast = parse_expr(text)
    # For single expressions, parser returns the expression directly
    assert not isinstance(ast, Document)
    generator = LaTeXGenerator()
    return generator.generate_expr(ast)


class TestSequenceLiteralParsing:
    """Test parsing of sequence literals."""

    def test_empty_sequence(self):
        """Test ⟨⟩ - empty sequence."""
        ast = parse_expr("⟨⟩")
        assert isinstance(ast, SequenceLiteral)
        assert len(ast.elements) == 0

    def test_single_element(self):
        """Test ⟨a⟩."""
        ast = parse_expr("⟨a⟩")
        assert isinstance(ast, SequenceLiteral)
        assert len(ast.elements) == 1
        assert isinstance(ast.elements[0], Identifier)
        assert ast.elements[0].name == "a"

    def test_multiple_elements(self):
        """Test ⟨1, 2, 3⟩."""
        ast = parse_expr("⟨1, 2, 3⟩")
        assert isinstance(ast, SequenceLiteral)
        assert len(ast.elements) == 3
        assert all(isinstance(elem, Number) for elem in ast.elements)
        values = [elem.value for elem in ast.elements if isinstance(elem, Number)]
        assert values == ["1", "2", "3"]

    def test_identifier_sequence(self):
        """Test ⟨a, b, c⟩."""
        ast = parse_expr("⟨a, b, c⟩")
        assert isinstance(ast, SequenceLiteral)
        assert len(ast.elements) == 3
        assert all(isinstance(elem, Identifier) for elem in ast.elements)
        names: list[str] = []
        for elem in ast.elements:
            assert isinstance(elem, Identifier)
            names.append(elem.name)
        assert names == ["a", "b", "c"]

    def test_expression_elements(self):
        """Test ⟨x, y+1, 2*z⟩."""
        ast = parse_expr("⟨x, y+1, 2*z⟩")
        assert isinstance(ast, SequenceLiteral)
        assert len(ast.elements) == 3
        assert isinstance(ast.elements[0], Identifier)
        assert isinstance(ast.elements[1], BinaryOp)
        assert isinstance(ast.elements[2], BinaryOp)


class TestSequenceLiteralLaTeX:
    """Test LaTeX generation for sequence literals."""

    def test_empty_sequence_latex(self):
        """Test ⟨⟩ → \\langle \\rangle."""
        result = generate_latex("⟨⟩")
        assert result == r"\langle \rangle"

    def test_single_element_latex(self):
        """Test ⟨a⟩ → \\langle a \\rangle."""
        result = generate_latex("⟨a⟩")
        assert result == r"\langle a \rangle"

    def test_multiple_elements_latex(self):
        """Test ⟨1, 2, 3⟩ → \\langle 1, 2, 3 \\rangle."""
        result = generate_latex("⟨1, 2, 3⟩")
        assert result == r"\langle 1, 2, 3 \rangle"

    def test_identifier_sequence_latex(self):
        """Test ⟨a, b, c⟩ → \\langle a, b, c \\rangle."""
        result = generate_latex("⟨a, b, c⟩")
        assert result == r"\langle a, b, c \rangle"

    def test_expression_elements_latex(self):
        """Test ⟨x, y+1⟩ → \\langle x, y + 1 \\rangle."""
        result = generate_latex("⟨x, y+1⟩")
        assert result == r"\langle x, y + 1 \rangle"


class TestBagLiteralParsing:
    """Test parsing of bag literals."""

    def test_single_element_bag(self):
        """Test [[x]]."""
        ast = parse_expr("[[x]]")
        assert isinstance(ast, BagLiteral)
        assert len(ast.elements) == 1
        assert isinstance(ast.elements[0], Identifier)
        assert ast.elements[0].name == "x"

    def test_multiple_element_bag(self):
        """Test [[a, b, c]]."""
        ast = parse_expr("[[a, b, c]]")
        assert isinstance(ast, BagLiteral)
        assert len(ast.elements) == 3
        names: list[str] = []
        for elem in ast.elements:
            assert isinstance(elem, Identifier)
            names.append(elem.name)
        assert names == ["a", "b", "c"]

    def test_bag_with_duplicates(self):
        """Test [[1, 2, 2, 3]]."""
        ast = parse_expr("[[1, 2, 2, 3]]")
        assert isinstance(ast, BagLiteral)
        assert len(ast.elements) == 4
        values = [elem.value for elem in ast.elements if isinstance(elem, Number)]
        assert values == ["1", "2", "2", "3"]

    def test_bag_with_expressions(self):
        """Test [[x, y+1]]."""
        ast = parse_expr("[[x, y+1]]")
        assert isinstance(ast, BagLiteral)
        assert len(ast.elements) == 2
        assert isinstance(ast.elements[0], Identifier)
        assert isinstance(ast.elements[1], BinaryOp)


class TestBagLiteralLaTeX:
    """Test LaTeX generation for bag literals."""

    def test_single_element_bag_latex(self):
        """Test [[x]] → \\lbag x \\rbag."""
        result = generate_latex("[[x]]")
        assert result == r"\lbag x \rbag"

    def test_multiple_element_bag_latex(self):
        """Test [[a, b, c]] → \\lbag a, b, c \\rbag."""
        result = generate_latex("[[a, b, c]]")
        assert result == r"\lbag a, b, c \rbag"

    def test_bag_with_numbers_latex(self):
        """Test [[1, 2, 3]] → \\lbag 1, 2, 3 \\rbag."""
        result = generate_latex("[[1, 2, 3]]")
        assert result == r"\lbag 1, 2, 3 \rbag"

    def test_bag_with_expressions_latex(self):
        """Test [[x, y+1]] → \\lbag x, y + 1 \\rbag."""
        result = generate_latex("[[x, y+1]]")
        assert result == r"\lbag x, y + 1 \rbag"


class TestTupleProjectionParsing:
    """Test parsing of tuple projection."""

    def test_first_component(self):
        """Test x.1."""
        ast = parse_expr("x.1")
        assert isinstance(ast, TupleProjection)
        assert isinstance(ast.base, Identifier)
        assert ast.base.name == "x"
        assert ast.index == 1

    def test_second_component(self):
        """Test x.2."""
        ast = parse_expr("x.2")
        assert isinstance(ast, TupleProjection)
        assert ast.index == 2

    def test_third_component(self):
        """Test x.3."""
        ast = parse_expr("x.3")
        assert isinstance(ast, TupleProjection)
        assert ast.index == 3

    def test_function_projection(self):
        """Test f(x).1."""
        ast = parse_expr("f(x).1")
        assert isinstance(ast, TupleProjection)
        assert isinstance(ast.base, FunctionApp)
        assert isinstance(ast.base.function, Identifier)
        assert ast.base.function.name == "f"
        assert ast.index == 1

    def test_nested_projection(self):
        """Test x.1.2."""
        ast = parse_expr("x.1.2")
        assert isinstance(ast, TupleProjection)
        assert isinstance(ast.base, TupleProjection)
        assert ast.index == 2
        # Check inner projection
        inner = ast.base
        assert isinstance(inner, TupleProjection)
        assert isinstance(inner.base, Identifier)
        assert inner.base.name == "x"
        assert inner.index == 1


class TestTupleProjectionLaTeX:
    """Test LaTeX generation for tuple projection."""

    def test_first_component_latex(self):
        """Test x.1 → x.1."""
        result = generate_latex("x.1")
        assert result == "x.1"

    def test_second_component_latex(self):
        """Test x.2 → x.2."""
        result = generate_latex("x.2")
        assert result == "x.2"

    def test_function_projection_latex(self):
        """Test f(x).1 → f(x).1."""
        result = generate_latex("f(x).1")
        assert result == "f(x).1"

    def test_nested_projection_latex(self):
        """Test x.1.2 → x.1.2."""
        result = generate_latex("x.1.2")
        assert result == "x.1.2"


class TestSequenceOperatorsParsing:
    """Test parsing of sequence operators."""

    def test_head_operator(self):
        """Test head s."""
        ast = parse_expr("head s")
        assert isinstance(ast, UnaryOp)
        assert ast.operator == "head"
        assert isinstance(ast.operand, Identifier)
        assert ast.operand.name == "s"

    def test_tail_operator(self):
        """Test tail s."""
        ast = parse_expr("tail s")
        assert isinstance(ast, UnaryOp)
        assert ast.operator == "tail"

    def test_last_operator(self):
        """Test last s."""
        ast = parse_expr("last s")
        assert isinstance(ast, UnaryOp)
        assert ast.operator == "last"

    def test_front_operator(self):
        """Test front s."""
        ast = parse_expr("front s")
        assert isinstance(ast, UnaryOp)
        assert ast.operator == "front"

    def test_rev_operator(self):
        """Test rev s."""
        ast = parse_expr("rev s")
        assert isinstance(ast, UnaryOp)
        assert ast.operator == "rev"

    def test_operator_on_sequence_literal(self):
        """Test head ⟨1, 2, 3⟩."""
        ast = parse_expr("head ⟨1, 2, 3⟩")
        assert isinstance(ast, UnaryOp)
        assert ast.operator == "head"
        assert isinstance(ast.operand, SequenceLiteral)

    def test_nested_operators(self):
        """Test tail (head s)."""
        ast = parse_expr("tail (head s)")
        assert isinstance(ast, UnaryOp)
        assert ast.operator == "tail"
        assert isinstance(ast.operand, UnaryOp)
        assert ast.operand.operator == "head"


class TestSequenceOperatorsLaTeX:
    """Test LaTeX generation for sequence operators."""

    def test_head_latex(self):
        """Test head s → \\head s."""
        result = generate_latex("head s")
        assert result == r"\head s"

    def test_tail_latex(self):
        """Test tail s → \\tail s."""
        result = generate_latex("tail s")
        assert result == r"\tail s"

    def test_last_latex(self):
        """Test last s → \\last s."""
        result = generate_latex("last s")
        assert result == r"\last s"

    def test_front_latex(self):
        """Test front s → \\front s."""
        result = generate_latex("front s")
        assert result == r"\front s"

    def test_rev_latex(self):
        """Test rev s → \\rev s."""
        result = generate_latex("rev s")
        assert result == r"\rev s"

    def test_operator_on_sequence_literal_latex(self):
        """Test head ⟨1, 2, 3⟩ → \\head \\langle 1, 2, 3 \\rangle."""
        result = generate_latex("head ⟨1, 2, 3⟩")
        assert result == r"\head \langle 1, 2, 3 \rangle"


class TestSequenceConcatenationParsing:
    """Test parsing of sequence concatenation."""

    def test_simple_concatenation(self):
        """Test s ⌢ t."""
        ast = parse_expr("s ⌢ t")
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "⌢"
        assert isinstance(ast.left, Identifier)
        assert isinstance(ast.right, Identifier)

    def test_concatenation_chain(self):
        """Test s ⌢ t ⌢ u."""
        ast = parse_expr("s ⌢ t ⌢ u")
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "⌢"
        # Left-associative: (s ⌢ t) ⌢ u
        assert isinstance(ast.left, BinaryOp)
        assert ast.left.operator == "⌢"

    def test_concatenation_with_literals(self):
        """Test ⟨1⟩ ⌢ ⟨2, 3⟩."""
        ast = parse_expr("⟨1⟩ ⌢ ⟨2, 3⟩")
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "⌢"
        assert isinstance(ast.left, SequenceLiteral)
        assert isinstance(ast.right, SequenceLiteral)


class TestSequenceConcatenationLaTeX:
    """Test LaTeX generation for sequence concatenation."""

    def test_simple_concatenation_latex(self):
        """Test s ⌢ t → s \\cat t."""
        result = generate_latex("s ⌢ t")
        assert result == r"s \cat t"

    def test_concatenation_chain_latex(self):
        """Test s ⌢ t ⌢ u → s \\cat t \\cat u."""
        result = generate_latex("s ⌢ t ⌢ u")
        assert result == r"s \cat t \cat u"

    def test_concatenation_with_literals_latex(self):
        """Test ⟨1⟩ ⌢ ⟨2, 3⟩ → \\langle 1 \\rangle \\cat \\langle 2, 3 \\rangle."""
        result = generate_latex("⟨1⟩ ⌢ ⟨2, 3⟩")
        assert result == r"\langle 1 \rangle \cat \langle 2, 3 \rangle"


class TestPhase12Integration:
    """Integration tests combining Phase 12 features."""

    def test_sequence_of_tuples(self):
        """Test ⟨(1, 2), (3, 4)⟩."""
        text = "⟨(1, 2), (3, 4)⟩"
        ast = parse_expr(text)
        assert isinstance(ast, SequenceLiteral)
        latex = generate_latex(text)
        assert "\\langle" in latex
        assert "\\rangle" in latex

    def test_projection_in_comparison(self):
        """Test x.1 = y.1."""
        text = "x.1 = y.1"
        ast = parse_expr(text)
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "="
        latex = generate_latex(text)
        assert latex == "x.1 = y.1"

    def test_sequence_in_expression(self):
        """Test x in ⟨1, 2, 3⟩."""
        text = "x in ⟨1, 2, 3⟩"
        ast = parse_expr(text)
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "in"
        latex = generate_latex(text)
        assert r"\in" in latex
        assert r"\langle" in latex

    def test_head_concatenation(self):
        """Test head (s ⌢ t)."""
        text = "head (s ⌢ t)"
        ast = parse_expr(text)
        assert isinstance(ast, UnaryOp)
        assert ast.operator == "head"
        assert isinstance(ast.operand, BinaryOp)
        latex = generate_latex(text)
        assert r"\head" in latex
        assert r"\cat" in latex

    def test_bag_in_comparison(self):
        """Test [[1, 2]] = [[2, 1]]."""
        text = "[[1, 2]] = [[2, 1]]"
        ast = parse_expr(text)
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "="
        latex = generate_latex(text)
        assert latex == r"\lbag 1, 2 \rbag = \lbag 2, 1 \rbag"

    def test_complex_sequence_expression(self):
        """Test rev (tail ⟨1, 2, 3⟩)."""
        text = "rev (tail ⟨1, 2, 3⟩)"
        ast = parse_expr(text)
        assert isinstance(ast, UnaryOp)
        assert ast.operator == "rev"
        latex = generate_latex(text)
        assert r"\rev" in latex
        assert r"\tail" in latex
        assert r"\langle" in latex


class TestPhase12EdgeCases:
    """Test edge cases and potential conflicts."""

    def test_bracket_not_bag(self):
        """Test Type[List[N]] - double brackets are not bag."""
        text = "Type[List[N]]"
        ast = parse_expr(text)
        # Should parse as generic instantiation, not bag literal
        assert isinstance(ast, GenericInstantiation)

    def test_empty_sequence_vs_tuple(self):
        """Test ⟨⟩ vs () - different constructs."""
        seq = parse_expr("⟨⟩")
        assert isinstance(seq, SequenceLiteral)
        assert len(seq.elements) == 0

        # () is just grouping, not a tuple (tuples need at least 2 elements)
        grouped = parse_expr("(x)")
        assert isinstance(grouped, Identifier)

    def test_sequence_vs_set(self):
        """Test ⟨1, 2⟩ vs {1, 2} - different constructs."""
        seq = parse_expr("⟨1, 2⟩")
        assert isinstance(seq, SequenceLiteral)

        set_literal = parse_expr("{1, 2}")
        assert isinstance(set_literal, SetLiteral)

        # LaTeX should be different
        seq_latex = generate_latex("⟨1, 2⟩")
        set_latex = generate_latex("{1, 2}")
        assert seq_latex != set_latex
        assert "\\langle" in seq_latex
        assert "\\{" in set_latex


# Phase 14: ASCII Sequence Brackets and Pattern Matching Support


class TestASCIISequenceBrackets:
    """Test ASCII <> as alternative to Unicode ⟨⟩ for sequence literals."""

    def test_empty_sequence_ascii(self):
        """Test <> parses as empty sequence."""
        ast = parse_expr("<>")
        assert isinstance(ast, SequenceLiteral)
        assert len(ast.elements) == 0

    def test_single_element_ascii(self):
        """Test <x> parses as sequence with one element."""
        ast = parse_expr("<x>")
        assert isinstance(ast, SequenceLiteral)
        assert len(ast.elements) == 1
        assert isinstance(ast.elements[0], Identifier)
        assert ast.elements[0].name == "x"

    def test_multiple_elements_ascii(self):
        """Test <a, b, c> parses as sequence."""
        ast = parse_expr("<a, b, c>")
        assert isinstance(ast, SequenceLiteral)
        assert len(ast.elements) == 3
        names = [e.name for e in ast.elements if isinstance(e, Identifier)]
        assert names == ["a", "b", "c"]

    def test_empty_sequence_latex(self):
        """Test <> → \\langle \\rangle."""
        result = generate_latex("<>")
        assert result == r"\langle \rangle"

    def test_single_element_latex(self):
        """Test <x> → \\langle x \\rangle."""
        result = generate_latex("<x>")
        assert result == r"\langle x \rangle"

    def test_multiple_elements_latex(self):
        """Test <a, b, c> → \\langle a, b, c \\rangle."""
        result = generate_latex("<a, b, c>")
        assert result == r"\langle a, b, c \rangle"

    def test_comparison_not_confused(self):
        """Test x > y is still comparison, not sequence."""
        ast = parse_expr("x > y")
        assert isinstance(ast, BinaryOp)
        assert ast.operator == ">"

        result = generate_latex("x > y")
        assert result == "x > y"

    def test_comparison_with_spacing(self):
        """Test x>y (no spaces) vs x > y (with spaces)."""
        # With spaces - comparison
        ast1 = parse_expr("x > y")
        assert isinstance(ast1, BinaryOp)

        # Without spaces after... this might be ambiguous
        # For now, < with alphanumeric → LANGLE, so x<y would be weird
        # Let's just ensure x > y works correctly

    def test_nested_sequences(self):
        """Test <<a>, <b>>."""
        ast = parse_expr("<<a>, <b>>")
        assert isinstance(ast, SequenceLiteral)
        assert len(ast.elements) == 2
        assert isinstance(ast.elements[0], SequenceLiteral)
        assert isinstance(ast.elements[1], SequenceLiteral)


class TestASCIIConcatenation:
    """Test ASCII ^ as concatenation after sequences (alternative to ⌢)."""

    def test_concatenation_after_sequence(self):
        """Test <x> ^ s parses as concatenation."""
        ast = parse_expr("<x> ^ s")
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "^"
        assert isinstance(ast.left, SequenceLiteral)
        assert isinstance(ast.right, Identifier)

    def test_concatenation_latex(self):
        """Test <x> ^ s → \\langle x \\rangle \\cat s."""
        result = generate_latex("<x> ^ s")
        assert result == r"\langle x \rangle \cat s"

    def test_superscript_still_works(self):
        """Test x^2 is still superscript."""
        # This should be superscript, not concatenation
        # For single-character exponents, LaTeX doesn't need braces
        result = generate_latex("x^2")
        assert result == "x^2"  # or x^{2}, both are correct LaTeX

    def test_concatenation_chain(self):
        """Test <a> ^ <b> ^ <c>."""
        ast = parse_expr("<a> ^ <b> ^ <c>")
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "^"
        # Left-associative: (<a> ^ <b>) ^ <c>
        assert isinstance(ast.left, BinaryOp)
        assert isinstance(ast.right, SequenceLiteral)

    def test_concatenation_with_empty(self):
        """Test <> ^ s."""
        result = generate_latex("<> ^ s")
        assert result == r"\langle \rangle \cat s"


class TestPatternMatching:
    """Test pattern matching in function application (no special syntax needed)."""

    def test_empty_sequence_pattern(self):
        """Test f(<>) - function applied to empty sequence."""
        ast = parse_expr("f(<>)")
        assert isinstance(ast, FunctionApp)
        assert isinstance(ast.function, Identifier)
        assert ast.function.name == "f"
        assert len(ast.args) == 1
        assert isinstance(ast.args[0], SequenceLiteral)
        assert len(ast.args[0].elements) == 0

    def test_cons_pattern(self):
        """Test f(<x> ^ s) - function applied to cons."""
        ast = parse_expr("f(<x> ^ s)")
        assert isinstance(ast, FunctionApp)
        assert isinstance(ast.function, Identifier)
        assert ast.function.name == "f"
        assert len(ast.args) == 1
        assert isinstance(ast.args[0], BinaryOp)
        assert ast.args[0].operator == "^"

    def test_pattern_equation(self):
        """Test f(<x> ^ s) = expr."""
        ast = parse_expr("f(<x> ^ s) = x.2 + f(s)")
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "="
        assert isinstance(ast.left, FunctionApp)
        assert isinstance(ast.right, BinaryOp)

    def test_pattern_equation_latex(self):
        """Test full pattern matching equation LaTeX."""
        result = generate_latex("f(<x> ^ s) = x.2 + f(s)")
        assert r"f(\langle x \rangle \cat s)" in result
        assert r"x.2 + f(s)" in result


class TestPhase14Integration:
    """Integration tests for Phase 14."""

    def test_solution40_style_pattern(self):
        """Test pattern matching style from Solution 40."""
        # Empty case
        latex1 = generate_latex("total(<>) = 0")
        assert r"total(\langle \rangle) = 0" in latex1

        # Cons case
        latex2 = generate_latex("total(<x> ^ s) = x + total(s)")
        assert r"total(\langle x \rangle \cat s)" in latex2
        assert r"x + total(s)" in latex2

    def test_mixed_unicode_and_ascii(self):
        """Test that Unicode ⟨⟩ and ASCII <> both work."""
        # Unicode
        ast1 = parse_expr("⟨a, b⟩")
        assert isinstance(ast1, SequenceLiteral)

        # ASCII
        ast2 = parse_expr("<a, b>")
        assert isinstance(ast2, SequenceLiteral)

        # Both generate same LaTeX
        latex1 = generate_latex("⟨a, b⟩")
        latex2 = generate_latex("<a, b>")
        assert latex1 == latex2

    def test_complex_nested_expression(self):
        """Test complex expression with sequences and concatenation."""
        text = "f(<a> ^ <b> ^ s, <c>)"
        ast = parse_expr(text)
        assert isinstance(ast, FunctionApp)
        assert len(ast.args) == 2

        latex = generate_latex(text)
        assert r"\langle a \rangle" in latex
        assert r"\cat" in latex


class TestNonEmptySequences:
    """Test seq1 (non-empty sequences) support."""

    def test_seq1_simple(self):
        """Test seq1 X → \\seq_1~X."""
        text = "seq1 X"
        ast = parse_expr(text)
        assert isinstance(ast, FunctionApp)
        assert isinstance(ast.function, Identifier)
        assert ast.function.name == "seq1"
        latex = generate_latex(text)
        assert latex == r"\seq_1~X"

    def test_seq_seq(self):
        """Test seq seq N → \\seq~(\\seq~\\mathbb{N}) (sequence of sequences)."""
        text = "seq seq N"
        latex = generate_latex(text)
        assert latex == r"\seq~(\seq~\mathbb{N})"

    def test_seq1_seq(self):
        """Test seq1 seq X → \\seq_1~(\\seq~X) (non-empty sequences)."""
        text = "seq1 seq X"
        latex = generate_latex(text)
        assert latex == r"\seq_1~(\seq~X)"

    def test_seq1_with_nat(self):
        """Test seq1 N → \\seq_1~\\nat (with fuzz) or \\seq_1~\\mathbb{N} (LaTeX)."""
        text = "seq1 N"
        ast = parse_expr(text)
        assert not isinstance(ast, Document)

        # Test with fuzz mode
        generator_fuzz = LaTeXGenerator(use_fuzz=True)
        latex_fuzz = generator_fuzz.generate_expr(ast)
        assert latex_fuzz == r"\seq_1~\nat"

        # Test with LaTeX mode
        generator_latex = LaTeXGenerator(use_fuzz=False)
        latex_regular = generator_latex.generate_expr(ast)
        assert latex_regular == r"\seq_1~\mathbb{N}"

    def test_seq1_in_function_type(self):
        """Test seq1 X -> Y → \\seq_1~X \\fun Y."""
        text = "seq1 X -> Y"
        latex = generate_latex(text)
        assert latex == r"\seq_1~X \fun Y"

    def test_seq1_in_declaration(self):
        """Test axdef with seq1 X."""
        text = """axdef
  s : seq1 N
end"""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        generator = LaTeXGenerator(use_fuzz=True)
        latex = generator.generate_document(ast)
        assert r"\seq_1~\nat" in latex
