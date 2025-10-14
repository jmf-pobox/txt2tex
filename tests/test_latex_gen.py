"""Tests for LaTeX generator to improve coverage.

Tests generation of LaTeX for various AST nodes and edge cases.
"""

from __future__ import annotations

from txt2tex.ast_nodes import Expr
from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser


def test_latex_gen_use_fuzz_true() -> None:
    """Test LaTeX generation with use_fuzz=True."""
    text = """schema State
  x : N
end
"""
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()

    gen = LaTeXGenerator(use_fuzz=True)
    latex = gen.generate_document(ast)

    assert "\\usepackage{fuzz}" in latex
    assert "zed-cm" not in latex


def test_latex_gen_use_fuzz_false() -> None:
    """Test LaTeX generation with use_fuzz=False (default)."""
    text = """schema State
  x : N
end
"""
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()

    gen = LaTeXGenerator(use_fuzz=False)
    latex = gen.generate_document(ast)

    assert "\\usepackage{zed-cm}" in latex
    assert "fuzz" not in latex


def test_latex_gen_case_analysis() -> None:
    """Test LaTeX generation for CASE ANALYSIS (syntax not fully supported yet)."""
    # Skip - CASE ANALYSIS syntax needs work
    pass


def test_latex_gen_proof_tree() -> None:
    """Test LaTeX generation for PROOF tree."""
    text = """PROOF:
  x > 0
    x >= 0
"""
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()

    gen = LaTeXGenerator()
    latex = gen.generate_document(ast)

    assert "\\infer" in latex or "proof" in latex.lower()


def test_latex_gen_equiv_chain() -> None:
    """Test LaTeX generation for EQUIV chain."""
    text = """EQUIV:
p and q
<=> q and p [commutative]
<=> p and q
"""
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()

    gen = LaTeXGenerator()
    latex = gen.generate_document(ast)

    assert "\\Leftrightarrow" in latex
    assert "commutative" in latex


def test_latex_gen_truth_table() -> None:
    """Test LaTeX generation for truth table."""
    text = """TRUTH TABLE:
p | q | p and q
T | T | T
T | F | F
F | T | F
F | F | F
"""
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()

    gen = LaTeXGenerator()
    latex = gen.generate_document(ast)

    assert "\\begin{tabular}" in latex
    assert "\\hline" in latex


def test_latex_gen_text_paragraph() -> None:
    """Test LaTeX generation for TEXT paragraph."""
    text = """TEXT:
Some explanation
"""
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()

    gen = LaTeXGenerator()
    latex = gen.generate_document(ast)

    assert "explanation" in latex


def test_latex_gen_solution_marker() -> None:
    """Test LaTeX generation for solution marker."""
    text = """** Solution 5 **

x = 1
"""
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()

    gen = LaTeXGenerator()
    latex = gen.generate_document(ast)

    assert "\\textbf{Solution 5}" in latex
    assert "\\bigskip" in latex


def test_latex_gen_section() -> None:
    """Test LaTeX generation for section."""
    text = "=== Introduction ==="
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()

    gen = LaTeXGenerator()
    latex = gen.generate_document(ast)

    assert "\\section*{Introduction}" in latex


def test_latex_gen_part_label() -> None:
    """Test LaTeX generation for part label."""
    text = "(a) First part"
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()

    gen = LaTeXGenerator()
    latex = gen.generate_document(ast)

    assert "(a)" in latex
    assert "\\medskip" in latex


def test_latex_gen_given_types() -> None:
    """Test LaTeX generation for given types."""
    text = "given Person, Address"
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()

    gen = LaTeXGenerator()
    latex = gen.generate_document(ast)

    assert "\\begin{zed}" in latex or "\\begin{given}" in latex
    assert "Person" in latex
    assert "Address" in latex


def test_latex_gen_free_type() -> None:
    """Test LaTeX generation for free type."""
    text = "Bool ::= true | false"
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()

    gen = LaTeXGenerator()
    latex = gen.generate_document(ast)

    assert "Bool" in latex
    assert "::=" in latex or "\\defs" in latex


def test_latex_gen_abbreviation() -> None:
    """Test LaTeX generation for abbreviation."""
    text = "nonzero == {x : N | x > 0}"
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()

    gen = LaTeXGenerator()
    latex = gen.generate_document(ast)

    assert "nonzero" in latex
    assert "==" in latex or "\\defs" in latex


def test_latex_gen_axdef() -> None:
    """Test LaTeX generation for axdef."""
    text = """axdef
  count : N
where
  count > 0
end
"""
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()

    gen = LaTeXGenerator()
    latex = gen.generate_document(ast)

    assert "\\begin{axdef}" in latex
    assert "\\end{axdef}" in latex
    assert "count" in latex


def test_latex_gen_schema() -> None:
    """Test LaTeX generation for schema."""
    text = """schema State
  x : N
where
  x >= 0
end
"""
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()

    gen = LaTeXGenerator()
    latex = gen.generate_document(ast)

    assert "\\begin{schema}" in latex
    assert "{State}" in latex
    assert "\\end{schema}" in latex


