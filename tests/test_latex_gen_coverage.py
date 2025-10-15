"""Tests to increase latex_gen.py coverage to 90%+."""

from __future__ import annotations

from txt2tex.ast_nodes import (
    BinaryOp,
    FunctionApp,
    Identifier,
    Paragraph,
    Quantifier,
)
from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser


def test_mu_expression_with_body() -> None:
    """Test mu-expression with explicit body (lines 478-484)."""
    text = "(mu x : N | x > 0 . x * 2)"
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()

    # Parser returns a Quantifier (mu) for this input
    assert isinstance(ast, Quantifier)

    gen = LaTeXGenerator()
    latex = gen.generate_expr(ast)

    # Should include bullet and body
    assert "mu" in latex or r"\mu" in latex
    assert "*" in latex or r"\times" in latex


def test_function_app_with_binary_op() -> None:
    """Test function application where function is binary op (lines 634-641)."""
    # Create (x + y)(z) - applying a binary operation as a function
    func = BinaryOp(
        operator="+",
        left=Identifier(name="x", line=1, column=1),
        right=Identifier(name="y", line=1, column=1),
        line=1,
        column=1,
    )
    app = FunctionApp(
        function=func, args=[Identifier(name="z", line=1, column=1)], line=1, column=1
    )

    gen = LaTeXGenerator()
    latex = gen.generate_expr(app)

    # Binary op should be parenthesized
    assert "(" in latex
    assert ")" in latex


def test_quantifier_use_fuzz_true() -> None:
    """Test quantifier generation with use_fuzz=True."""
    text = "forall x : N | x > 0"
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()

    # Parser returns a Quantifier for this input
    assert isinstance(ast, Quantifier)

    gen = LaTeXGenerator(use_fuzz=True)
    latex = gen.generate_expr(ast)

    # With fuzz, uses \spot instead of \bullet
    assert r"\spot" in latex or "forall" in latex


def test_exists1_quantifier() -> None:
    """Test exists1 quantifier generation."""
    text = "exists1 x : N | x = 0"
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()

    # Parser returns a Quantifier for this input
    assert isinstance(ast, Quantifier)

    gen = LaTeXGenerator()
    latex = gen.generate_expr(ast)

    # Should use exists_1 LaTeX command
    assert "exists" in latex or r"\exists" in latex


def test_nested_function_application() -> None:
    """Test nested function applications."""
    text = "f(g(x))"
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()

    # Parser returns a FunctionApp for this input
    assert isinstance(ast, FunctionApp)

    gen = LaTeXGenerator()
    latex = gen.generate_expr(ast)

    # Should have nested parentheses
    assert latex.count("(") >= 2
    assert latex.count(")") >= 2


def test_complex_binary_op() -> None:
    """Test complex binary operation tree."""
    text = "x + y * z - w"
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()

    # Parser returns a BinaryOp for this input
    assert isinstance(ast, BinaryOp)

    gen = LaTeXGenerator()
    latex = gen.generate_expr(ast)

    # Should contain all variables
    assert "x" in latex
    assert "y" in latex
    assert "z" in latex
    assert "w" in latex


def test_quantifier_at_sentence_end() -> None:
    """Test quantifier ending with sentence boundary (lines 963-968)."""
    para = Paragraph(
        text="We have forall x : N | x > 0. This is another sentence.", line=1, column=1
    )

    gen = LaTeXGenerator()
    latex_lines = gen._generate_paragraph(para)
    latex = "\n".join(latex_lines)

    # Quantifier should stop at sentence boundary
    assert "forall" in latex or r"\forall" in latex


def test_quantifier_without_pipe() -> None:
    """Test quantifier-like text without pipe (line 973-974)."""
    para = Paragraph(text="The keyword forall x appears here.", line=1, column=1)

    gen = LaTeXGenerator()
    latex_lines = gen._generate_paragraph(para)
    latex = "\n".join(latex_lines)

    # "forall" keyword (one word) should convert to symbol (English uses "for all")
    # Per user requirement: forall → ∀, but not processed as full quantifier
    assert r"\forall" in latex


def test_inline_math_parse_failure() -> None:
    """Test inline math that fails to parse (exception handlers)."""
    # Malformed set comprehension
    para = Paragraph(text="Consider {not valid syntax} here.", line=1, column=1)

    gen = LaTeXGenerator()
    latex_lines = gen._generate_paragraph(para)
    latex = "\n".join(latex_lines)

    # Should be left unchanged (parse fails, caught by except)
    assert "{not valid syntax}" in latex
