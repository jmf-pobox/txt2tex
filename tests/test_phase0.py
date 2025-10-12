"""Tests for Phase 0: Simple propositional logic."""

from __future__ import annotations

import pytest

from txt2tex.ast_nodes import BinaryOp, Identifier, UnaryOp
from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer, LexerError
from txt2tex.parser import Parser, ParserError
from txt2tex.tokens import TokenType


class TestLexer:
    """Tests for lexer."""

    def test_single_identifier(self) -> None:
        """Test lexing single identifier."""
        lexer = Lexer("p")
        tokens = lexer.tokenize()
        assert len(tokens) == 2  # identifier + EOF
        assert tokens[0].type == TokenType.IDENTIFIER
        assert tokens[0].value == "p"
        assert tokens[1].type == TokenType.EOF

    def test_binary_operators(self) -> None:
        """Test lexing binary operators."""
        lexer = Lexer("p and q or r => s <=> t")
        tokens = lexer.tokenize()
        types = [t.type for t in tokens[:-1]]  # Exclude EOF
        assert types == [
            TokenType.IDENTIFIER,
            TokenType.AND,
            TokenType.IDENTIFIER,
            TokenType.OR,
            TokenType.IDENTIFIER,
            TokenType.IMPLIES,
            TokenType.IDENTIFIER,
            TokenType.IFF,
            TokenType.IDENTIFIER,
        ]

    def test_unary_operator(self) -> None:
        """Test lexing unary operator."""
        lexer = Lexer("not p")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.NOT
        assert tokens[1].type == TokenType.IDENTIFIER

    def test_position_tracking(self) -> None:
        """Test line and column tracking."""
        lexer = Lexer("p and q")
        tokens = lexer.tokenize()
        assert tokens[0].line == 1
        assert tokens[0].column == 1
        assert tokens[1].line == 1
        assert tokens[1].column == 3
        assert tokens[2].line == 1
        assert tokens[2].column == 7

    def test_invalid_character(self) -> None:
        """Test error on invalid character."""
        lexer = Lexer("p @ q")
        with pytest.raises(LexerError) as exc_info:
            lexer.tokenize()
        assert "Unexpected character" in str(exc_info.value)

    def test_parentheses(self) -> None:
        """Test lexing parentheses."""
        lexer = Lexer("(p and q)")
        tokens = lexer.tokenize()
        types = [t.type for t in tokens[:-1]]  # Exclude EOF
        assert types == [
            TokenType.LPAREN,
            TokenType.IDENTIFIER,
            TokenType.AND,
            TokenType.IDENTIFIER,
            TokenType.RPAREN,
        ]


class TestParser:
    """Tests for parser."""

    def test_single_identifier(self) -> None:
        """Test parsing single identifier."""
        lexer = Lexer("p")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Identifier)
        assert ast.name == "p"

    def test_binary_op(self) -> None:
        """Test parsing binary operation."""
        lexer = Lexer("p and q")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "and"
        assert isinstance(ast.left, Identifier)
        assert isinstance(ast.right, Identifier)

    def test_precedence_and_or(self) -> None:
        """Test and has higher precedence than or."""
        lexer = Lexer("p or q and r")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        # Should parse as: p or (q and r)
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "or"
        assert isinstance(ast.left, Identifier)
        assert isinstance(ast.right, BinaryOp)
        assert ast.right.operator == "and"

    def test_precedence_implies_or(self) -> None:
        """Test or has higher precedence than implies."""
        lexer = Lexer("p => q or r")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        # Should parse as: p => (q or r)
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "=>"
        assert isinstance(ast.left, Identifier)
        assert isinstance(ast.right, BinaryOp)
        assert ast.right.operator == "or"

    def test_unary_not(self) -> None:
        """Test parsing not operation."""
        lexer = Lexer("not p")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, UnaryOp)
        assert ast.operator == "not"
        assert isinstance(ast.operand, Identifier)

    def test_not_precedence(self) -> None:
        """Test not has higher precedence than binary operators."""
        lexer = Lexer("not p and q")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        # Should parse as: (not p) and q
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "and"
        assert isinstance(ast.left, UnaryOp)
        assert isinstance(ast.right, Identifier)

    def test_unexpected_eof(self) -> None:
        """Test error on unexpected end of input."""
        lexer = Lexer("p and")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        with pytest.raises(ParserError):
            parser.parse()

    def test_simple_parens(self) -> None:
        """Test parsing simple parenthesized expression."""
        lexer = Lexer("(p)")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, Identifier)
        assert ast.name == "p"

    def test_precedence_override_with_parens(self) -> None:
        """Test parentheses override precedence."""
        lexer = Lexer("(p or q) and r")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        # Should parse as: (p or q) and r
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "and"
        assert isinstance(ast.left, BinaryOp)
        assert ast.left.operator == "or"
        assert isinstance(ast.right, Identifier)

    def test_nested_parens(self) -> None:
        """Test parsing nested parentheses."""
        lexer = Lexer("((p and q))")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "and"

    def test_complex_parens(self) -> None:
        """Test parsing complex parenthesized expression."""
        lexer = Lexer("(p => q) and (q => r)")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        # Should parse as: (p => q) and (q => r)
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "and"
        assert isinstance(ast.left, BinaryOp)
        assert ast.left.operator == "=>"
        assert isinstance(ast.right, BinaryOp)
        assert ast.right.operator == "=>"

    def test_unclosed_paren(self) -> None:
        """Test error on unclosed parenthesis."""
        lexer = Lexer("(p and q")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        with pytest.raises(ParserError) as exc_info:
            parser.parse()
        assert "Expected ')'" in str(exc_info.value)


