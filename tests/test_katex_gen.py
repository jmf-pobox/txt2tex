"""Tests for KaTeX HTML generator.

Tests the KaTeXGenerator class which converts txt2tex AST to HTML
with KaTeX math rendering.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from txt2tex.ast_nodes import (
    Abbreviation,
    ArgueChain,
    ArgueStep,
    AxDef,
    BinaryOp,
    Declaration,
    Document,
    FreeBranch,
    FreeType,
    FunctionApp,
    FunctionType,
    GenDef,
    GivenType,
    Identifier,
    Lambda,
    Number,
    Paragraph,
    Part,
    ProofNode,
    ProofTree,
    Quantifier,
    Schema,
    Section,
    SequenceLiteral,
    SetComprehension,
    SetLiteral,
    Solution,
    Subscript,
    Superscript,
    TruthTable,
    Tuple,
    UnaryOp,
)
from txt2tex.cli import main
from txt2tex.katex_gen import KaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser


@pytest.fixture
def generator() -> KaTeXGenerator:
    """Create a KaTeX generator instance."""
    return KaTeXGenerator()


class TestKaTeXGeneratorBasics:
    """Test basic KaTeX generation functionality."""

    def test_identifier(self, generator: KaTeXGenerator) -> None:
        """Test identifier rendering."""
        node = Identifier(line=1, column=1, name="x")
        result = generator.generate_expr(node)
        assert result == "x"

    def test_number(self, generator: KaTeXGenerator) -> None:
        """Test number rendering."""
        node = Number(line=1, column=1, value="42")
        result = generator.generate_expr(node)
        assert result == "42"

    def test_multichar_identifier(self, generator: KaTeXGenerator) -> None:
        """Test multi-character identifier rendering."""
        node = Identifier(line=1, column=1, name="count")
        result = generator.generate_expr(node)
        assert result == r"\mathit{count}"

    def test_type_identifier_nat(self, generator: KaTeXGenerator) -> None:
        """Test N type renders as mathbb{N}."""
        node = Identifier(line=1, column=1, name="N")
        result = generator.generate_expr(node)
        assert result == r"\mathbb{N}"

    def test_type_identifier_int(self, generator: KaTeXGenerator) -> None:
        """Test Z type renders as mathbb{Z}."""
        node = Identifier(line=1, column=1, name="Z")
        result = generator.generate_expr(node)
        assert result == r"\mathbb{Z}"

    def test_underscore_identifier(self, generator: KaTeXGenerator) -> None:
        """Test identifier with underscore."""
        node = Identifier(line=1, column=1, name="total_count")
        result = generator.generate_expr(node)
        assert r"\mathit{" in result
        assert r"\_" in result


class TestKaTeXGeneratorOperators:
    """Test operator rendering."""

    def test_binary_land(self, generator: KaTeXGenerator) -> None:
        """Test logical AND."""
        node = BinaryOp(
            line=1,
            column=1,
            operator="land",
            left=Identifier(line=1, column=1, name="p"),
            right=Identifier(line=1, column=5, name="q"),
        )
        result = generator.generate_expr(node)
        assert r"\land" in result
        assert "p" in result
        assert "q" in result

    def test_binary_lor(self, generator: KaTeXGenerator) -> None:
        """Test logical OR."""
        node = BinaryOp(
            line=1,
            column=1,
            operator="lor",
            left=Identifier(line=1, column=1, name="p"),
            right=Identifier(line=1, column=5, name="q"),
        )
        result = generator.generate_expr(node)
        assert r"\lor" in result

    def test_binary_implies(self, generator: KaTeXGenerator) -> None:
        """Test implication."""
        node = BinaryOp(
            line=1,
            column=1,
            operator="=>",
            left=Identifier(line=1, column=1, name="p"),
            right=Identifier(line=1, column=5, name="q"),
        )
        result = generator.generate_expr(node)
        assert r"\Rightarrow" in result

    def test_binary_iff(self, generator: KaTeXGenerator) -> None:
        """Test biconditional."""
        node = BinaryOp(
            line=1,
            column=1,
            operator="<=>",
            left=Identifier(line=1, column=1, name="p"),
            right=Identifier(line=1, column=5, name="q"),
        )
        result = generator.generate_expr(node)
        assert r"\Leftrightarrow" in result

    def test_unary_lnot(self, generator: KaTeXGenerator) -> None:
        """Test logical NOT."""
        node = UnaryOp(
            line=1,
            column=1,
            operator="lnot",
            operand=Identifier(line=1, column=5, name="p"),
        )
        result = generator.generate_expr(node)
        assert r"\lnot" in result

    def test_elem_operator(self, generator: KaTeXGenerator) -> None:
        """Test set membership."""
        node = BinaryOp(
            line=1,
            column=1,
            operator="elem",
            left=Identifier(line=1, column=1, name="x"),
            right=Identifier(line=1, column=5, name="S"),
        )
        result = generator.generate_expr(node)
        assert r"\in" in result

    def test_mapsto_operator(self, generator: KaTeXGenerator) -> None:
        """Test maplet operator."""
        node = BinaryOp(
            line=1,
            column=1,
            operator="|->",
            left=Number(line=1, column=1, value="1"),
            right=Identifier(line=1, column=5, name="a"),
        )
        result = generator.generate_expr(node)
        assert r"\mapsto" in result


class TestKaTeXGeneratorQuantifiers:
    """Test quantifier rendering."""

    def test_forall(self, generator: KaTeXGenerator) -> None:
        """Test universal quantifier."""
        node = Quantifier(
            line=1,
            column=1,
            quantifier="forall",
            variables=["x"],
            domain=Identifier(line=1, column=10, name="N"),
            body=BinaryOp(
                line=1,
                column=15,
                operator=">",
                left=Identifier(line=1, column=15, name="x"),
                right=Number(line=1, column=19, value="0"),
            ),
        )
        result = generator.generate_expr(node)
        assert r"\forall" in result
        assert r"\bullet" in result

    def test_exists(self, generator: KaTeXGenerator) -> None:
        """Test existential quantifier."""
        node = Quantifier(
            line=1,
            column=1,
            quantifier="exists",
            variables=["x"],
            domain=Identifier(line=1, column=10, name="N"),
            body=BinaryOp(
                line=1,
                column=15,
                operator="=",
                left=Identifier(line=1, column=15, name="x"),
                right=Number(line=1, column=19, value="1"),
            ),
        )
        result = generator.generate_expr(node)
        assert r"\exists" in result


class TestKaTeXGeneratorSets:
    """Test set notation rendering."""

    def test_empty_set(self, generator: KaTeXGenerator) -> None:
        """Test empty set literal."""
        node = SetLiteral(line=1, column=1, elements=[])
        result = generator.generate_expr(node)
        assert r"\emptyset" in result

    def test_set_literal(self, generator: KaTeXGenerator) -> None:
        """Test set literal with elements."""
        node = SetLiteral(
            line=1,
            column=1,
            elements=[
                Number(line=1, column=2, value="1"),
                Number(line=1, column=5, value="2"),
                Number(line=1, column=8, value="3"),
            ],
        )
        result = generator.generate_expr(node)
        assert r"\{" in result
        assert r"\}" in result
        assert "1" in result
        assert "2" in result
        assert "3" in result

    def test_set_comprehension(self, generator: KaTeXGenerator) -> None:
        """Test set comprehension."""
        node = SetComprehension(
            line=1,
            column=1,
            variables=["x"],
            domain=Identifier(line=1, column=5, name="N"),
            predicate=BinaryOp(
                line=1,
                column=10,
                operator=">",
                left=Identifier(line=1, column=10, name="x"),
                right=Number(line=1, column=14, value="0"),
            ),
            expression=None,
        )
        result = generator.generate_expr(node)
        assert r"\{" in result
        assert r"\mid" in result
        assert r"\}" in result


class TestKaTeXGeneratorSequences:
    """Test sequence notation rendering."""

    def test_empty_sequence(self, generator: KaTeXGenerator) -> None:
        """Test empty sequence."""
        node = SequenceLiteral(line=1, column=1, elements=[])
        result = generator.generate_expr(node)
        assert r"\langle" in result
        assert r"\rangle" in result

    def test_sequence_literal(self, generator: KaTeXGenerator) -> None:
        """Test sequence with elements."""
        node = SequenceLiteral(
            line=1,
            column=1,
            elements=[
                Identifier(line=1, column=2, name="a"),
                Identifier(line=1, column=5, name="b"),
            ],
        )
        result = generator.generate_expr(node)
        assert r"\langle" in result
        assert r"\rangle" in result
        assert "a" in result
        assert "b" in result


class TestKaTeXGeneratorFunctions:
    """Test function notation rendering."""

    def test_function_application(self, generator: KaTeXGenerator) -> None:
        """Test function application."""
        node = FunctionApp(
            line=1,
            column=1,
            function=Identifier(line=1, column=1, name="f"),
            args=[Identifier(line=1, column=3, name="x")],
        )
        result = generator.generate_expr(node)
        assert "f" in result
        assert "x" in result
        assert "(" in result
        assert ")" in result

    def test_function_type(self, generator: KaTeXGenerator) -> None:
        """Test function type arrow."""
        node = FunctionType(
            line=1,
            column=1,
            arrow="->",
            domain=Identifier(line=1, column=1, name="X"),
            range=Identifier(line=1, column=6, name="Y"),
        )
        result = generator.generate_expr(node)
        assert r"\rightarrow" in result

    def test_lambda_expression(self, generator: KaTeXGenerator) -> None:
        """Test lambda expression."""
        node = Lambda(
            line=1,
            column=1,
            variables=["x"],
            domain=Identifier(line=1, column=10, name="N"),
            body=Identifier(line=1, column=15, name="x"),
        )
        result = generator.generate_expr(node)
        assert r"\lambda" in result


class TestKaTeXGeneratorSubscriptsSuperscripts:
    """Test subscript and superscript rendering."""

    def test_subscript(self, generator: KaTeXGenerator) -> None:
        """Test subscript."""
        node = Subscript(
            line=1,
            column=1,
            base=Identifier(line=1, column=1, name="x"),
            index=Number(line=1, column=3, value="1"),
        )
        result = generator.generate_expr(node)
        assert "x" in result
        assert "_{" in result
        assert "1" in result

    def test_superscript(self, generator: KaTeXGenerator) -> None:
        """Test superscript."""
        node = Superscript(
            line=1,
            column=1,
            base=Identifier(line=1, column=1, name="x"),
            exponent=Number(line=1, column=3, value="2"),
        )
        result = generator.generate_expr(node)
        assert "x" in result
        assert "^{" in result
        assert "2" in result


class TestKaTeXGeneratorTuples:
    """Test tuple rendering."""

    def test_tuple(self, generator: KaTeXGenerator) -> None:
        """Test tuple expression."""
        node = Tuple(
            line=1,
            column=1,
            elements=[
                Identifier(line=1, column=2, name="a"),
                Identifier(line=1, column=5, name="b"),
            ],
        )
        result = generator.generate_expr(node)
        assert "(" in result
        assert "a" in result
        assert "b" in result
        assert ")" in result


class TestKaTeXGeneratorZEnvironments:
    """Test Z notation environment rendering."""

    def test_schema_basic(self, generator: KaTeXGenerator) -> None:
        """Test basic schema rendering."""
        schema = Schema(
            line=1,
            column=1,
            name="State",
            declarations=[
                Declaration(
                    line=2,
                    column=3,
                    variable="count",
                    type_expr=Identifier(line=2, column=10, name="N"),
                )
            ],
            predicates=[
                [
                    BinaryOp(
                        line=4,
                        column=3,
                        operator=">=",
                        left=Identifier(line=4, column=3, name="count"),
                        right=Number(line=4, column=12, value="0"),
                    )
                ]
            ],
        )
        result = generator._generate_schema(schema)
        assert any("z-schema" in line for line in result)
        assert any("z-header" in line for line in result)
        assert any("State" in line for line in result)

    def test_axdef(self, generator: KaTeXGenerator) -> None:
        """Test axiomatic definition rendering."""
        axdef = AxDef(
            line=1,
            column=1,
            declarations=[
                Declaration(
                    line=2,
                    column=3,
                    variable="max",
                    type_expr=FunctionType(
                        line=2,
                        column=9,
                        arrow="->",
                        domain=Identifier(line=2, column=9, name="N"),
                        range=Identifier(line=2, column=14, name="N"),
                    ),
                )
            ],
            predicates=[],
        )
        result = generator._generate_axdef(axdef)
        assert any("z-axdef" in line for line in result)

    def test_gendef(self, generator: KaTeXGenerator) -> None:
        """Test generic definition rendering."""
        gendef = GenDef(
            line=1,
            column=1,
            generic_params=["X"],
            declarations=[
                Declaration(
                    line=2,
                    column=3,
                    variable="id",
                    type_expr=FunctionType(
                        line=2,
                        column=8,
                        arrow="->",
                        domain=Identifier(line=2, column=8, name="X"),
                        range=Identifier(line=2, column=13, name="X"),
                    ),
                )
            ],
            predicates=[],
        )
        result = generator._generate_gendef(gendef)
        assert any("z-gendef" in line for line in result)
        assert any("[X]" in line for line in result)

    def test_given_type(self, generator: KaTeXGenerator) -> None:
        """Test given type declaration."""
        given = GivenType(line=1, column=1, names=["PERSON", "DATE"])
        result = generator._generate_given_type(given)
        assert any("PERSON" in line for line in result)
        assert any("DATE" in line for line in result)

    def test_free_type(self, generator: KaTeXGenerator) -> None:
        """Test free type definition."""
        ftype = FreeType(
            line=1,
            column=1,
            name="Status",
            branches=[
                FreeBranch(line=1, column=12, name="active", parameters=None),
                FreeBranch(line=1, column=21, name="inactive", parameters=None),
            ],
        )
        result = generator._generate_free_type(ftype)
        assert any("Status" in line for line in result)
        assert any("active" in line for line in result)
        assert any(r"\mid" in line for line in result)

    def test_abbreviation(self, generator: KaTeXGenerator) -> None:
        """Test abbreviation definition."""
        abbrev = Abbreviation(
            line=1,
            column=1,
            name="Pair",
            expression=BinaryOp(
                line=1,
                column=10,
                operator="cross",
                left=Identifier(line=1, column=10, name="N"),
                right=Identifier(line=1, column=14, name="N"),
            ),
        )
        result = generator._generate_abbreviation(abbrev)
        assert any("Pair" in line for line in result)
        assert any("==" in line for line in result)


class TestKaTeXGeneratorDocumentStructure:
    """Test document structure rendering."""

    def test_section(self, generator: KaTeXGenerator) -> None:
        """Test section rendering."""
        section = Section(
            line=1,
            column=1,
            title="Introduction",
            items=[
                Paragraph(line=2, column=1, text="This is a test paragraph."),
            ],
        )
        result = generator._generate_section(section)
        assert any("section" in line for line in result)
        assert any("<h2>" in line for line in result)
        assert any("Introduction" in line for line in result)

    def test_solution(self, generator: KaTeXGenerator) -> None:
        """Test solution block rendering."""
        solution = Solution(
            line=1,
            column=1,
            number="1",
            items=[],
        )
        result = generator._generate_solution(solution)
        assert any("solution" in line for line in result)
        assert any("Solution 1" in line for line in result)

    def test_part(self, generator: KaTeXGenerator) -> None:
        """Test part label rendering."""
        part = Part(
            line=1,
            column=1,
            label="a",
            items=[],
        )
        result = generator._generate_part(part)
        assert any("part" in line for line in result)
        assert any("(a)" in line for line in result)

    def test_truth_table(self, generator: KaTeXGenerator) -> None:
        """Test truth table rendering."""
        table = TruthTable(
            line=1,
            column=1,
            headers=["p", "q", "p land q"],
            rows=[
                ["T", "T", "T"],
                ["T", "F", "F"],
                ["F", "T", "F"],
                ["F", "F", "F"],
            ],
        )
        result = generator._generate_truth_table(table)
        assert any("truth-table" in line for line in result)
        assert any("<table" in line for line in result)
        assert any("<th>" in line for line in result)

    def test_argue_chain(self, generator: KaTeXGenerator) -> None:
        """Test equivalence chain rendering."""
        chain = ArgueChain(
            line=1,
            column=1,
            steps=[
                ArgueStep(
                    line=1,
                    column=1,
                    expression=BinaryOp(
                        line=1,
                        column=1,
                        operator="land",
                        left=Identifier(line=1, column=1, name="p"),
                        right=Identifier(line=1, column=5, name="q"),
                    ),
                    justification=None,
                ),
                ArgueStep(
                    line=2,
                    column=1,
                    expression=BinaryOp(
                        line=2,
                        column=1,
                        operator="land",
                        left=Identifier(line=2, column=1, name="q"),
                        right=Identifier(line=2, column=5, name="p"),
                    ),
                    justification="commutative",
                ),
            ],
        )
        result = generator._generate_argue_chain(chain)
        assert any("argue-chain" in line for line in result)
        assert any("commutative" in line for line in result)


class TestKaTeXGeneratorProofTrees:
    """Test proof tree rendering."""

    def test_simple_proof(self, generator: KaTeXGenerator) -> None:
        """Test simple proof tree rendering."""
        proof = ProofTree(
            line=1,
            column=1,
            conclusion=ProofNode(
                line=1,
                column=3,
                expression=Identifier(line=1, column=3, name="p"),
                justification="assumption",
                label=1,
                is_assumption=True,
                is_sibling=False,
                children=[],
                indent_level=0,
            ),
        )
        result = generator._generate_proof_tree(proof)
        assert any("proof-tree" in line for line in result)


class TestKaTeXGeneratorFullDocument:
    """Test full document generation."""

    def test_generate_minimal_document(self, generator: KaTeXGenerator) -> None:
        """Test generating a minimal HTML document."""
        doc = Document(
            line=1,
            column=1,
            items=[
                BinaryOp(
                    line=1,
                    column=1,
                    operator="=",
                    left=Identifier(line=1, column=1, name="x"),
                    right=Number(line=1, column=5, value="1"),
                )
            ],
        )
        result = generator.generate_document(doc)

        # Check HTML structure
        assert "<!DOCTYPE html>" in result
        assert "<html" in result
        assert "</html>" in result
        assert "<head>" in result
        assert "</head>" in result
        assert "<body>" in result
        assert "</body>" in result

        # Check KaTeX includes
        assert "katex" in result.lower()
        assert "cdn.jsdelivr.net" in result

        # Check math content
        assert "x = 1" in result or "x=1" in result

    def test_document_with_schema(self, generator: KaTeXGenerator) -> None:
        """Test document containing a schema."""
        doc = Document(
            line=1,
            column=1,
            items=[
                Schema(
                    line=1,
                    column=1,
                    name="State",
                    declarations=[
                        Declaration(
                            line=2,
                            column=3,
                            variable="n",
                            type_expr=Identifier(line=2, column=7, name="N"),
                        )
                    ],
                    predicates=[],
                )
            ],
        )
        result = generator.generate_document(doc)
        assert "z-schema" in result
        assert "State" in result

    def test_katex_macros_included(self, generator: KaTeXGenerator) -> None:
        """Test that KaTeX macros are included in output."""
        doc = Document(line=1, column=1, items=[])
        result = generator.generate_document(doc)

        # Check for macro definitions
        assert "macros" in result
        assert r"\\nat" in result or r"\nat" in result
        assert r"\\num" in result or r"\num" in result

    def test_css_styles_included(self, generator: KaTeXGenerator) -> None:
        """Test that CSS styles are included in output."""
        doc = Document(line=1, column=1, items=[])
        result = generator.generate_document(doc)

        # Check for style definitions
        assert "<style>" in result
        assert "z-schema" in result
        assert "z-axdef" in result


class TestCLIHtmlOutput:
    """Test CLI --html flag."""

    @pytest.fixture
    def temp_input_file(self, tmp_path: Path) -> Path:
        """Create a temporary input file."""
        input_file = tmp_path / "test.txt"
        input_file.write_text("x = 1")
        return input_file

    def test_html_output_generated(self, temp_input_file: Path) -> None:
        """Test that --html generates HTML file."""
        output_file = temp_input_file.with_suffix(".html")
        with patch.object(sys, "argv", ["txt2tex", str(temp_input_file), "--html"]):
            result = main()
        assert result == 0
        assert output_file.exists()
        content = output_file.read_text()
        assert "<!DOCTYPE html>" in content
        assert "katex" in content.lower()

    def test_html_custom_output(self, temp_input_file: Path, tmp_path: Path) -> None:
        """Test --html with custom output path."""
        output_file = tmp_path / "custom.html"
        with patch.object(
            sys,
            "argv",
            ["txt2tex", str(temp_input_file), "--html", "-o", str(output_file)],
        ):
            result = main()
        assert result == 0
        assert output_file.exists()

    def test_validate_requires_html(self, temp_input_file: Path) -> None:
        """Test that --validate requires --html."""
        with patch.object(sys, "argv", ["txt2tex", str(temp_input_file), "--validate"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            # argparse exits with code 2 for errors
            assert exc_info.value.code == 2

    def test_html_with_schema(self, tmp_path: Path) -> None:
        """Test HTML generation with schema content."""
        input_file = tmp_path / "schema.txt"
        input_file.write_text("schema State\n  n : N\nend\n")
        output_file = input_file.with_suffix(".html")

        with patch.object(sys, "argv", ["txt2tex", str(input_file), "--html"]):
            result = main()

        assert result == 0
        assert output_file.exists()
        content = output_file.read_text()
        assert "z-schema" in content
        assert "State" in content


class TestKaTeXGeneratorEdgeCases:
    """Test edge cases in KaTeX generation."""

    def test_unknown_expression_type(self, generator: KaTeXGenerator) -> None:
        """Test that unknown expression types raise TypeError."""

        class UnknownExpr:
            pass

        with pytest.raises(TypeError, match="Unknown expression type"):
            generator.generate_expr(UnknownExpr())

    def test_html_escaping(self, generator: KaTeXGenerator) -> None:
        """Test that HTML special characters are escaped."""
        para = Paragraph(line=1, column=1, text="x < y & a > b")
        result = generator._generate_paragraph(para)
        # HTML entities should be escaped
        assert "&lt;" in result[0] or "<" not in result[0].replace("<p>", "").replace(
            "</p>", ""
        )

    def test_empty_document(self, generator: KaTeXGenerator) -> None:
        """Test empty document generation."""
        doc = Document(line=1, column=1, items=[])
        result = generator.generate_document(doc)
        assert "<!DOCTYPE html>" in result
        assert "</html>" in result


class TestKaTeXIntegration:
    """Integration tests using parser and generator together."""

    def test_parse_and_generate_expression(self) -> None:
        """Test parsing text and generating KaTeX."""
        text = "forall x : N | x >= 0"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        generator = KaTeXGenerator()
        result = generator.generate_document(ast)

        assert r"\forall" in result
        assert r"\mathbb{N}" in result

    def test_parse_and_generate_schema(self) -> None:
        """Test parsing schema and generating KaTeX."""
        text = "schema Counter\n  count : N\nwhere\n  count >= 0\nend\n"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        generator = KaTeXGenerator()
        result = generator.generate_document(ast)

        assert "z-schema" in result
        assert "Counter" in result
        assert r"\mathbb{N}" in result or "mathbb" in result
