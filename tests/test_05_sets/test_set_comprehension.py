"""Tests for Phase 8: Set Comprehension."""

from txt2tex.ast_nodes import (
    BinaryOp,
    Document,
    Identifier,
    SetComprehension,
    Superscript,
)
from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser


class TestPhase8Parsing:
    """Test parsing of set comprehension syntax."""

    def test_simple_set_by_predicate(self) -> None:
        """Test parsing simple set comprehension: { x : N | x > 0 }."""
        lexer = Lexer("{ x : N | x > 0 }")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        assert isinstance(ast, SetComprehension)
        assert ast.variables == ["x"]
        assert isinstance(ast.domain, Identifier)
        assert ast.domain.name == "N"
        assert isinstance(ast.predicate, BinaryOp)
        assert ast.predicate.operator == ">"
        assert ast.expression is None  # No expression part

    def test_set_by_expression(self) -> None:
        """Test parsing set with expression: { x : N | x > 0 . x^2 }."""
        lexer = Lexer("{ x : N | x > 0 . x^2 }")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        assert isinstance(ast, SetComprehension)
        assert ast.variables == ["x"]
        assert isinstance(ast.domain, Identifier)
        assert ast.domain.name == "N"
        assert isinstance(ast.predicate, BinaryOp)
        assert ast.predicate.operator == ">"
        assert ast.expression is not None
        assert isinstance(ast.expression, Superscript)

    def test_multi_variable_set(self) -> None:
        """Test parsing multi-variable set: { x, y : N | x = y }."""
        lexer = Lexer("{ x, y : N | x = y }")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        assert isinstance(ast, SetComprehension)
        assert ast.variables == ["x", "y"]
        assert isinstance(ast.domain, Identifier)
        assert ast.domain.name == "N"
        assert isinstance(ast.predicate, BinaryOp)
        assert ast.predicate.operator == "="

    def test_set_without_domain(self) -> None:
        """Test parsing set without domain: { x | x in A }."""
        lexer = Lexer("{ x | x in A }")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        assert isinstance(ast, SetComprehension)
        assert ast.variables == ["x"]
        assert ast.domain is None
        assert isinstance(ast.predicate, BinaryOp)
        assert ast.predicate.operator == "in"

    def test_set_in_document(self) -> None:
        """Test set comprehension within a document."""
        lexer = Lexer("{ x : N | x > 0 }\n{ y : Z | y < 0 }")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        assert isinstance(ast, Document)
        assert len(ast.items) == 2
        assert isinstance(ast.items[0], SetComprehension)
        assert isinstance(ast.items[1], SetComprehension)


class TestPhase8LaTeXGeneration:
    """Test LaTeX generation for set comprehension."""

    def test_generate_simple_set_by_predicate(self) -> None:
        """Test LaTeX generation for { x : N | x > 0 }."""
        gen = LaTeXGenerator()
        set_comp = SetComprehension(
            variables=["x"],
            domain=Identifier(name="N", line=1, column=5),
            predicate=BinaryOp(
                operator=">",
                left=Identifier(name="x", line=1, column=11),
                right=Identifier(name="0", line=1, column=15),
                line=1,
                column=13,
            ),
            expression=None,
            line=1,
            column=1,
        )

        latex = gen.generate_expr(set_comp)

        assert r"\{" in latex
        assert r"\}" in latex
        assert r"\colon" in latex
        assert r"\mid" in latex
        assert r"\bullet" not in latex  # No expression part
        assert "x" in latex
        assert "N" in latex
        assert ">" in latex
        assert "0" in latex

    def test_generate_set_by_expression(self) -> None:
        """Test LaTeX generation for { x : N | x > 0 . x^2 }."""
        gen = LaTeXGenerator()
        set_comp = SetComprehension(
            variables=["x"],
            domain=Identifier(name="N", line=1, column=5),
            predicate=BinaryOp(
                operator=">",
                left=Identifier(name="x", line=1, column=11),
                right=Identifier(name="0", line=1, column=15),
                line=1,
                column=13,
            ),
            expression=Superscript(
                base=Identifier(name="x", line=1, column=19),
                exponent=Identifier(name="2", line=1, column=21),
                line=1,
                column=20,
            ),
            line=1,
            column=1,
        )

        latex = gen.generate_expr(set_comp)

        assert r"\{" in latex
        assert r"\}" in latex
        assert r"\colon" in latex
        assert r"\mid" in latex
        assert r"\bullet" in latex  # Has expression part
        assert "x" in latex
        assert "N" in latex
        assert r"\bsup" in latex
        assert "2" in latex

    def test_generate_multi_variable_set(self) -> None:
        """Test LaTeX generation for { x, y : N | x = y }."""
        gen = LaTeXGenerator()
        set_comp = SetComprehension(
            variables=["x", "y"],
            domain=Identifier(name="N", line=1, column=9),
            predicate=BinaryOp(
                operator="=",
                left=Identifier(name="x", line=1, column=15),
                right=Identifier(name="y", line=1, column=19),
                line=1,
                column=17,
            ),
            expression=None,
            line=1,
            column=1,
        )

        latex = gen.generate_expr(set_comp)

        assert r"\{" in latex
        assert r"\}" in latex
        assert r"\colon" in latex
        assert r"\mid" in latex
        assert "x, y" in latex or "x , y" in latex  # May have spacing
        assert "N" in latex
        assert "=" in latex

    def test_generate_set_without_domain(self) -> None:
        """Test LaTeX generation for { x | x in A }."""
        gen = LaTeXGenerator()
        set_comp = SetComprehension(
            variables=["x"],
            domain=None,
            predicate=BinaryOp(
                operator="in",
                left=Identifier(name="x", line=1, column=7),
                right=Identifier(name="A", line=1, column=12),
                line=1,
                column=9,
            ),
            expression=None,
            line=1,
            column=1,
        )

        latex = gen.generate_expr(set_comp)

        assert r"\{" in latex
        assert r"\}" in latex
        assert r"\colon" not in latex  # No domain
        assert r"\mid" in latex
        assert r"\in" in latex
        assert "x" in latex
        assert "A" in latex

    def test_generate_document_with_set(self) -> None:
        """Test LaTeX generation for document containing set comprehension."""
        gen = LaTeXGenerator()
        doc = Document(
            items=[
                SetComprehension(
                    variables=["x"],
                    domain=Identifier(name="N", line=1, column=5),
                    predicate=BinaryOp(
                        operator=">",
                        left=Identifier(name="x", line=1, column=11),
                        right=Identifier(name="0", line=1, column=15),
                        line=1,
                        column=13,
                    ),
                    expression=None,
                    line=1,
                    column=1,
                ),
            ],
            line=1,
            column=1,
        )

        latex = gen.generate_document(doc)

        assert r"\documentclass[a4paper,10pt,fleqn]{article}" in latex
        assert r"\begin{document}" in latex
        assert r"\{" in latex
        assert r"\}" in latex
        assert r"\end{document}" in latex