class TestLaTeXGenerator:
    """Tests for LaTeX generator."""

    def test_identifier(self) -> None:
        """Test generating identifier."""
        gen = LaTeXGenerator()
        ast = Identifier(name="p", line=1, column=1)
        latex = gen.generate_expr(ast)
        assert latex == "p"

    def test_binary_and(self) -> None:
        """Test generating and operation."""
        gen = LaTeXGenerator()
        ast = BinaryOp(
            operator="and",
            left=Identifier(name="p", line=1, column=1),
            right=Identifier(name="q", line=1, column=7),
            line=1,
            column=3,
        )
        latex = gen.generate_expr(ast)
        assert latex == r"p \land q"

    def test_binary_or(self) -> None:
        """Test generating or operation."""
        gen = LaTeXGenerator()
        ast = BinaryOp(
            operator="or",
            left=Identifier(name="p", line=1, column=1),
            right=Identifier(name="q", line=1, column=6),
            line=1,
            column=3,
        )
        latex = gen.generate_expr(ast)
        assert latex == r"p \lor q"

    def test_binary_implies(self) -> None:
        """Test generating implies operation."""
        gen = LaTeXGenerator()
        ast = BinaryOp(
            operator="=>",
            left=Identifier(name="p", line=1, column=1),
            right=Identifier(name="q", line=1, column=6),
            line=1,
            column=3,
        )
        latex = gen.generate_expr(ast)
        assert latex == r"p \Rightarrow q"

    def test_binary_iff(self) -> None:
        """Test generating iff operation."""
        gen = LaTeXGenerator()
        ast = BinaryOp(
            operator="<=>",
            left=Identifier(name="p", line=1, column=1),
            right=Identifier(name="q", line=1, column=8),
            line=1,
            column=3,
        )
        latex = gen.generate_expr(ast)
        assert latex == r"p \Leftrightarrow q"

    def test_unary_not(self) -> None:
        """Test generating not operation."""
        gen = LaTeXGenerator()
        ast = UnaryOp(
            operator="not",
            operand=Identifier(name="p", line=1, column=5),
            line=1,
            column=1,
        )
        latex = gen.generate_expr(ast)
        assert latex == r"\lnot p"

    def test_document_zed(self) -> None:
        """Test generating complete document with zed packages."""
        gen = LaTeXGenerator(use_fuzz=False)
        ast = Identifier(name="p", line=1, column=1)
        doc = gen.generate_document(ast)
        assert r"\documentclass{article}" in doc
        assert r"\usepackage{zed-cm}" in doc
        assert r"\usepackage{zed-maths}" in doc
        assert r"\usepackage{amsmath}" in doc
        assert r"\begin{document}" in doc
        assert r"$p$" in doc
        assert r"\end{document}" in doc

    def test_document_fuzz(self) -> None:
        """Test generating complete document with fuzz package."""
        gen = LaTeXGenerator(use_fuzz=True)
        ast = Identifier(name="p", line=1, column=1)
        doc = gen.generate_document(ast)
        assert r"\usepackage{fuzz}" in doc
        assert r"\usepackage{zed-cm}" not in doc


