"""Test line continuation in different contexts (schemas, proofs, etc.)."""

from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser


def test_continuation_in_schema_where():
    """Test line break in schema where clause."""
    code = r"""schema TestSchema
  x : N
where
  x > 0 and \
    x < 100
end"""
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()

    gen = LaTeXGenerator()
    latex = gen.generate_document(ast)

    # Should contain line break in schema
    assert r"\\" in latex
    assert r"\quad" in latex
    assert "TestSchema" in latex


def test_continuation_in_multiple_schema_predicates():
    """Test line breaks with multiple predicates in schema."""
    code = r"""schema TestSchema
  x : N
  y : N
where
  x > 0 and \
    x < 100
  y > 0
end"""
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()

    gen = LaTeXGenerator()
    latex = gen.generate_document(ast)

    # Should have line break for first predicate
    assert r"\\" in latex
    # Should have both predicates
    assert "x" in latex and "y" in latex


def test_continuation_in_quantifier_body():
    """Test line break in quantifier body."""
    code = r"""EQUIV:
forall x : N | x > 0 and \
  x < 100"""
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()

    gen = LaTeXGenerator()
    latex = gen.generate_document(ast)

    assert r"\\" in latex
    assert r"\forall" in latex or "forall" in latex


def test_continuation_in_set_comprehension():
    """Test that continuation doesn't break set comprehensions."""
    code = r"""EQUIV:
{ x : N | x > 0 and x < 100 }"""
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()

    gen = LaTeXGenerator()
    latex = gen.generate_document(ast)

    # Should parse successfully
    assert "x" in latex


def test_continuation_in_proof():
    """Test line break in proof block."""
    code = r"""PROOF:
  p and \
    q
    r"""
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()

    gen = LaTeXGenerator()
    latex = gen.generate_document(ast)

    # Should contain line break
    assert r"\\" in latex


def test_continuation_with_long_predicate():
    """Test realistic long predicate with line break."""
    code = r"""schema Example
  s : ShowId
  e : EpisodeId
where
  s in dom show_episodes and e in show_episodes s and \
    card (show_episodes s) > 0
end"""
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()

    gen = LaTeXGenerator()
    latex = gen.generate_document(ast)

    # Should have line break
    assert r"\\" in latex
    # Should have relevant terms
    assert "show" in latex.lower() or "ShowId" in latex
