"""Tests for Phase 17: Recursive Free Types with Constructor Parameters."""

from __future__ import annotations

from txt2tex.ast_nodes import (
    BinaryOp,
    Document,
    FreeBranch,
    FreeType,
    Identifier,
)
from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser


class TestRecursiveFreeTypeParsing:
    """Tests for parsing recursive free types with constructor parameters."""

    def test_simple_branch_no_params(self) -> None:
        """Test parsing free type with simple branch (no parameters)."""
        lexer = Lexer("Status ::= active")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Document)
        free_type = ast.items[0]
        assert isinstance(free_type, FreeType)
        assert free_type.name == "Status"
        assert len(free_type.branches) == 1
        assert free_type.branches[0].name == "active"
        assert free_type.branches[0].parameters is None

    def test_single_parameter_constructor(self) -> None:
        """Test parsing constructor with single parameter: leaf⟨N⟩."""
        lexer = Lexer("Tree ::= leaf⟨N⟩")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Document)
        free_type = ast.items[0]
        assert isinstance(free_type, FreeType)
        assert free_type.name == "Tree"
        assert len(free_type.branches) == 1
        branch = free_type.branches[0]
        assert branch.name == "leaf"
        assert branch.parameters is not None
        assert isinstance(branch.parameters, Identifier)
        assert branch.parameters.name == "N"

    def test_multi_parameter_constructor(self) -> None:
        """Test constructor with multiple parameters: branch⟨Tree × Tree⟩."""  # noqa: RUF002
        lexer = Lexer("Tree ::= branch⟨Tree × Tree⟩")  # noqa: RUF001
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Document)
        free_type = ast.items[0]
        assert isinstance(free_type, FreeType)
        assert free_type.name == "Tree"
        assert len(free_type.branches) == 1
        branch = free_type.branches[0]
        assert branch.name == "branch"
        assert branch.parameters is not None
        assert isinstance(branch.parameters, BinaryOp)
        assert branch.parameters.operator == "×"  # noqa: RUF001
        assert isinstance(branch.parameters.left, Identifier)
        assert branch.parameters.left.name == "Tree"
        assert isinstance(branch.parameters.right, Identifier)
        assert branch.parameters.right.name == "Tree"

    def test_mixed_branches(self) -> None:
        """Test free type with mix of simple and parameterized branches."""
        lexer = Lexer("Tree ::= stalk | leaf⟨N⟩ | branch⟨Tree × Tree⟩")  # noqa: RUF001
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Document)
        free_type = ast.items[0]
        assert isinstance(free_type, FreeType)
        assert free_type.name == "Tree"
        assert len(free_type.branches) == 3

        # stalk - simple branch
        assert free_type.branches[0].name == "stalk"
        assert free_type.branches[0].parameters is None

        # leaf⟨N⟩ - single parameter
        assert free_type.branches[1].name == "leaf"
        assert isinstance(free_type.branches[1].parameters, Identifier)

        # branch⟨Tree × Tree⟩ - multiple parameters  # noqa: RUF003
        assert free_type.branches[2].name == "branch"
        assert isinstance(free_type.branches[2].parameters, BinaryOp)

    def test_ascii_angle_brackets(self) -> None:
        """Test ASCII angle brackets < > as alternative to Unicode ⟨ ⟩."""
        lexer = Lexer("Tree ::= leaf<N>")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Document)
        free_type = ast.items[0]
        assert isinstance(free_type, FreeType)
        assert free_type.name == "Tree"
        assert len(free_type.branches) == 1
        branch = free_type.branches[0]
        assert branch.name == "leaf"
        assert isinstance(branch.parameters, Identifier)
        assert branch.parameters.name == "N"

    def test_complex_parameter_type(self) -> None:
        """Test constructor with complex parameter type."""
        lexer = Lexer("List ::= cons⟨N × seq(N)⟩")  # noqa: RUF001
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Document)
        free_type = ast.items[0]
        assert isinstance(free_type, FreeType)
        assert free_type.name == "List"
        assert len(free_type.branches) == 1
        branch = free_type.branches[0]
        assert branch.name == "cons"
        assert branch.parameters is not None