class TestPhase8Integration:
    """Integration tests for Phase 8."""

    def test_end_to_end_simple_set(self) -> None:
        """Test complete pipeline from text to LaTeX for simple set."""
        text = "{ x : N | x > 0 }"

        # Lex
        lexer = Lexer(text)
        tokens = lexer.tokenize()

        # Parse
        parser = Parser(tokens)
        ast = parser.parse()

        # Generate
        gen = LaTeXGenerator()
        # ast is SetComprehension here, not Document
        assert isinstance(ast, SetComprehension)
        latex = gen.generate_expr(ast)

        # Verify
        assert r"\{" in latex
        assert r"\mid" in latex
        assert r"\}" in latex

    def test_end_to_end_set_by_expression(self) -> None:
        """Test complete pipeline for set by expression."""
        text = "{ x : N | x > 0 . x^2 }"

        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        assert isinstance(ast, SetComprehension)
        assert ast.expression is not None

        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)

        assert r"\bullet" in latex
        assert r"\bsup" in latex

    def test_end_to_end_multi_variable(self) -> None:
        """Test complete pipeline for multi-variable set."""
        text = "{ x, y, z : N | x = y and y = z }"

        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        assert isinstance(ast, SetComprehension)
        assert ast.variables == ["x", "y", "z"]

        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)

        assert "x" in latex
        assert "y" in latex
        assert "z" in latex


# Set comprehension with period separator tests


def test_set_comp_with_period_separator() -> None:
    """Test set comprehension with period separator: {x : N . expr}."""
    text = "{p : Person . p |-> f(p)}"
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    result = parser.parse()

    # Should parse as: {p : Person . p |-> f(p)} with predicate=None
    assert isinstance(result, SetComprehension)
    assert result.variables == ["p"]
    assert result.predicate is None
    assert result.expression is not None


def test_set_comp_period_vs_pipe() -> None:
    """Test difference between period and pipe separator."""
    # Period: no predicate
    text1 = "{x : N . x * 2}"
    lexer1 = Lexer(text1)
    result1 = Parser(lexer1.tokenize()).parse()
    assert isinstance(result1, SetComprehension)
    assert result1.predicate is None
    assert result1.expression is not None

    # Pipe: has predicate
    text2 = "{x : N | x > 0 . x * 2}"
    lexer2 = Lexer(text2)
    result2 = Parser(lexer2.tokenize()).parse()
    assert isinstance(result2, SetComprehension)
    assert result2.predicate is not None
    assert result2.expression is not None


class TestUnaryOperatorsInSetComprehensions:
    """Test unary operators (# , not, -) in set comprehension contexts."""

    def test_hash_in_predicate(self) -> None:
        """Test # operator in set comprehension predicate."""
        text = "{i : 1 .. 5 | # s(i) > 0}"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, SetComprehension)
        # Verify it parsed successfully

    def test_hash_in_expression(self) -> None:
        """Test # operator in set comprehension expression part."""
        text = "{i : 1 .. 5 . # s(i)}"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, SetComprehension)
        # Verify it parsed successfully

    def test_nested_set_with_hash(self) -> None:
        """Test nested set comprehensions with # in predicate."""
        text = "{i : 1 .. n | # {j : 1 .. i | j > 0} > 0}"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, SetComprehension)

    def test_hash_with_function_application(self) -> None:
        """Test # applied to function application in predicate."""
        text = "{i : 1 .. # s | # s(i) = i}"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, SetComprehension)

    def test_not_in_predicate(self) -> None:
        """Test not operator in set comprehension predicate."""
        text = "{x : N | not x > 0}"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, SetComprehension)

    def test_minus_in_predicate(self) -> None:
        """Test unary minus in set comprehension predicate."""
        text = "{x : N | -x > 0}"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, SetComprehension)

    def test_latex_generation_hash_predicate(self) -> None:
        """Test LaTeX generation for # in predicate."""
        text = "{i : 1 .. n | # s(i) > 0}"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert not isinstance(ast, Document)
        generator = LaTeXGenerator()
        latex = generator.generate_expr(ast)
        assert r"\#" in latex
        assert "s(i)" in latex
