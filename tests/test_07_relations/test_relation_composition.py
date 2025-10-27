"""Tests for Phase 10b: Extended relation operators."""

from __future__ import annotations

from txt2tex.ast_nodes import BinaryOp, Expr, Identifier, UnaryOp
from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser
from txt2tex.tokens import TokenType


class TestPhase10bLexer:
    """Test lexer for Phase 10b extended relation operators."""

    def test_domain_subtraction_operator(self) -> None:
        """Test lexing domain subtraction operator <<|."""
        lexer = Lexer("S <<| R")
        tokens = lexer.tokenize()
        types = [t.type for t in tokens[:-1]]  # Exclude EOF
        assert types == [
            TokenType.IDENTIFIER,
            TokenType.NDRES,
            TokenType.IDENTIFIER,
        ]
        assert tokens[1].value == "<<|"

    def test_range_subtraction_operator(self) -> None:
        """Test lexing range subtraction operator |>>."""
        lexer = Lexer("R |>> S")
        tokens = lexer.tokenize()
        types = [t.type for t in tokens[:-1]]  # Exclude EOF
        assert types == [
            TokenType.IDENTIFIER,
            TokenType.NRRES,
            TokenType.IDENTIFIER,
        ]
        assert tokens[1].value == "|>>"

    def test_composition_operator(self) -> None:
        """Test lexing composition operator o9."""
        lexer = Lexer("R o9 S")
        tokens = lexer.tokenize()
        types = [t.type for t in tokens[:-1]]  # Exclude EOF
        assert types == [
            TokenType.IDENTIFIER,
            TokenType.CIRC,
            TokenType.IDENTIFIER,
        ]
        assert tokens[1].value == "o9"

    def test_inv_keyword(self) -> None:
        """Test lexing inv keyword."""
        lexer = Lexer("inv R")
        tokens = lexer.tokenize()
        types = [t.type for t in tokens[:-1]]  # Exclude EOF
        assert types == [TokenType.INV, TokenType.IDENTIFIER]
        assert tokens[0].value == "inv"

    def test_id_keyword(self) -> None:
        """Test lexing id keyword."""
        lexer = Lexer("id X")
        tokens = lexer.tokenize()
        types = [t.type for t in tokens[:-1]]  # Exclude EOF
        assert types == [TokenType.ID, TokenType.IDENTIFIER]
        assert tokens[0].value == "id"

    def test_tilde_postfix_operator(self) -> None:
        """Test lexing tilde postfix operator ~."""
        lexer = Lexer("R~")
        tokens = lexer.tokenize()
        types = [t.type for t in tokens[:-1]]  # Exclude EOF
        assert types == [TokenType.IDENTIFIER, TokenType.TILDE]
        assert tokens[1].value == "~"

    def test_plus_postfix_operator(self) -> None:
        """Test lexing plus postfix operator +."""
        lexer = Lexer("R+")
        tokens = lexer.tokenize()
        types = [t.type for t in tokens[:-1]]  # Exclude EOF
        assert types == [TokenType.IDENTIFIER, TokenType.PLUS]
        assert tokens[1].value == "+"

    def test_star_postfix_operator(self) -> None:
        """Test lexing star postfix operator *."""
        lexer = Lexer("R*")
        tokens = lexer.tokenize()
        types = [t.type for t in tokens[:-1]]  # Exclude EOF
        assert types == [TokenType.IDENTIFIER, TokenType.STAR]
        assert tokens[1].value == "*"

    def test_operator_precedence_no_conflict(self) -> None:
        """Test that 3-char operators don't conflict with 2-char operators."""
        # <<| should be parsed as NDRES, not LESS_THAN followed by DRES
        lexer = Lexer("a <<| b")
        tokens = lexer.tokenize()
        types = [t.type for t in tokens[:-1]]
        assert types == [
            TokenType.IDENTIFIER,
            TokenType.NDRES,
            TokenType.IDENTIFIER,
        ]

        # |>> should be parsed as NRRES, not RRES followed by GREATER_THAN
        lexer = Lexer("a |>> b")
        tokens = lexer.tokenize()
        types = [t.type for t in tokens[:-1]]
        assert types == [
            TokenType.IDENTIFIER,
            TokenType.NRRES,
            TokenType.IDENTIFIER,
        ]


