"""Tests for simple propositional logic operators."""

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
        assert len(tokens) == 2
        assert tokens[0].type == TokenType.IDENTIFIER
        assert tokens[0].value == "p"
        assert tokens[1].type == TokenType.EOF

    def test_binary_operators(self) -> None:
        """Test lexing binary operators."""
        lexer = Lexer("p land q lor r => s <=> t")
        tokens = lexer.tokenize()
        types = [t.type for t in tokens[:-1]]
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
        lexer = Lexer("lnot p")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.NOT
        assert tokens[1].type == TokenType.IDENTIFIER

    def test_position_tracking(self) -> None:
        """Test line land column tracking."""
        lexer = Lexer("p land q")
        tokens = lexer.tokenize()
        assert tokens[0].line == 1
        assert tokens[0].column == 1
        assert tokens[1].line == 1
        assert tokens[1].column == 3
        assert tokens[2].line == 1
        assert tokens[2].column == 8

    def test_invalid_character(self) -> None:
        """Test error on invalid character."""
        lexer = Lexer("p @ q")
        with pytest.raises(LexerError) as exc_info:
            lexer.tokenize()
        assert "Unexpected character" in str(exc_info.value)

    def test_parentheses(self) -> None:
        """Test lexing parentheses."""
        lexer = Lexer("(p land q)")
        tokens = lexer.tokenize()
        types = [t.type for t in tokens[:-1]]
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
        lexer = Lexer("p land q")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "land"
        assert isinstance(ast.left, Identifier)
        assert isinstance(ast.right, Identifier)

    def test_precedence_and_or(self) -> None:
        """Test land has higher precedence than lor."""
        lexer = Lexer("p lor q land r")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "lor"
        assert isinstance(ast.left, Identifier)
        assert isinstance(ast.right, BinaryOp)
        assert ast.right.operator == "land"

    def test_precedence_implies_or(self) -> None:
        """Test lor has higher precedence than implies."""
        lexer = Lexer("p => q lor r")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "=>"
        assert isinstance(ast.left, Identifier)
        assert isinstance(ast.right, BinaryOp)
        assert ast.right.operator == "lor"

    def test_unary_not(self) -> None:
        """Test parsing lnot operation."""
        lexer = Lexer("lnot p")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, UnaryOp)
        assert ast.operator == "lnot"
        assert isinstance(ast.operand, Identifier)

    def test_not_precedence(self) -> None:
        """Test lnot has higher precedence than binary operators."""
        lexer = Lexer("lnot p land q")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "land"
        assert isinstance(ast.left, UnaryOp)
        assert isinstance(ast.right, Identifier)

    def test_unexpected_eof(self) -> None:
        """Test error on unexpected end of input."""
        lexer = Lexer("p land")
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
        lexer = Lexer("(p lor q) land r")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "land"
        assert isinstance(ast.left, BinaryOp)
        assert ast.left.operator == "lor"
        assert isinstance(ast.right, Identifier)

    def test_nested_parens(self) -> None:
        """Test parsing nested parentheses."""
        lexer = Lexer("((p land q))")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "land"

    def test_complex_parens(self) -> None:
        """Test parsing complex parenthesized expression."""
        lexer = Lexer("(p => q) land (q => r)")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "land"
        assert isinstance(ast.left, BinaryOp)
        assert ast.left.operator == "=>"
        assert isinstance(ast.right, BinaryOp)
        assert ast.right.operator == "=>"

    def test_unclosed_paren(self) -> None:
        """Test error on unclosed parenthesis."""
        lexer = Lexer("(p land q")
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
        """Test generating land operation."""
        gen = LaTeXGenerator()
        ast = BinaryOp(
            operator="land",
            left=Identifier(name="p", line=1, column=1),
            right=Identifier(name="q", line=1, column=7),
            line=1,
            column=3,
        )
        latex = gen.generate_expr(ast)
        assert latex == "p \\land q"

    def test_binary_or(self) -> None:
        """Test generating lor operation."""
        gen = LaTeXGenerator()
        ast = BinaryOp(
            operator="lor",
            left=Identifier(name="p", line=1, column=1),
            right=Identifier(name="q", line=1, column=6),
            line=1,
            column=3,
        )
        latex = gen.generate_expr(ast)
        assert latex == "p \\lor q"

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
        assert latex == "p \\Rightarrow q"

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
        assert latex == "p \\Leftrightarrow q"

    def test_unary_not(self) -> None:
        """Test generating lnot operation."""
        gen = LaTeXGenerator()
        ast = UnaryOp(
            operator="lnot",
            operand=Identifier(name="p", line=1, column=5),
            line=1,
            column=1,
        )
        latex = gen.generate_expr(ast)
        assert latex == "\\lnot p"

    def test_document_zed(self) -> None:
        """Test generating complete document with zed packages."""
        gen = LaTeXGenerator(use_fuzz=False)
        ast = Identifier(name="p", line=1, column=1)
        doc = gen.generate_document(ast)
        assert "\\documentclass[a4paper,10pt,fleqn]{article}" in doc
        assert "\\usepackage{zed-cm}" in doc
        assert "\\usepackage{zed-maths}" in doc
        assert "\\usepackage{amssymb}" in doc
        assert "\\begin{document}" in doc
        assert "$p$" in doc
        assert "\\end{document}" in doc

    def test_document_fuzz(self) -> None:
        """Test generating complete document with fuzz package."""
        gen = LaTeXGenerator(use_fuzz=True)
        ast = Identifier(name="p", line=1, column=1)
        doc = gen.generate_document(ast)
        assert "\\usepackage{fuzz}" in doc
        assert "\\usepackage{zed-cm}" not in doc


