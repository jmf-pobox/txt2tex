"""Test quantifiers with complex type expressions.

Tests support for function types (X -> Y) and relation types (X <-> Y)
in quantifier bindings, as required by Z notation standard.
"""

from __future__ import annotations

from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser


def test_forall_with_function_type() -> None:
    """Test forall with function type binding: forall f : X -> Y | predicate."""
    txt = "forall f : X -> Y | f(x) = y"

    lexer = Lexer(txt)
    tokens = list(lexer.tokenize())
    parser = Parser(tokens)
    ast = parser.parse()

    gen = LaTeXGenerator()
    latex = gen.generate_document(ast)

    # Should generate: \forall f : X \fun Y \bullet f(x) = y
    assert r"\forall" in latex
    assert r"\fun" in latex or r"\rightarrow" in latex
    assert "f(x) = y" in latex or "f(x)" in latex


def test_forall_with_relation_type() -> None:
    """Test forall with relation type binding: forall R : X <-> Y | predicate."""
    txt = "forall R : X <-> Y | x in dom R"

    lexer = Lexer(txt)
    tokens = list(lexer.tokenize())
    parser = Parser(tokens)
    ast = parser.parse()

    gen = LaTeXGenerator()
    latex = gen.generate_document(ast)

    # Should generate: \forall R : X \rel Y \bullet x \in \dom R
    assert r"\forall" in latex
    assert r"\rel" in latex or r"leftrightarrow" in latex


def test_forall_with_function_and_simple_types() -> None:
    """Test forall with mixed function and simple type bindings."""
    txt = "forall f : X -> Y; x : X | f(x) in Y"

    lexer = Lexer(txt)
    tokens = list(lexer.tokenize())
    parser = Parser(tokens)
    ast = parser.parse()

    gen = LaTeXGenerator()
    latex = gen.generate_document(ast)

    # Should generate: \forall f : X \fun Y; x : X \bullet f(x) \in Y
    assert r"\forall" in latex
    assert r"\fun" in latex or r"\rightarrow" in latex
    assert latex.count("X") >= 2  # X appears in both declarations


def test_exists_with_function_type() -> None:
    """Test exists with function type binding: exists f : X -> Y | predicate."""
    txt = "exists f : X -> Y | f(x) = y"

    lexer = Lexer(txt)
    tokens = list(lexer.tokenize())
    parser = Parser(tokens)
    ast = parser.parse()

    gen = LaTeXGenerator()
    latex = gen.generate_document(ast)

    # Should generate: \exists f : X \fun Y \bullet f(x) = y
    assert r"\exists" in latex
    assert r"\fun" in latex or r"\rightarrow" in latex


def test_exists1_with_function_type() -> None:
    """Test exists1 with function type binding: exists1 f : X -> Y | predicate."""
    txt = "exists1 f : X -> Y | f(x) = y"

    lexer = Lexer(txt)
    tokens = list(lexer.tokenize())
    parser = Parser(tokens)
    ast = parser.parse()

    gen = LaTeXGenerator()
    latex = gen.generate_document(ast)

    # Should generate: \exists_1 f : X \fun Y \bullet f(x) = y
    assert r"\exists" in latex
    assert r"\fun" in latex or r"\rightarrow" in latex


def test_gendef_with_function_type_in_quantifier() -> None:
    """Test quantifier with function type inside gendef block."""
    txt = """gendef [X, Y]
  map : (X -> Y) cross seq X -> seq Y
where
  forall f : X -> Y | map(f, ⟨⟩) = ⟨⟩
end
"""

    lexer = Lexer(txt)
    tokens = list(lexer.tokenize())
    parser = Parser(tokens)
    ast = parser.parse()

    gen = LaTeXGenerator()
    latex = gen.generate_document(ast)

    # Should generate gendef with quantifier containing function type
    assert r"\forall" in latex
    assert r"\fun" in latex or r"\rightarrow" in latex
    assert "map" in latex


def test_nested_function_types() -> None:
    """Test quantifier with nested function types: (X -> Y) -> Z."""
    txt = "forall h : (X -> Y) -> Z | h(f) in Z"

    lexer = Lexer(txt)
    tokens = list(lexer.tokenize())
    parser = Parser(tokens)
    ast = parser.parse()

    gen = LaTeXGenerator()
    latex = gen.generate_document(ast)

    # Should handle nested function types
    assert r"\forall" in latex
    # Should have nested function arrows
    assert latex.count(r"\fun") >= 2 or latex.count(r"\rightarrow") >= 2


def test_partial_function_type() -> None:
    """Test quantifier with partial function type: X +-> Y."""
    txt = "forall f : X +-> Y | x in dom f"

    lexer = Lexer(txt)
    tokens = list(lexer.tokenize())
    parser = Parser(tokens)
    ast = parser.parse()

    gen = LaTeXGenerator()
    latex = gen.generate_document(ast)

    # Should handle partial function symbol
    assert r"\forall" in latex
    assert r"\pfun" in latex or "pfun" in latex