class TestPhase10bParser:
    """Test parser for Phase 10b extended relation operators."""

    def test_parse_domain_subtraction(self) -> None:
        """Test parsing domain subtraction operator <<|."""
        lexer = Lexer("S <<| R")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        assert isinstance(ast, BinaryOp)
        assert ast.operator == "<<|"
        assert isinstance(ast.left, Identifier)
        assert ast.left.name == "S"
        assert isinstance(ast.right, Identifier)
        assert ast.right.name == "R"

    def test_parse_range_subtraction(self) -> None:
        """Test parsing range subtraction operator |>>."""
        lexer = Lexer("R |>> S")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        assert isinstance(ast, BinaryOp)
        assert ast.operator == "|>>"
        assert isinstance(ast.left, Identifier)
        assert ast.left.name == "R"
        assert isinstance(ast.right, Identifier)
        assert ast.right.name == "S"

    def test_parse_composition_operator(self) -> None:
        """Test parsing composition operator o9."""
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

    def test_parse_inv_function(self) -> None:
        """Test parsing inv function."""
        lexer = Lexer("inv R")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        assert isinstance(ast, UnaryOp)
        assert ast.operator == "inv"
        assert isinstance(ast.operand, Identifier)
        assert ast.operand.name == "R"

    def test_parse_id_function(self) -> None:
        """Test parsing id function."""
        lexer = Lexer("id X")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        assert isinstance(ast, UnaryOp)
        assert ast.operator == "id"
        assert isinstance(ast.operand, Identifier)
        assert ast.operand.name == "X"

    def test_parse_tilde_postfix(self) -> None:
        """Test parsing tilde postfix operator ~."""
        lexer = Lexer("R~")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        assert isinstance(ast, UnaryOp)
        assert ast.operator == "~"
        assert isinstance(ast.operand, Identifier)
        assert ast.operand.name == "R"

    def test_parse_plus_postfix(self) -> None:
        """Test parsing plus postfix operator +."""
        lexer = Lexer("R+")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        assert isinstance(ast, UnaryOp)
        assert ast.operator == "+"
        assert isinstance(ast.operand, Identifier)
        assert ast.operand.name == "R"

    def test_parse_star_postfix(self) -> None:
        """Test parsing star postfix operator *."""
        lexer = Lexer("R*")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        assert isinstance(ast, UnaryOp)
        assert ast.operator == "*"
        assert isinstance(ast.operand, Identifier)
        assert ast.operand.name == "R"

    def test_parse_complex_postfix_expression(self) -> None:
        """Test parsing complex expression with postfix operators."""
        lexer = Lexer("(R~)+")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        # Should parse as: (R~)+
        assert isinstance(ast, UnaryOp)
        assert ast.operator == "+"
        assert isinstance(ast.operand, UnaryOp)
        assert ast.operand.operator == "~"

    def test_parse_chained_extended_relations(self) -> None:
        """Test parsing chained extended relation operators."""
        lexer = Lexer("R o9 S o9 T")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        # Should parse as: (R o9 S) o9 T (left-associative)
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "o9"
        assert isinstance(ast.left, BinaryOp)
        assert ast.left.operator == "o9"


class TestPhase10bLaTeXGeneration:
    """Test LaTeX generation for Phase 10b extended relation operators."""

    def test_generate_domain_subtraction(self) -> None:
        """Test generating LaTeX for domain subtraction."""
        gen = LaTeXGenerator()
        ast = BinaryOp(
            operator="<<|",
            left=Identifier(name="S", line=1, column=1),
            right=Identifier(name="R", line=1, column=6),
            line=1,
            column=3,
        )
        latex = gen.generate_expr(ast)
        assert latex == r"S \ndres R"

    def test_generate_range_subtraction(self) -> None:
        """Test generating LaTeX for range subtraction."""
        gen = LaTeXGenerator()
        ast = BinaryOp(
            operator="|>>",
            left=Identifier(name="R", line=1, column=1),
            right=Identifier(name="S", line=1, column=6),
            line=1,
            column=3,
        )
        latex = gen.generate_expr(ast)
        assert latex == r"R \nrres S"

    def test_generate_composition_operator(self) -> None:
        """Test generating LaTeX for composition operator."""
        gen = LaTeXGenerator()
        ast = BinaryOp(
            operator="o9",
            left=Identifier(name="R", line=1, column=1),
            right=Identifier(name="S", line=1, column=5),
            line=1,
            column=3,
        )
        latex = gen.generate_expr(ast)
        assert latex == r"R \circ S"

    def test_generate_inv_function(self) -> None:
        """Test generating LaTeX for inv function."""
        gen = LaTeXGenerator()
        ast = UnaryOp(
            operator="inv",
            operand=Identifier(name="R", line=1, column=5),
            line=1,
            column=1,
        )
        latex = gen.generate_expr(ast)
        assert latex == r"\inv R"

    def test_generate_id_function(self) -> None:
        """Test generating LaTeX for id function."""
        gen = LaTeXGenerator()
        ast = UnaryOp(
            operator="id",
            operand=Identifier(name="X", line=1, column=4),
            line=1,
            column=1,
        )
        latex = gen.generate_expr(ast)
        assert latex == r"\id X"

    def test_generate_tilde_postfix(self) -> None:
        """Test generating LaTeX for tilde postfix operator."""
        gen = LaTeXGenerator()
        ast = UnaryOp(
            operator="~",
            operand=Identifier(name="R", line=1, column=1),
            line=1,
            column=2,
        )
        latex = gen.generate_expr(ast)
        assert latex == r"R^{-1}"

    def test_generate_plus_postfix(self) -> None:
        """Test generating LaTeX for plus postfix operator."""
        gen = LaTeXGenerator()
        ast = UnaryOp(
            operator="+",
            operand=Identifier(name="R", line=1, column=1),
            line=1,
            column=2,
        )
        latex = gen.generate_expr(ast)
        assert latex == r"R^{+}"

    def test_generate_star_postfix(self) -> None:
        """Test generating LaTeX for star postfix operator."""
        gen = LaTeXGenerator()
        ast = UnaryOp(
            operator="*",
            operand=Identifier(name="R", line=1, column=1),
            line=1,
            column=2,
        )
        latex = gen.generate_expr(ast)
        assert latex == r"R^{*}"


