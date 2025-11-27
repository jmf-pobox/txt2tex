"""Tests for Phase 4: Z Notation Basics."""

from __future__ import annotations

from txt2tex.ast_nodes import (
    Abbreviation,
    AxDef,
    BinaryOp,
    Declaration,
    Document,
    FreeBranch,
    FreeType,
    GivenType,
    Identifier,
    Number,
    Schema,
)
from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser


class TestLexer:
    """Tests for Phase 4 lexer features."""

    def test_given_keyword(self) -> None:
        """Test lexing given keyword."""
        lexer = Lexer("given Person")
        tokens = lexer.tokenize()
        assert tokens[0].type.name == "GIVEN"
        assert tokens[1].type.name == "IDENTIFIER"

    def test_free_type_operator(self) -> None:
        """Test lexing ::= operator."""
        lexer = Lexer("Status ::= active")
        tokens = lexer.tokenize()
        assert tokens[0].type.name == "IDENTIFIER"
        assert tokens[1].type.name == "FREE_TYPE"
        assert tokens[1].value == "::="

    def test_abbrev_operator(self) -> None:
        """Test lexing == operator."""
        lexer = Lexer("adult == age")
        tokens = lexer.tokenize()
        assert tokens[0].type.name == "IDENTIFIER"
        assert tokens[1].type.name == "ABBREV"
        assert tokens[1].value == "=="

    def test_axdef_keyword(self) -> None:
        """Test lexing axdef keyword."""
        lexer = Lexer("axdef")
        tokens = lexer.tokenize()
        assert tokens[0].type.name == "AXDEF"

    def test_schema_keyword(self) -> None:
        """Test lexing schema keyword."""
        lexer = Lexer("schema MySchema")
        tokens = lexer.tokenize()
        assert tokens[0].type.name == "SCHEMA"
        assert tokens[1].type.name == "IDENTIFIER"

    def test_where_keyword(self) -> None:
        """Test lexing where keyword."""
        lexer = Lexer("where")
        tokens = lexer.tokenize()
        assert tokens[0].type.name == "WHERE"

    def test_end_keyword(self) -> None:
        """Test lexing end keyword."""
        lexer = Lexer("end")
        tokens = lexer.tokenize()
        assert tokens[0].type.name == "END"


