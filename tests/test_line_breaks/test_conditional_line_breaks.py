"""Tests for line breaks in conditional expressions (if/then/else)."""

from txt2tex.ast_nodes import Conditional
from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser


class TestConditionalLineBreaks:
    """Tests for backslash continuation in if/then/else."""

    def test_line_break_after_condition(self) -> None:
        """Test line break after condition (before then)."""
        code = "if x > 0 \\\n  then 1 else 0"
        tokens = Lexer(code).tokenize()
        ast = Parser(tokens).parse()

        assert isinstance(ast, Conditional)
        assert ast.line_break_after_condition is True
        assert ast.line_break_after_then is False

    def test_line_break_after_then(self) -> None:
        """Test line break after then (before else)."""
        code = "if x > 0 then 1 \\\n  else 0"
        tokens = Lexer(code).tokenize()
        ast = Parser(tokens).parse()

        assert isinstance(ast, Conditional)
        assert ast.line_break_after_condition is False
        assert ast.line_break_after_then is True

    def test_line_breaks_both(self) -> None:
        """Test line breaks after both condition and then."""
        code = "if x > 0 \\\n  then 1 \\\n  else 0"
        tokens = Lexer(code).tokenize()
        ast = Parser(tokens).parse()

        assert isinstance(ast, Conditional)
        assert ast.line_break_after_condition is True
        assert ast.line_break_after_then is True

    def test_no_line_breaks(self) -> None:
        """Test conditional without line breaks."""
        code = "if x > 0 then 1 else 0"
        tokens = Lexer(code).tokenize()
        ast = Parser(tokens).parse()

        assert isinstance(ast, Conditional)
        assert ast.line_break_after_condition is False
        assert ast.line_break_after_then is False

    def test_latex_generation_with_breaks(self) -> None:
        """Test LaTeX output includes line breaks."""
        code = "if x > 0 \\\n  then 1 \\\n  else 0"
        tokens = Lexer(code).tokenize()
        ast = Parser(tokens).parse()

        gen = LaTeXGenerator(use_fuzz=True)
        latex = gen.generate_expr(ast)

        # Should contain \\ and \t1 for line breaks
        assert "\\\\" in latex
        assert "\\t1" in latex
        assert "\\IF" in latex
        assert "\\THEN" in latex
        assert "\\ELSE" in latex
