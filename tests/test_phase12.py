"""Tests for Phase 12: Sequences, Bags, and Tuple Projection."""

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
        names = []
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
        names = []
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