class TestParser:
    """Tests for Phase 4 parser features."""

    def test_given_type_single(self) -> None:
        """Test parsing given type with single name."""
        lexer = Lexer("given Person")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        # Document with one GivenType item
        assert isinstance(ast, Document)
        assert len(ast.items) == 1
        given = ast.items[0]
        assert isinstance(given, GivenType)
        assert given.names == ["Person"]

    def test_given_type_multiple(self) -> None:
        """Test parsing given type with multiple names."""
        lexer = Lexer("given Person Company")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Document)
        given = ast.items[0]
        assert isinstance(given, GivenType)
        assert given.names == ["Person", "Company"]

    def test_free_type_simple(self) -> None:
        """Test parsing simple free type."""
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

    def test_free_type_multiple_branches(self) -> None:
        """Test parsing free type with multiple branches."""
        lexer = Lexer("Status ::= active | inactive | suspended")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Document)
        free_type = ast.items[0]
        assert isinstance(free_type, FreeType)
        assert free_type.name == "Status"
        assert len(free_type.branches) == 3
        assert free_type.branches[0].name == "active"
        assert free_type.branches[1].name == "inactive"
        assert free_type.branches[2].name == "suspended"

    def test_abbreviation_simple(self) -> None:
        """Test parsing simple abbreviation."""
        lexer = Lexer("adult == x")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Document)
        abbrev = ast.items[0]
        assert isinstance(abbrev, Abbreviation)
        assert abbrev.name == "adult"
        assert isinstance(abbrev.expression, Identifier)

    def test_abbreviation_with_expression(self) -> None:
        """Test parsing abbreviation with complex expression."""
        lexer = Lexer("positive == x > 0")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Document)
        abbrev = ast.items[0]
        assert isinstance(abbrev, Abbreviation)
        assert abbrev.name == "positive"
        assert isinstance(abbrev.expression, BinaryOp)
        assert abbrev.expression.operator == ">"

    def test_axdef_declarations_only(self) -> None:
        """Test parsing axdef with only declarations."""
        text = """axdef
x : N
y : N
end"""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Document)
        axdef = ast.items[0]
        assert isinstance(axdef, AxDef)
        assert len(axdef.declarations) == 2
        assert axdef.declarations[0].variable == "x"
        assert axdef.declarations[1].variable == "y"
        assert len(axdef.predicates) == 0

    def test_axdef_with_predicates(self) -> None:
        """Test parsing axdef with where clause."""
        text = """axdef
population : N
capacity : N
where
population <= capacity
capacity > 0
end"""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Document)
        axdef = ast.items[0]
        assert isinstance(axdef, AxDef)
        assert len(axdef.declarations) == 2
        assert len(axdef.predicates) == 1  # One group
        assert len(axdef.predicates[0]) == 2  # Two predicates in that group

    def test_schema_basic(self) -> None:
        """Test parsing basic schema."""
        text = """schema Library
books : N
members : N
end"""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Document)
        schema = ast.items[0]
        assert isinstance(schema, Schema)
        assert schema.name == "Library"
        assert len(schema.declarations) == 2
        assert schema.declarations[0].variable == "books"
        assert schema.declarations[1].variable == "members"

    def test_schema_with_predicates(self) -> None:
        """Test parsing schema with where clause."""
        text = """schema BankAccount
balance : N
where
balance >= 0
end"""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Document)
        schema = ast.items[0]
        assert isinstance(schema, Schema)
        assert schema.name == "BankAccount"
        assert len(schema.declarations) == 1
        assert len(schema.predicates) == 1


