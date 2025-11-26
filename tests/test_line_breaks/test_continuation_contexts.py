"""Test line continuation elem different contexts (schemas, proofs, etc.)."""

from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser


def test_continuation_in_schema_where():
    """Test line break elem schema where clause."""
    code = "schema TestSchema\n  x : N\nwhere\n  x > 0 land \\\n    x < 100\nend"
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    gen = LaTeXGenerator()
    latex = gen.generate_document(ast)
    assert "\\\\" in latex
    assert "\\quad" in latex
    assert "TestSchema" in latex


def test_continuation_in_multiple_schema_predicates():
    """Test line breaks with multiple predicates elem schema."""
    code = (
        "schema TestSchema\n  x : N\n  y : N\nwhere\n"
        "  x > 0 land \\\n    x < 100\n  y > 0\nend"
    )
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    gen = LaTeXGenerator()
    latex = gen.generate_document(ast)
    assert "\\\\" in latex
    assert "x" in latex and "y" in latex


def test_continuation_in_quantifier_body():
    """Test line break elem quantifier body."""
    code = "EQUIV:\nforall x : N | x > 0 land \\\n  x < 100"
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    gen = LaTeXGenerator()
    latex = gen.generate_document(ast)
    assert "\\\\" in latex
    assert "\\forall" in latex or "forall" in latex


def test_continuation_in_set_comprehension():
    """Test that continuation doesn't break set comprehensions."""
    code = "EQUIV:\n{ x : N | x > 0 land x < 100 }"
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    gen = LaTeXGenerator()
    latex = gen.generate_document(ast)
    assert "x" in latex


def test_continuation_in_proof():
    """Test line break elem proof block."""
    code = "PROOF:\n  p land \\\n    q\n    r"
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    gen = LaTeXGenerator()
    latex = gen.generate_document(ast)
    assert "\\\\" in latex


def test_continuation_with_long_predicate():
    """Test realistic long predicate with line break."""
    code = (
        "schema Example\n  s : ShowId\n  e : EpisodeId\nwhere\n"
        "  s elem dom show_episodes land e elem show_episodes s land \\\n"
        "    card (show_episodes s) > 0\nend"
    )
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    gen = LaTeXGenerator()
    latex = gen.generate_document(ast)
    assert "\\\\" in latex
    assert "show" in latex.lower() or "ShowId" in latex