class TestRecursiveFreeTypeLaTeX:
    """Tests for LaTeX generation of recursive free types."""

    def test_simple_branch_latex(self) -> None:
        """Test LaTeX generation for simple branch."""
        gen = LaTeXGenerator()
        ast = FreeType(
            name="Status",
            branches=[FreeBranch(name="active", parameters=None, line=1, column=10)],
            line=1,
            column=1,
        )
        latex_lines = gen.generate_document_item(ast)
        latex = "".join(latex_lines)
        assert "Status ::= active" in latex
        assert r"\begin{zed}" in latex
        assert r"\end{zed}" in latex

    def test_single_parameter_latex(self) -> None:
        """Test LaTeX generation for single parameter constructor."""
        gen = LaTeXGenerator()
        ast = FreeType(
            name="Tree",
            branches=[
                FreeBranch(
                    name="leaf",
                    parameters=Identifier(name="N", line=1, column=15),
                    line=1,
                    column=10,
                )
            ],
            line=1,
            column=1,
        )
        latex_lines = gen.generate_document_item(ast)
        latex = "".join(latex_lines)
        assert "Tree ::= leaf" in latex
        assert r"\ldata" in latex
        assert r"\rdata" in latex
        assert "N" in latex

    def test_multi_parameter_latex(self) -> None:
        """Test LaTeX generation for multi-parameter constructor."""
        gen = LaTeXGenerator()
        params = BinaryOp(
            operator="cross",
            left=Identifier(name="Tree", line=1, column=18),
            right=Identifier(name="Tree", line=1, column=25),
            line=1,
            column=22,
        )
        ast = FreeType(
            name="Tree",
            branches=[FreeBranch(name="branch", parameters=params, line=1, column=10)],
            line=1,
            column=1,
        )
        latex_lines = gen.generate_document_item(ast)
        latex = "".join(latex_lines)
        assert "Tree ::= branch" in latex
        assert r"\ldata" in latex
        assert r"\rdata" in latex
        assert r"\cross" in latex

    def test_mixed_branches_latex(self) -> None:
        """Test LaTeX generation for mixed simple and parameterized branches."""
        gen = LaTeXGenerator()
        ast = FreeType(
            name="Tree",
            branches=[
                FreeBranch(name="stalk", parameters=None, line=1, column=10),
                FreeBranch(
                    name="leaf",
                    parameters=Identifier(name="N", line=1, column=22),
                    line=1,
                    column=17,
                ),
                FreeBranch(
                    name="branch",
                    parameters=BinaryOp(
                        operator="cross",
                        left=Identifier(name="Tree", line=1, column=35),
                        right=Identifier(name="Tree", line=1, column=42),
                        line=1,
                        column=39,
                    ),
                    line=1,
                    column=27,
                ),
            ],
            line=1,
            column=1,
        )
        latex_lines = gen.generate_document_item(ast)
        latex = "".join(latex_lines)
        assert "Tree ::= stalk | leaf" in latex
        assert "| branch" in latex
        assert r"\ldata" in latex
        assert r"\rdata" in latex


class TestRecursiveFreeTypeIntegration:
    """End-to-end integration tests for recursive free types."""

    def test_complete_tree_definition(self) -> None:
        """Test complete Tree free type definition with LaTeX generation."""
        text = "Tree ::= stalk | leaf⟨N⟩ | branch⟨Tree × Tree⟩"  # noqa: RUF001
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        doc = gen.generate_document(ast)

        # Check document structure
        assert r"\documentclass{article}" in doc
        assert r"\begin{document}" in doc
        assert r"\end{document}" in doc

        # Check free type definition
        assert "Tree ::= stalk | leaf" in doc
        assert r"\ldata" in doc
        assert r"\rdata" in doc
        assert r"\cross" in doc

    def test_complete_list_definition(self) -> None:
        """Test List free type with nil and cons constructors."""
        text = "List ::= nil | cons⟨N × List⟩"  # noqa: RUF001
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        doc = gen.generate_document(ast)

        assert "List ::= nil | cons" in doc
        assert r"\ldata" in doc
        assert r"\cross" in doc

    def test_ascii_brackets_integration(self) -> None:
        """Test ASCII angle brackets in full pipeline."""
        text = "Tree ::= leaf<N> | branch<Tree × Tree>"  # noqa: RUF001
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        doc = gen.generate_document(ast)

        assert "Tree ::= leaf" in doc
        assert r"\ldata" in doc
        assert r"\rdata" in doc
        assert "| branch" in doc


class TestRecursiveFreeTypeEdgeCases:
    """Tests for edge cases and error handling."""

    def test_no_branches_error(self) -> None:
        """Test that empty branches list raises an error."""
        lexer = Lexer("Tree ::=")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        try:
            parser.parse()
            raise AssertionError("Expected ParserError for empty branches")
        except Exception as e:
            assert "Expected at least one branch" in str(e)

    def test_unclosed_angle_bracket(self) -> None:
        """Test error handling for unclosed constructor parameters."""
        lexer = Lexer("Tree ::= leaf⟨N")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        try:
            parser.parse()
            raise AssertionError("Expected ParserError for unclosed angle bracket")
        except Exception as e:
            assert "Expected" in str(e)

    def test_empty_parameters(self) -> None:
        """Test constructor with empty parameter list."""
        lexer = Lexer("Tree ::= leaf⟨⟩")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        # This should parse - empty sequence literal as parameter
        ast = parser.parse()
        assert isinstance(ast, Document)


class TestBackwardCompatibility:
    """Tests to ensure backward compatibility with simple free types."""

    def test_simple_free_types_still_work(self) -> None:
        """Test that simple free types from Phase 4 still work."""
        text = "Status ::= active | inactive | suspended"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        doc = gen.generate_document(ast)

        assert "Status ::= active | inactive | suspended" in doc
        # Should not have \ldata or \rdata for simple branches
        assert r"\ldata" not in doc

    def test_phase4_examples_unchanged(self) -> None:
        """Test that Phase 4 example outputs remain the same."""
        text = "Answer ::= yes | no"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        doc = gen.generate_document(ast)

        assert "Answer ::= yes | no" in doc
        assert r"\ldata" not in doc
