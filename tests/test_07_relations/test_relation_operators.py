"""Tests for Phase 10a: Relation operators - Critical subset."""

from __future__ import annotations

from txt2tex.ast_nodes import BinaryOp, Expr, Identifier, UnaryOp
from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser
from txt2tex.tokens import TokenType


class TestPhase10aLexer:
    """Test lexer for Phase 10a relation operators."""

    def test_relation_operator(self) -> None:
        """Test lexing relation type operator <->."""
        lexer = Lexer("R <-> S")
        tokens = lexer.tokenize()
        types = [t.type for t in tokens[:-1]]
        assert types == [TokenType.IDENTIFIER, TokenType.RELATION, TokenType.IDENTIFIER]
        assert tokens[1].value == "<->"

    def test_maplet_operator(self) -> None:
        """Test lexing maplet operator |->."""
        lexer = Lexer("x |-> y")
        tokens = lexer.tokenize()
        types = [t.type for t in tokens[:-1]]
        assert types == [TokenType.IDENTIFIER, TokenType.MAPLET, TokenType.IDENTIFIER]
        assert tokens[1].value == "|->"

    def test_domain_restriction_operator(self) -> None:
        """Test lexing domain restriction operator <|."""
        lexer = Lexer("S <| R")
        tokens = lexer.tokenize()
        types = [t.type for t in tokens[:-1]]
        assert types == [TokenType.IDENTIFIER, TokenType.DRES, TokenType.IDENTIFIER]
        assert tokens[1].value == "<|"

    def test_range_restriction_operator(self) -> None:
        """Test lexing range restriction operator |>."""
        lexer = Lexer("R |> S")
        tokens = lexer.tokenize()
        types = [t.type for t in tokens[:-1]]
        assert types == [TokenType.IDENTIFIER, TokenType.RRES, TokenType.IDENTIFIER]
        assert tokens[1].value == "|>"

    def test_comp_keyword(self) -> None:
        """Test lexing comp keyword."""
        lexer = Lexer("R comp S")
        tokens = lexer.tokenize()
        types = [t.type for t in tokens[:-1]]
        assert types == [TokenType.IDENTIFIER, TokenType.COMP, TokenType.IDENTIFIER]
        assert tokens[1].value == "comp"

    def test_semicolon_operator(self) -> None:
        """Test lexing semicolon operator ;."""
        lexer = Lexer("R ; S")
        tokens = lexer.tokenize()
        types = [t.type for t in tokens[:-1]]
        assert types == [
            TokenType.IDENTIFIER,
            TokenType.SEMICOLON,
            TokenType.IDENTIFIER,
        ]
        assert tokens[1].value == ";"

    def test_dom_function(self) -> None:
        """Test lexing dom function."""
        lexer = Lexer("dom R")
        tokens = lexer.tokenize()
        types = [t.type for t in tokens[:-1]]
        assert types == [TokenType.DOM, TokenType.IDENTIFIER]
        assert tokens[0].value == "dom"

    def test_ran_function(self) -> None:
        """Test lexing ran function."""
        lexer = Lexer("ran R")
        tokens = lexer.tokenize()
        types = [t.type for t in tokens[:-1]]
        assert types == [TokenType.RAN, TokenType.IDENTIFIER]
        assert tokens[0].value == "ran"

    def test_operator_precedence_no_conflict(self) -> None:
        """Test that multi-character operators don't conflict with single characters."""
        lexer = Lexer("a |-> b")
        tokens = lexer.tokenize()
        types = [t.type for t in tokens[:-1]]
        assert types == [TokenType.IDENTIFIER, TokenType.MAPLET, TokenType.IDENTIFIER]
        lexer = Lexer("a <| b")
        tokens = lexer.tokenize()
        types = [t.type for t in tokens[:-1]]
        assert types == [TokenType.IDENTIFIER, TokenType.DRES, TokenType.IDENTIFIER]
        lexer = Lexer("a |> b")
        tokens = lexer.tokenize()
        types = [t.type for t in tokens[:-1]]
        assert types == [TokenType.IDENTIFIER, TokenType.RRES, TokenType.IDENTIFIER]


