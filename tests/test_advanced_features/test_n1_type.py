"""Test N1 (positive integers) type recognition."""

from txt2tex.ast_nodes import Expr, Quantifier, SetComprehension
from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser


def test_n1_in_quantifier_fuzz():
    """Test N1 renders as \nat_1 in fuzz mode."""
    code = "forall x : N1 | x > 0"
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()

    assert isinstance(ast, Quantifier)
    gen = LaTeXGenerator(use_fuzz=True)
    latex = gen.generate_expr(ast)

    assert r"\nat_1" in latex
    assert "forall x" in latex or r"\forall x" in latex


def test_n1_in_quantifier_standard():
    r"""Test N1 renders as \mathbb{N}_1 in standard LaTeX."""
    code = "forall x : N1 | x > 0"
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()

    assert isinstance(ast, Quantifier)
    gen = LaTeXGenerator(use_fuzz=False)
    latex = gen.generate_expr(ast)

    assert r"\mathbb{N}_1" in latex
    assert r"\forall x" in latex


def test_n1_in_set_comprehension_fuzz():
    """Test N1 in set comprehension with fuzz mode."""
    code = "{ x : N1 | x < 10 }"
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()

    assert isinstance(ast, SetComprehension)
    gen = LaTeXGenerator(use_fuzz=True)
    latex = gen.generate_expr(ast)

    assert r"\nat_1" in latex


def test_n1_in_set_comprehension_standard():
    """Test N1 in set comprehension with standard LaTeX."""
    code = "{ x : N1 | x < 10 }"
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()

    assert isinstance(ast, SetComprehension)
    gen = LaTeXGenerator(use_fuzz=False)
    latex = gen.generate_expr(ast)

    assert r"\mathbb{N}_1" in latex


def test_n1_with_n_and_z():
    """Test N1 alongside N and Z to ensure no conflicts."""
    code = "forall x : N | forall y : N1 | forall z : Z | x >= 0 and y >= 1"
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()

    assert isinstance(ast, Expr)
    gen = LaTeXGenerator(use_fuzz=True)
    latex = gen.generate_expr(ast)

    # All three should be present
    assert r"\nat" in latex  # N → \nat
    assert r"\nat_1" in latex  # N1 → \nat_1
    assert r"\num" in latex  # Z → \num


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

    # N1 should render as \nat_1
    assert r"\nat_1" in latex1
    # N_1 should render as N_1 (identifier with subscript)
    assert "N_1" in latex2