class TestPhase10bIntegration:
    """Integration tests for Phase 10b."""

    def test_end_to_end_domain_subtraction(self) -> None:
        """Test complete pipeline for domain subtraction."""
        text = "S <<| R"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Expr)  # Type narrowing for mypy
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)

        assert isinstance(ast, BinaryOp)
        assert ast.operator == "<<|"
        assert latex == r"S \ndres R"

    def test_end_to_end_range_subtraction(self) -> None:
        """Test complete pipeline for range subtraction."""
        text = "R |>> S"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Expr)  # Type narrowing for mypy
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)

        assert isinstance(ast, BinaryOp)
        assert ast.operator == "|>>"
        assert latex == r"R \nrres S"

    def test_end_to_end_composition(self) -> None:
        """Test complete pipeline for composition operator."""
        text = "R o9 S"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Expr)  # Type narrowing for mypy
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)

        assert isinstance(ast, BinaryOp)
        assert ast.operator == "o9"
        assert latex == r"R \circ S"

    def test_end_to_end_inv_function(self) -> None:
        """Test complete pipeline for inv function."""
        text = "inv R"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Expr)  # Type narrowing for mypy
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)

        assert isinstance(ast, UnaryOp)
        assert ast.operator == "inv"
        assert latex == r"\inv R"

    def test_end_to_end_id_function(self) -> None:
        """Test complete pipeline for id function."""
        text = "id X"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Expr)  # Type narrowing for mypy
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)

        assert isinstance(ast, UnaryOp)
        assert ast.operator == "id"
        assert latex == r"\id X"

    def test_end_to_end_tilde_postfix(self) -> None:
        """Test complete pipeline for tilde postfix operator."""
        text = "R~"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Expr)  # Type narrowing for mypy
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)

        assert isinstance(ast, UnaryOp)
        assert ast.operator == "~"
        assert latex == r"R^{-1}"

    def test_end_to_end_plus_postfix(self) -> None:
        """Test complete pipeline for plus postfix operator."""
        text = "R+"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Expr)  # Type narrowing for mypy
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)

        assert isinstance(ast, UnaryOp)
        assert ast.operator == "+"
        assert latex == r"R^{+}"

    def test_end_to_end_star_postfix(self) -> None:
        """Test complete pipeline for star postfix operator."""
        text = "R*"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Expr)  # Type narrowing for mypy
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)

        assert isinstance(ast, UnaryOp)
        assert ast.operator == "*"
        assert latex == r"R^{*}"

    def test_complex_extended_relation_expression(self) -> None:
        """Test complex expression with multiple extended operators."""
        text = "inv (S <<| R~)"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Expr)  # Type narrowing for mypy
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)

        assert isinstance(ast, UnaryOp)
        assert ast.operator == "inv"
        assert latex == r"\inv (S \ndres R^{-1})"

    def test_transitive_closure_of_composition(self) -> None:
        """Test transitive closure applied to composition."""
        text = "(R o9 S)+"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Expr)  # Type narrowing for mypy
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)

        assert isinstance(ast, UnaryOp)
        assert ast.operator == "+"
        assert isinstance(ast.operand, BinaryOp)
        assert latex == r"(R \circ S)^{+}"

    def test_mixed_phase10a_and_10b_operators(self) -> None:
        """Test mixing Phase 10a and 10b operators."""
        text = "(S <| R)~"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Expr)  # Type narrowing for mypy
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)

        # Domain restriction followed by inverse
        assert isinstance(ast, UnaryOp)
        assert ast.operator == "~"
        assert isinstance(ast.operand, BinaryOp)
        assert ast.operand.operator == "<|"
        assert latex == r"(S \dres R)^{-1}"