class TestPhase10aParser:
    """Test parser for Phase 10a relation operators."""

    def test_parse_relation_operator(self) -> None:
        """Test parsing relation type operator <->."""
        lexer = Lexer("R <-> S")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "<->"
        assert isinstance(ast.left, Identifier)
        assert ast.left.name == "R"
        assert isinstance(ast.right, Identifier)
        assert ast.right.name == "S"

    def test_parse_maplet_operator(self) -> None:
        """Test parsing maplet operator |->."""
        lexer = Lexer("x |-> y")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "|->"
        assert isinstance(ast.left, Identifier)
        assert ast.left.name == "x"
        assert isinstance(ast.right, Identifier)
        assert ast.right.name == "y"

    def test_parse_domain_restriction(self) -> None:
        """Test parsing domain restriction operator <|."""
        lexer = Lexer("S <| R")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "<|"
        assert isinstance(ast.left, Identifier)
        assert ast.left.name == "S"
        assert isinstance(ast.right, Identifier)
        assert ast.right.name == "R"

    def test_parse_range_restriction(self) -> None:
        """Test parsing range restriction operator |>."""
        lexer = Lexer("R |> S")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "|>"
        assert isinstance(ast.left, Identifier)
        assert ast.left.name == "R"
        assert isinstance(ast.right, Identifier)
        assert ast.right.name == "S"

    def test_parse_comp_operator(self) -> None:
        """Test parsing comp operator."""
        lexer = Lexer("R comp S")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "comp"
        assert isinstance(ast.left, Identifier)
        assert ast.left.name == "R"
        assert isinstance(ast.right, Identifier)
        assert ast.right.name == "S"

    def test_parse_circ_operator(self) -> None:
        """Test parsing o9 (circ) composition operator.

        Note: Semicolon (;) is reserved for declaration separators.
        Use o9 for relational composition instead.
        """
        lexer = Lexer("R o9 S")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "o9"
        assert isinstance(ast.left, Identifier)
        assert ast.left.name == "R"
        assert isinstance(ast.right, Identifier)
        assert ast.right.name == "S"

    def test_parse_dom_function(self) -> None:
        """Test parsing dom function."""
        lexer = Lexer("dom R")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, UnaryOp)
        assert ast.operator == "dom"
        assert isinstance(ast.operand, Identifier)
        assert ast.operand.name == "R"

    def test_parse_ran_function(self) -> None:
        """Test parsing ran function."""
        lexer = Lexer("ran R")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, UnaryOp)
        assert ast.operator == "ran"
        assert isinstance(ast.operand, Identifier)
        assert ast.operand.name == "R"

    def test_parse_complex_relation_expression(self) -> None:
        """Test parsing complex expression with relation operators."""
        lexer = Lexer("dom (S <| R)")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, UnaryOp)
        assert ast.operator == "dom"
        assert isinstance(ast.operand, BinaryOp)
        assert ast.operand.operator == "<|"

    def test_parse_chained_relations(self) -> None:
        """Test parsing chained relation operators.

        Note: Using o9 for composition, lnot semicolon.
        """
        lexer = Lexer("R o9 S o9 T")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "o9"
        assert isinstance(ast.left, BinaryOp)
        assert ast.left.operator == "o9"


