"""Test for Phase 12: Parentheses around cross in iseq(X cross Y).

This is critical for fuzz compatibility - without parentheses,
iseq ShowId cross EpisodeId parses as (iseq ShowId) cross EpisodeId,
which is a type error when using ran.
"""

from txt2tex.ast_nodes import BinaryOp, FunctionApp, Identifier
from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser


class TestIseqCrossParentheses:
    """Test that cross products inside iseq get proper parentheses."""

    def test_iseq_cross_parsing(self) -> None:
        """Test that iseq(X cross Y) parses as FunctionApp with BinaryOp arg."""
        text = "iseq(ShowId cross EpisodeId)"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)

        ast = parser.parse()
        assert isinstance(ast, FunctionApp)
        assert isinstance(ast.function, Identifier)
        assert ast.function.name == "iseq"
        assert len(ast.args) == 1
        assert isinstance(ast.args[0], BinaryOp)
        assert ast.args[0].operator == "cross"

    def test_iseq_cross_latex(self) -> None:
        """Test that iseq(X cross Y) generates \\iseq (X \\cross Y) with parens."""
        text = "iseq(ShowId cross EpisodeId)"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)

        ast = parser.parse()
        assert isinstance(ast, FunctionApp)
        gen = LaTeXGenerator(use_fuzz=True)
        result = gen.generate_expr(ast)

        # Must have parentheses around cross for correct precedence
        assert result == r"\iseq (ShowId \cross EpisodeId)"

    def test_seq_union_latex(self) -> None:
        """Test that seq(X union Y) also gets parentheses."""
        text = "seq(X union Y)"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)

        ast = parser.parse()
        assert isinstance(ast, FunctionApp)
        gen = LaTeXGenerator()
        result = gen.generate_expr(ast)

        # Must have parentheses around union
        assert result == r"\seq (X \cup Y)"

    def test_seq_nested_no_extra_parens(self) -> None:
        """Test that seq1 (seq X) doesn't add double parentheses."""
        text = "seq1(seq(X))"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)

        ast = parser.parse()
        assert isinstance(ast, FunctionApp)
        gen = LaTeXGenerator()
        result = gen.generate_expr(ast)

        # Only one set of parentheses needed
        assert result == r"\seq_1 (\seq X)"

    def test_iseq_identifier_no_parens(self) -> None:
        """Test that iseq(X) with simple identifier doesn't add unnecessary parens."""
        text = "iseq(ShowId)"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)

        ast = parser.parse()
        assert isinstance(ast, FunctionApp)
        gen = LaTeXGenerator()
        result = gen.generate_expr(ast)

        # No parentheses needed for simple identifier
        assert result == r"\iseq ShowId"