class TestIntegration:
    """End-to-end integration tests."""

    def test_simple_expression(self) -> None:
        """Test complete pipeline for simple expression."""
        text = "p land q => r"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, (BinaryOp, UnaryOp, Identifier))
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)
        assert latex == "p \\land q \\Rightarrow r"

    def test_complex_expression(self) -> None:
        """Test complete pipeline for complex expression."""
        text = "lnot p lor q <=> p => q"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, (BinaryOp, UnaryOp, Identifier))
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)
        assert latex == "\\lnot p \\lor q \\Leftrightarrow p \\Rightarrow q"

    def test_parentheses_precedence_override(self) -> None:
        """Test complete pipeline with parentheses overriding precedence."""
        text = "(p lor q) land r"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, (BinaryOp, UnaryOp, Identifier))
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)
        assert latex == "(p \\lor q) \\land r"

    def test_nested_parentheses(self) -> None:
        """Test complete pipeline with nested parentheses."""
        text = "p => (q => r)"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, (BinaryOp, UnaryOp, Identifier))
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)
        assert latex == "p \\Rightarrow (q \\Rightarrow r)"

    def test_solution3_expression(self) -> None:
        """Test expression from Solution 3 with parentheses."""
        text = "lnot (p land q) lor r"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, (BinaryOp, UnaryOp, Identifier))
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)
        assert latex == "\\lnot (p \\land q) \\lor r"

    def test_unary_with_binary_operand_and(self) -> None:
        """Test lnot with land operand requires parentheses."""
        text = "lnot (p land q)"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, UnaryOp)
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)
        assert latex == "\\lnot (p \\land q)"

    def test_unary_with_binary_operand_or(self) -> None:
        """Test lnot with lor operand requires parentheses."""
        text = "lnot (p lor q)"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, UnaryOp)
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)
        assert latex == "\\lnot (p \\lor q)"

    def test_unary_with_binary_operand_implies(self) -> None:
        """Test lnot with implies operand requires parentheses."""
        text = "lnot (p => q)"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, UnaryOp)
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)
        assert latex == "\\lnot (p \\Rightarrow q)"

    def test_unary_with_binary_operand_iff(self) -> None:
        """Test lnot with iff operand requires parentheses."""
        text = "lnot (p <=> q)"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, UnaryOp)
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)
        assert latex == "\\lnot (p \\Leftrightarrow q)"

    def test_unary_with_unary_operand(self) -> None:
        """Test lnot with lnot operand does lnot require parentheses."""
        text = "lnot lnot p"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, UnaryOp)
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)
        assert latex == "\\lnot \\lnot p"

    def test_unary_with_identifier_operand(self) -> None:
        """Test lnot with identifier operand does lnot require parentheses."""
        text = "lnot p"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, UnaryOp)
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)
        assert latex == "\\lnot p"

    def test_complex_unary_binary_mix(self) -> None:
        """Test complex expression mixing unary land binary operators."""
        text = "lnot (p land q) => lnot (r lor s)"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, BinaryOp)
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)
        assert latex == "\\lnot (p \\land q) \\Rightarrow \\lnot (r \\lor s)"