class TestIntegration:
    """End-to-end integration tests."""

    def test_simple_expression(self) -> None:
        """Test complete pipeline for simple expression."""
        text = "p and q => r"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        # Single expression should return Expr, not Document
        assert isinstance(ast, (BinaryOp, UnaryOp, Identifier))
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)
        assert latex == r"p \land q \Rightarrow r"

    def test_complex_expression(self) -> None:
        """Test complete pipeline for complex expression."""
        text = "not p or q <=> p => q"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        # Single expression should return Expr, not Document
        assert isinstance(ast, (BinaryOp, UnaryOp, Identifier))
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)
        assert latex == r"\lnot p \lor q \Leftrightarrow p \Rightarrow q"

    def test_parentheses_precedence_override(self) -> None:
        """Test complete pipeline with parentheses overriding precedence."""
        text = "(p or q) and r"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        # Single expression should return Expr, not Document
        assert isinstance(ast, (BinaryOp, UnaryOp, Identifier))
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)
        # Parentheses must be preserved because 'or' has lower precedence than 'and'
        assert latex == r"(p \lor q) \land r"

    def test_nested_parentheses(self) -> None:
        """Test complete pipeline with nested parentheses."""
        text = "p => (q => r)"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        # Single expression should return Expr, not Document
        assert isinstance(ast, (BinaryOp, UnaryOp, Identifier))
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)
        # Nested implications now have explicit parentheses for clarity
        assert latex == r"p \Rightarrow (q \Rightarrow r)"

    def test_solution3_expression(self) -> None:
        """Test expression from Solution 3 with parentheses."""
        text = "not (p and q) or r"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        # Single expression should return Expr, not Document
        assert isinstance(ast, (BinaryOp, UnaryOp, Identifier))
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)
        # Fixed: Parentheses must be preserved around binary operand of not
        assert latex == r"\lnot (p \land q) \lor r"

    def test_unary_with_binary_operand_and(self) -> None:
        """Test not with and operand requires parentheses."""
        text = "not (p and q)"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, UnaryOp)
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)
        # Parentheses required because 'and' is binary operator
        assert latex == r"\lnot (p \land q)"

    def test_unary_with_binary_operand_or(self) -> None:
        """Test not with or operand requires parentheses."""
        text = "not (p or q)"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, UnaryOp)
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)
        # Parentheses required because 'or' is binary operator
        assert latex == r"\lnot (p \lor q)"

    def test_unary_with_binary_operand_implies(self) -> None:
        """Test not with implies operand requires parentheses."""
        text = "not (p => q)"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, UnaryOp)
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)
        # Parentheses required because '=>' is binary operator
        assert latex == r"\lnot (p \Rightarrow q)"

    def test_unary_with_binary_operand_iff(self) -> None:
        """Test not with iff operand requires parentheses."""
        text = "not (p <=> q)"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, UnaryOp)
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)
        # Parentheses required because '<=>' is binary operator
        assert latex == r"\lnot (p \Leftrightarrow q)"

    def test_unary_with_unary_operand(self) -> None:
        """Test not with not operand does not require parentheses."""
        text = "not not p"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, UnaryOp)
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)
        # No parentheses needed for unary operand
        assert latex == r"\lnot \lnot p"

    def test_unary_with_identifier_operand(self) -> None:
        """Test not with identifier operand does not require parentheses."""
        text = "not p"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, UnaryOp)
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)
        # No parentheses needed for identifier operand
        assert latex == r"\lnot p"

    def test_complex_unary_binary_mix(self) -> None:
        """Test complex expression mixing unary and binary operators."""
        text = "not (p and q) => not (r or s)"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, BinaryOp)
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)
        # Both not operators need parentheses around their binary operands
        assert latex == r"\lnot (p \land q) \Rightarrow \lnot (r \lor s)"