class TestPhase10aLaTeXGeneration:
    """Test LaTeX generation for Phase 10a relation operators."""

    def test_generate_relation_operator(self) -> None:
        """Test generating LaTeX for relation type operator."""
        gen = LaTeXGenerator()
        ast = BinaryOp(
            operator="<->",
            left=Identifier(name="R", line=1, column=1),
            right=Identifier(name="S", line=1, column=5),
            line=1,
            column=3,
        )
        latex = gen.generate_expr(ast)
        assert latex == "R \\rel S"

    def test_generate_maplet_operator(self) -> None:
        """Test generating LaTeX for maplet operator."""
        gen = LaTeXGenerator()
        ast = BinaryOp(
            operator="|->",
            left=Identifier(name="x", line=1, column=1),
            right=Identifier(name="y", line=1, column=6),
            line=1,
            column=3,
        )
        latex = gen.generate_expr(ast)
        assert latex == "x \\mapsto y"

    def test_generate_domain_restriction(self) -> None:
        """Test generating LaTeX for domain restriction."""
        gen = LaTeXGenerator()
        ast = BinaryOp(
            operator="<|",
            left=Identifier(name="S", line=1, column=1),
            right=Identifier(name="R", line=1, column=5),
            line=1,
            column=3,
        )
        latex = gen.generate_expr(ast)
        assert latex == "S \\dres R"

    def test_generate_range_restriction(self) -> None:
        """Test generating LaTeX for range restriction."""
        gen = LaTeXGenerator()
        ast = BinaryOp(
            operator="|>",
            left=Identifier(name="R", line=1, column=1),
            right=Identifier(name="S", line=1, column=5),
            line=1,
            column=3,
        )
        latex = gen.generate_expr(ast)
        assert latex == "R \\rres S"

    def test_generate_comp_operator(self) -> None:
        """Test generating LaTeX for comp operator."""
        gen = LaTeXGenerator()
        ast = BinaryOp(
            operator="comp",
            left=Identifier(name="R", line=1, column=1),
            right=Identifier(name="S", line=1, column=7),
            line=1,
            column=3,
        )
        latex = gen.generate_expr(ast)
        assert latex == "R \\comp S"

    def test_generate_circ_operator(self) -> None:
        """Test generating LaTeX for o9 (circ) operator.

        Note: Semicolon is reserved for declarations, use o9 for composition.
        """
        gen = LaTeXGenerator()
        ast = BinaryOp(
            operator="o9",
            left=Identifier(name="R", line=1, column=1),
            right=Identifier(name="S", line=1, column=7),
            line=1,
            column=3,
        )
        latex = gen.generate_expr(ast)
        assert latex == "R \\circ S"

    def test_generate_dom_function(self) -> None:
        """Test generating LaTeX for dom function."""
        gen = LaTeXGenerator()
        ast = UnaryOp(
            operator="dom",
            operand=Identifier(name="R", line=1, column=5),
            line=1,
            column=1,
        )
        latex = gen.generate_expr(ast)
        assert latex == "\\dom R"

    def test_generate_ran_function(self) -> None:
        """Test generating LaTeX for ran function."""
        gen = LaTeXGenerator()
        ast = UnaryOp(
            operator="ran",
            operand=Identifier(name="R", line=1, column=5),
            line=1,
            column=1,
        )
        latex = gen.generate_expr(ast)
        assert latex == "\\ran R"


class TestPhase10aIntegration:
    """Integration tests for Phase 10a."""

    def test_end_to_end_relation_operator(self) -> None:
        """Test complete pipeline for relation type operator."""
        text = "R <-> S"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Expr)
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "<->"
        assert latex == "R \\rel S"

    def test_end_to_end_maplet(self) -> None:
        """Test complete pipeline for maplet operator."""
        text = "x |-> y"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Expr)
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "|->"
        assert latex == "x \\mapsto y"

    def test_end_to_end_domain_restriction(self) -> None:
        """Test complete pipeline for domain restriction."""
        text = "S <| R"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Expr)
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "<|"
        assert latex == "S \\dres R"

    def test_end_to_end_range_restriction(self) -> None:
        """Test complete pipeline for range restriction."""
        text = "R |> S"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Expr)
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "|>"
        assert latex == "R \\rres S"

    def test_end_to_end_comp(self) -> None:
        """Test complete pipeline for comp operator."""
        text = "R comp S"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Expr)
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "comp"
        assert latex == "R \\comp S"

    def test_end_to_end_circ(self) -> None:
        """Test complete pipeline for o9 (circ) operator.

        Note: Semicolon is reserved for declarations, use o9 for composition.
        """
        text = "R o9 S"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Expr)
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "o9"
        assert latex == "R \\circ S"

    def test_end_to_end_dom_function(self) -> None:
        """Test complete pipeline for dom function."""
        text = "dom R"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Expr)
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)
        assert isinstance(ast, UnaryOp)
        assert ast.operator == "dom"
        assert latex == "\\dom R"

    def test_end_to_end_ran_function(self) -> None:
        """Test complete pipeline for ran function."""
        text = "ran R"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Expr)
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)
        assert isinstance(ast, UnaryOp)
        assert ast.operator == "ran"
        assert latex == "\\ran R"

    def test_complex_relation_expression(self) -> None:
        """Test complex expression with multiple relation operators."""
        text = "dom ((S <| R) |> T)"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Expr)
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)
        assert isinstance(ast, UnaryOp)
        assert ast.operator == "dom"
        assert latex == "\\dom ((S \\dres R) \\rres T)"

    def test_relation_with_set_operations(self) -> None:
        """Test relation operators have lower precedence than set operations."""
        text = "(x |-> y) elem R"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Expr)
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "elem"
        assert latex == "(x \\mapsto y) \\in R"
