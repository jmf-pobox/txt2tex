"""Tests for Phase 24: Whitespace-sensitive ^ operator.

Tests the disambiguation between concatenation (space before ^) and
exponentiation (no space before ^).

Rules:
- Space before ^ → concatenation (CAT token)
- No space before ^ → exponentiation (CARET token)
- >^< pattern → error (missing required space)
"""

from __future__ import annotations

import pytest

from txt2tex.ast_nodes import BinaryOp, Document, Expr, SequenceLiteral, Superscript
from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer, LexerError
from txt2tex.parser import Parser


def parse_expr(text: str) -> Document | Expr:
    """Helper to parse expression."""
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    return parser.parse()


def generate_latex(text: str) -> str:
    """Helper to generate LaTeX."""
    ast = parse_expr(text)
    assert not isinstance(ast, Document)
    gen = LaTeXGenerator()
    return gen.generate_expr(ast)


class TestConcatenationWithSpace:
    """Test concatenation when space before ^."""

    def test_seq_literal_concat_with_space(self):
        """<x> ^ <y> → concatenation."""
        ast = parse_expr("<x> ^ <y>")
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "^"
        latex = generate_latex("<x> ^ <y>")
        assert "\\langle x \\rangle \\cat \\langle y \\rangle" in latex

    def test_variable_concat_with_space(self):
        """s ^ t → concatenation."""
        ast = parse_expr("s ^ t")
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "^"
        latex = generate_latex("s ^ t")
        assert "s \\cat t" in latex

    def test_function_result_concat(self):
        """reverseSeq(s) ^ <x> → concatenation."""
        ast = parse_expr("reverseSeq(s) ^ <x>")
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "^"
        latex = generate_latex("reverseSeq(s) ^ <x>")
        assert "reverseSeq(s) \\cat \\langle x \\rangle" in latex

    def test_paren_seq_concat(self):
        """(s) ^ t → concatenation."""
        ast = parse_expr("(s) ^ t")
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "^"
        latex = generate_latex("(s) ^ t")
        assert "s \\cat t" in latex

    def test_multiple_concat_chain(self):
        """<a> ^ <b> ^ <c> → left-associative concatenation."""
        ast = parse_expr("<a> ^ <b> ^ <c>")
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "^"
        assert isinstance(ast.left, BinaryOp)
        assert ast.left.operator == "^"
        assert isinstance(ast.right, SequenceLiteral)

    def test_empty_seq_concat(self):
        """<> ^ s → concatenation."""
        latex = generate_latex("<> ^ s")
        assert "\\langle \\rangle \\cat s" in latex

    def test_tab_before_caret(self):
        """Tab counts as whitespace."""
        lexer = Lexer("<x>\t^\t<y>")
        tokens = lexer.tokenize()
        caret_token = next(t for t in tokens if t.value == "^")
        assert caret_token.type.name == "CAT"

    def test_newline_before_caret(self):
        """Newline counts as whitespace."""
        text = "<x>\n^ <y>"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        caret_token = next(t for t in tokens if t.value == "^")
        assert caret_token.type.name == "CAT"


class TestExponentiationNoSpace:
    """Test exponentiation when no space before ^."""

    def test_simple_exponent(self):
        """x^2 → exponentiation."""
        ast = parse_expr("x^2")
        assert isinstance(ast, Superscript)
        latex = generate_latex("x^2")
        assert "x \\bsup" in latex
        assert "cat" not in latex.lower()

    def test_number_exponent(self):
        """4^2 → exponentiation."""
        ast = parse_expr("4^2")
        assert isinstance(ast, Superscript)
        latex = generate_latex("4^2")
        assert "4 \\bsup" in latex

    def test_nested_exponent(self):
        """(x^3)^2 → nested superscript."""
        ast = parse_expr("(x^3)^2")
        assert isinstance(ast, Superscript)
        assert isinstance(ast.base, Superscript)
        latex = generate_latex("(x^3)^2")
        assert "\\bsup" in latex
        assert "cat" not in latex.lower()

    def test_identifier_exponent(self):
        """n^k → exponentiation."""
        ast = parse_expr("n^k")
        assert isinstance(ast, Superscript)
        latex = generate_latex("n^k")
        assert "n \\bsup k \\esup" in latex

    def test_function_result_exponent(self):
        """f(x)^2 → exponentiation."""
        ast = parse_expr("f(x)^2")
        assert isinstance(ast, Superscript)
        latex = generate_latex("f(x)^2")
        assert "f(x) \\bsup" in latex

    def test_multi_char_exponent(self):
        """x^{2n} works with braces."""
        text = "x^abc"
        ast = parse_expr(text)
        assert isinstance(ast, Superscript)

    def test_underscore_then_exponent(self):
        """a_i^2 → subscript then superscript."""
        lexer = Lexer("a_i^2")
        tokens = lexer.tokenize()
        caret_tokens = [t for t in tokens if t.value == "^"]
        assert len(caret_tokens) == 1
        assert caret_tokens[0].type.name == "CARET"


