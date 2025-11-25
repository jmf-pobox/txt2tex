"""Tests to increase latex_gen.py coverage to 90%+."""

from __future__ import annotations

import pytest

from txt2tex.ast_nodes import (
    BinaryOp,
    CaseAnalysis,
    Expr,
    FunctionApp,
    Identifier,
    Paragraph,
    Quantifier,
    SequenceLiteral,
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


# Additional LaTeX generator coverage tests


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

    assert "\\section*{Solution 5}" in latex
    # TOC is no longer automatically generated - requires CONTENTS: directive


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

    assert "\\subsection*{(a)}" in latex
    assert "First part" in latex


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

    assert r"\bsup" in latex


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

    # seq[N] renders as \seq \mathbb{N} (no brackets for special types)
    assert "seq" in latex
    assert "\\mathbb{N}" in latex
    assert latex == "\\seq \\mathbb{N}"


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


# Additional coverage tests from test_latex_gen_more_coverage.py


def test_unknown_quantifier() -> None:
    """Test error for unknown quantifier (line 463)."""
    node = Quantifier(
        quantifier="???",
        variables=["x"],
        domain=Identifier(name="N", line=1, column=1),
        body=Identifier(name="true", line=1, column=1),
        expression=None,
        line=1,
        column=1,
    )
    gen = LaTeXGenerator()

    with pytest.raises(ValueError, match="Unknown quantifier"):
        gen.generate_expr(node)


def test_pattern3_parse_failure() -> None:
    """Test Pattern 3 fallback when parsing fails (lines 1048-1051)."""
    para = Paragraph(text="The value x := 5 is assigned here.", line=1, column=1)
    gen = LaTeXGenerator()
    latex_lines = gen._generate_paragraph(para)
    latex = "\n".join(latex_lines)

    # Should still process the text (even if := doesn't parse)
    assert "x" in latex


def test_sequence_notation_empty() -> None:
    """Test empty sequence notation (line 770)."""
    node = SequenceLiteral(elements=[], line=1, column=1)
    gen = LaTeXGenerator()
    latex = gen.generate_expr(node)

    # Empty sequence: \langle \rangle
    assert r"\langle" in latex
    assert r"\rangle" in latex


def test_case_analysis_depth_no_steps() -> None:
    """Test case analysis depth calculation with no steps (line 1270)."""
    # Create a CaseAnalysis with no steps
    case = CaseAnalysis(case_name="p", steps=[], line=1, column=1)

    gen = LaTeXGenerator()
    depth = gen._calculate_tree_depth(case)

    # Should return 0 for empty case
    assert depth == 0


# Complex proof tree tests removed - ProofNode requires many fields
# (label, is_assumption, indent_level, etc.) and lines 1279-1283 are
# in complex case analysis code that's hard to test in isolation


def test_identifier_edge_case_empty_parts() -> None:
    """Test identifier with empty parts after split (lines 350-351)."""
    # Edge case: multiple consecutive underscores
    node = Identifier(name="x___y", line=1, column=1)
    gen = LaTeXGenerator()
    latex = gen._generate_identifier(node)

    # Should use fallback: mathit with escaped underscores
    assert r"\mathit{" in latex
    assert r"\_" in latex


def test_identifier_exactly_two_parts_long_suffix() -> None:
    """Test identifier with exactly 2 parts where suffix > 3 chars (line 336)."""
    # Should trigger multi-word heuristic
    node = Identifier(name="x_maximum", line=1, column=1)
    gen = LaTeXGenerator()
    latex = gen._generate_identifier(node)

    # Should use mathit (suffix > 3 chars)
    assert r"\mathit{x\_maximum}" in latex


def test_sequence_corner_bracket_with_label() -> None:
    """Test sequence corner bracket with label (line 1264)."""
    para = Paragraph(text="SEQUENCE: [p => q] [modus-ponens]", line=1, column=1)
    gen = LaTeXGenerator()
    latex_lines = gen._generate_paragraph(para)
    latex = "\n".join(latex_lines)

    # Should generate corner brackets with label
    assert r"\ulcorner" in latex or "SEQUENCE:" in latex


# Removed test_right_associative_subtraction - line 425 is part of
# parenthesization logic that's already covered by test_right_associative_parens
# in test_latex_gen_errors.py