class TestLaTeXGenerator:
    """Tests for Phase 4 LaTeX generator."""

    def test_given_type(self) -> None:
        """Test generating given type."""
        gen = LaTeXGenerator()
        ast = GivenType(names=["Person", "Company"], line=1, column=1)
        latex_lines = gen.generate_document_item(ast)
        latex = "".join(latex_lines)
        assert r"\begin{zed}[Person, Company]\end{zed}" in latex

    def test_free_type(self) -> None:
        """Test generating free type."""
        gen = LaTeXGenerator()
        ast = FreeType(
            name="Status",
            branches=[
                FreeBranch(name="active", parameters=None, line=1, column=10),
                FreeBranch(name="inactive", parameters=None, line=1, column=19),
            ],
            line=1,
            column=1,
        )
        latex_lines = gen.generate_document_item(ast)
        latex = "".join(latex_lines)
        assert "Status ::= active | inactive" in latex

    def test_abbreviation(self) -> None:
        """Test generating abbreviation."""
        gen = LaTeXGenerator()
        ast = Abbreviation(
            name="adult",
            expression=Identifier(name="x", line=1, column=10),
            line=1,
            column=1,
        )
        latex_lines = gen.generate_document_item(ast)
        latex = "".join(latex_lines)
        assert "adult == x" in latex

    def test_axdef_no_predicates(self) -> None:
        """Test generating axdef without predicates."""
        gen = LaTeXGenerator()
        ast = AxDef(
            declarations=[
                Declaration(
                    variable="x",
                    type_expr=Identifier(name="N", line=2, column=5),
                    line=2,
                    column=1,
                )
            ],
            predicates=[],
            line=1,
            column=1,
        )
        latex_lines = gen.generate_document_item(ast)
        latex = "".join(latex_lines)
        assert r"\begin{axdef}" in latex
        assert r"x : \mathbb{N}" in latex
        assert r"\end{axdef}" in latex
        assert r"\where" not in latex

    def test_axdef_with_predicates(self) -> None:
        """Test generating axdef with predicates."""
        gen = LaTeXGenerator()
        ast = AxDef(
            declarations=[
                Declaration(
                    variable="x",
                    type_expr=Identifier(name="N", line=2, column=5),
                    line=2,
                    column=1,
                )
            ],
            predicates=[
                [
                    BinaryOp(
                        operator=">",
                        left=Identifier(name="x", line=4, column=1),
                        right=Number(value="0", line=4, column=5),
                        line=4,
                        column=3,
                    )
                ]
            ],
            line=1,
            column=1,
        )
        latex_lines = gen.generate_document_item(ast)
        latex = "".join(latex_lines)
        assert r"\begin{axdef}" in latex
        assert r"\where" in latex
        assert "x > 0" in latex
        assert r"\end{axdef}" in latex

    def test_schema_basic(self) -> None:
        """Test generating basic schema."""
        gen = LaTeXGenerator()
        ast = Schema(
            name="Library",
            declarations=[
                Declaration(
                    variable="books",
                    type_expr=Identifier(name="N", line=2, column=9),
                    line=2,
                    column=1,
                )
            ],
            predicates=[],
            line=1,
            column=1,
        )
        latex_lines = gen.generate_document_item(ast)
        latex = "".join(latex_lines)
        assert r"\begin{schema}{Library}" in latex
        assert r"books : \mathbb{N}" in latex
        assert r"\end{schema}" in latex

    def test_schema_with_predicates(self) -> None:
        """Test generating schema with predicates."""
        gen = LaTeXGenerator()
        ast = Schema(
            name="BankAccount",
            declarations=[
                Declaration(
                    variable="balance",
                    type_expr=Identifier(name="N", line=2, column=11),
                    line=2,
                    column=1,
                )
            ],
            predicates=[
                [
                    BinaryOp(
                        operator=">=",
                        left=Identifier(name="balance", line=4, column=1),
                        right=Number(value="0", line=4, column=12),
                        line=4,
                        column=9,
                    )
                ]
            ],
            line=1,
            column=1,
        )
        latex_lines = gen.generate_document_item(ast)
        latex = "".join(latex_lines)
        assert r"\begin{schema}{BankAccount}" in latex
        assert r"\where" in latex
        assert r"balance \geq 0" in latex
        assert r"\end{schema}" in latex


class TestIntegration:
    """End-to-end integration tests for Phase 4."""

    def test_complete_given_type(self) -> None:
        """Test complete pipeline for given type."""
        text = "given Person Company"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        doc = gen.generate_document(ast)
        assert r"\begin{zed}[Person, Company]\end{zed}" in doc

    def test_complete_free_type(self) -> None:
        """Test complete pipeline for free type."""
        text = "Status ::= active | inactive"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        doc = gen.generate_document(ast)
        assert "Status ::= active | inactive" in doc

    def test_complete_abbreviation(self) -> None:
        """Test complete pipeline for abbreviation."""
        text = "adult == age >= 18"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        doc = gen.generate_document(ast)
        assert r"adult == age \geq 18" in doc

    def test_complete_axdef(self) -> None:
        """Test complete pipeline for axdef."""
        text = """axdef
population : N
capacity : N
where
population <= capacity
end"""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        doc = gen.generate_document(ast)
        assert r"\begin{axdef}" in doc
        assert r"population : \mathbb{N}" in doc
        assert r"\where" in doc
        assert r"population \leq capacity" in doc
        assert r"\end{axdef}" in doc

    def test_complete_schema(self) -> None:
        """Test complete pipeline for schema."""
        text = """schema Library
books : N
members : N
where
books > 0
members >= 0
end"""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        doc = gen.generate_document(ast)
        assert r"\begin{schema}{Library}" in doc
        assert r"books : \mathbb{N}" in doc
        assert r"members : \mathbb{N}" in doc
        assert r"\where" in doc
        assert "books > 0" in doc
        assert r"members \geq 0" in doc
        assert r"\end{schema}" in doc