class TestErrorCases:
    """Test error conditions."""

    def test_no_space_seq_concat_errors(self):
        """<x>^<y> → clear error."""
        lexer = Lexer("<x>^<y>")
        with pytest.raises(LexerError) as exc_info:
            lexer.tokenize()
        error_msg = str(exc_info.value).lower()
        assert "space" in error_msg
        assert "> ^ <" in str(exc_info.value)

    def test_no_space_in_middle_of_chain(self):
        """<a> ^ <b>^<c> → error at second ^."""
        lexer = Lexer("<a> ^ <b>^<c>")
        with pytest.raises(LexerError):
            lexer.tokenize()

    def test_error_message_clear(self):
        """Verify error message is helpful."""
        lexer = Lexer("<x>^<y>")
        with pytest.raises(LexerError) as exc_info:
            lexer.tokenize()
        assert ">^<" in str(exc_info.value) or "'>^<'" in str(exc_info.value)


class TestMixedUsage:
    """Test files with both concatenation land exponentiation."""

    def test_concat_and_exponent_same_expr(self):
        """<x^2> ^ <y^3> → sequence of powers, concatenated."""
        ast = parse_expr("<x^2> ^ <y^3>")
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "^"
        assert isinstance(ast.left, SequenceLiteral)
        assert isinstance(ast.right, SequenceLiteral)

    def test_exponent_in_function_arg(self):
        """f(<x> ^ s, n^2) → concat elem arg 1, power elem arg 2."""
        text = "f(<x> ^ s, n^2)"
        latex = generate_latex(text)
        assert "\\cat" in latex
        assert "n \\bsup" in latex


class TestIntegration:
    """Integration tests with full definitions."""

    def test_reverse_seq_full_example(self):
        """User's reverseSeq example - both ^ should be concatenation."""
        text = (
            "gendef [X]\n  reverseSeq : seq X -> seq X\nwhere\n"
            "  reverseSeq <> = <>\n"
            "  forall x : X; s : seq X | reverseSeq (<x> ^ s) = reverseSeq (s) ^ <x>\n"
            "end"
        )
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert latex.count("\\cat") == 2
        assert "\\esup" not in latex
        expected = (
            "reverseSeq(\\langle x \\rangle \\cat s) = "
            "reverseSeq(s) \\cat \\langle x \\rangle"
        )
        assert expected in latex

    def test_count_s_example(self):
        """count_s definition with concatenation."""
        text = (
            "gendef [X]\n  count_s : seq X -> N\nwhere\n"
            "  count_s <> = 0\n"
            "  forall x : X; s : seq X | count_s (<x> ^ s) = 1 + count_s(s)\n"
            "end"
        )
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "\\cat" in latex
        assert "\\mathit{count\\_s}(" in latex or "count_s(" in latex

    def test_mixed_definition_concat_and_power(self):
        """Definition using both operators."""
        text = (
            "gendef [X]\n  f : seq X -> N\nwhere\n"
            "  forall s, t : seq X | f(s ^ t) = f(s)^2 + f(t)^2\nend"
        )
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert "s \\cat t" in latex
        assert "f(s) \\bsup 2 \\esup" in latex
        assert "f(t) \\bsup 2 \\esup" in latex


class TestEdgeCases:
    """Test edge cases land boundary conditions."""

    def test_caret_at_start_of_line(self):
        """^ at start of line (after newline)."""
        text = "\n^ x"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        caret_token = next(t for t in tokens if t.value == "^")
        assert caret_token.type.name == "CAT"

    def test_multiple_spaces_before_caret(self):
        """Multiple spaces should still count as space."""
        text = "<x>   ^ <y>"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        caret_token = next(t for t in tokens if t.value == "^")
        assert caret_token.type.name == "CAT"

    def test_caret_after_closing_paren(self):
        """(expr)^2 should be exponentiation (no space)."""
        ast = parse_expr("(x + 1)^2")
        assert isinstance(ast, Superscript)

    def test_caret_after_closing_bracket(self):
        """f[X]^2 should be exponentiation (no space)."""
        text = "Type[N]^2"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        caret_token = next(t for t in tokens if t.value == "^")
        assert caret_token.type.name == "CARET"