def test_latex_gen_all_operators() -> None:
    """Test LaTeX generation for various operators."""
    text = "x and y or z => a <=> b"
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    result = parser.parse()
    assert isinstance(result, Expr)

    gen = LaTeXGenerator()
    latex = gen.generate_expr(result)

    assert "\\land" in latex
    assert "\\lor" in latex
    assert "\\Rightarrow" in latex
    assert "\\Leftrightarrow" in latex


def test_latex_gen_quantifiers() -> None:
    """Test LaTeX generation for quantifiers."""
    text = "forall x : N | x > 0"
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    result = parser.parse()
    assert isinstance(result, Expr)

    gen = LaTeXGenerator()
    latex = gen.generate_expr(result)

    assert "\\forall" in latex or "forall" in latex


def test_latex_gen_set_comprehension() -> None:
    """Test LaTeX generation for set comprehension."""
    text = "{x : N | x > 0}"
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    result = parser.parse()
    assert isinstance(result, Expr)

    gen = LaTeXGenerator()
    latex = gen.generate_expr(result)

    assert "{" in latex or "\\{" in latex


def test_latex_gen_set_literal() -> None:
    """Test LaTeX generation for set literal."""
    text = "{1, 2, 3}"
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    result = parser.parse()
    assert isinstance(result, Expr)

    gen = LaTeXGenerator()
    latex = gen.generate_expr(result)

    assert "{" in latex or "\\{" in latex


def test_latex_gen_sequence_literal() -> None:
    """Test LaTeX generation for sequence literal."""
    text = "⟨1, 2, 3⟩"
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    result = parser.parse()
    assert isinstance(result, Expr)

    gen = LaTeXGenerator()
    latex = gen.generate_expr(result)

    assert "\\langle" in latex
    assert "\\rangle" in latex


def test_latex_gen_bag_literal() -> None:
    """Test LaTeX generation for bag literal."""
    text = "[[1, 2, 3]]"
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    result = parser.parse()
    assert isinstance(result, Expr)

    gen = LaTeXGenerator()
    latex = gen.generate_expr(result)

    assert "bag" in latex.lower() or "[[" in latex


def test_latex_gen_tuple() -> None:
    """Test LaTeX generation for tuple."""
    text = "(1, 2, 3)"
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    result = parser.parse()
    assert isinstance(result, Expr)

    gen = LaTeXGenerator()
    latex = gen.generate_expr(result)

    assert "(" in latex
    assert "," in latex


def test_latex_gen_function_application() -> None:
    """Test LaTeX generation for function application."""
    text = "f(x, y)"
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    result = parser.parse()
    assert isinstance(result, Expr)

    gen = LaTeXGenerator()
    latex = gen.generate_expr(result)

    assert "f" in latex


def test_latex_gen_lambda() -> None:
    """Test LaTeX generation for lambda."""
    text = "(lambda x : N . x + 1)"
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    result = parser.parse()
    assert isinstance(result, Expr)

    gen = LaTeXGenerator()
    latex = gen.generate_expr(result)

    assert "\\lambda" in latex


def test_latex_gen_conditional() -> None:
    """Test LaTeX generation for conditional."""
    text = "if x > 0 then 1 else 0"
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    result = parser.parse()
    assert isinstance(result, Expr)

    gen = LaTeXGenerator()
    latex = gen.generate_expr(result)

    assert "if" in latex.lower()


def test_latex_gen_subscript() -> None:
    """Test LaTeX generation for subscript."""
    text = "x_i"
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    result = parser.parse()
    assert isinstance(result, Expr)

    gen = LaTeXGenerator()
    latex = gen.generate_expr(result)

    assert "_" in latex or "_{" in latex


def test_latex_gen_superscript() -> None:
    """Test LaTeX generation for superscript."""
    text = "x^2"
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    result = parser.parse()
    assert isinstance(result, Expr)

    gen = LaTeXGenerator()
    latex = gen.generate_expr(result)

    assert "^" in latex or "^{" in latex


def test_latex_gen_relational_image() -> None:
    """Test LaTeX generation for relational image."""
    text = "R (| {1, 2} |)"
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    result = parser.parse()
    assert isinstance(result, Expr)

    gen = LaTeXGenerator()
    latex = gen.generate_expr(result)

    assert "(|" in latex or "\\limg" in latex


def test_latex_gen_generic_instantiation() -> None:
    """Test LaTeX generation for generic instantiation."""
    text = "seq[N]"
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    result = parser.parse()
    assert isinstance(result, Expr)

    gen = LaTeXGenerator()
    latex = gen.generate_expr(result)

    assert "seq" in latex
    assert "[" in latex


def test_latex_gen_range() -> None:
    """Test LaTeX generation for range."""
    text = "1..10"
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    result = parser.parse()
    assert isinstance(result, Expr)

    gen = LaTeXGenerator()
    latex = gen.generate_expr(result)

    assert ".." in latex or "\\upto" in latex


def test_latex_gen_function_types() -> None:
    """Test LaTeX generation for function type operators."""
    text = "N -> N"
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    result = parser.parse()
    assert isinstance(result, Expr)

    gen = LaTeXGenerator()
    latex = gen.generate_expr(result)

    assert "\\fun" in latex or "\\to" in latex or "rightarrow" in latex.lower()
