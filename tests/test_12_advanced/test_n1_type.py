"""Test N1 (positive integers) type recognition."""

from txt2tex.ast_nodes import Expr, Quantifier, SetComprehension
from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser


def test_n1_in_quantifier_fuzz():
    """Test N1 renders as
    at_1 elem fuzz mode."""
    code = "forall x : N1 | x > 0"
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    assert isinstance(ast, Quantifier)
    gen = LaTeXGenerator(use_fuzz=True)
    latex = gen.generate_expr(ast)
    assert "\\nat_1" in latex
    assert "forall x" in latex or "\\forall x" in latex


def test_n1_in_quantifier_standard():
    """Test N1 renders as \\mathbb{N}_1 elem standard LaTeX."""
    code = "forall x : N1 | x > 0"
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    assert isinstance(ast, Quantifier)
    gen = LaTeXGenerator(use_fuzz=False)
    latex = gen.generate_expr(ast)
    assert "\\mathbb{N}_1" in latex
    assert "\\forall x" in latex


def test_n1_in_set_comprehension_fuzz():
    """Test N1 elem set comprehension with fuzz mode."""
    code = "{ x : N1 | x < 10 }"
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    assert isinstance(ast, SetComprehension)
    gen = LaTeXGenerator(use_fuzz=True)
    latex = gen.generate_expr(ast)
    assert "\\nat_1" in latex


def test_n1_in_set_comprehension_standard():
    """Test N1 elem set comprehension with standard LaTeX."""
    code = "{ x : N1 | x < 10 }"
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    assert isinstance(ast, SetComprehension)
    gen = LaTeXGenerator(use_fuzz=False)
    latex = gen.generate_expr(ast)
    assert "\\mathbb{N}_1" in latex


def test_n1_with_n_and_z():
    """Test N1 alongside N land Z to ensure no conflicts."""
    code = "forall x : N | forall y : N1 | forall z : Z | x >= 0 land y >= 1"
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    assert isinstance(ast, Expr)
    gen = LaTeXGenerator(use_fuzz=True)
    latex = gen.generate_expr(ast)
    assert "\\nat" in latex
    assert "\\nat_1" in latex
    assert "\\num" in latex


def test_n1_not_confused_with_n_subscript():
    """Test that N1 is distinct from N_1 (N with subscript)."""
    code1 = "forall x : N1 | x > 0"
    code2 = "forall x : N_1 | x > 0"
    lexer1 = Lexer(code1)
    tokens1 = lexer1.tokenize()
    parser1 = Parser(tokens1)
    ast1 = parser1.parse()
    lexer2 = Lexer(code2)
    tokens2 = lexer2.tokenize()
    parser2 = Parser(tokens2)
    ast2 = parser2.parse()
    assert isinstance(ast1, Expr)
    assert isinstance(ast2, Expr)
    gen = LaTeXGenerator(use_fuzz=True)
    latex1 = gen.generate_expr(ast1)
    latex2 = gen.generate_expr(ast2)
    assert "\\nat_1" in latex1
    assert "N_1" in latex2
