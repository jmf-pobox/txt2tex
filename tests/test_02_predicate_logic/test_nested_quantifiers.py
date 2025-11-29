"""Tests for nested quantifiers."""

from txt2tex.ast_nodes import BinaryOp, Quantifier
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser


def test_simple_nested_quantifier() -> None:
    """Test forall with nested exists."""
    text = "forall x : N | exists y : N | x = y"
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    result = parser.parse()
    assert isinstance(result, Quantifier)
    assert result.quantifier == "forall"
    assert isinstance(result.body, Quantifier)
    assert result.body.quantifier == "exists"


def test_mu_with_nested_forall_simple() -> None:
    """Test mu with nested forall (simplified)."""
    text = "mu p : N | forall q : N | p > q"
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    result = parser.parse()
    assert isinstance(result, Quantifier)
    assert result.quantifier == "mu"
    assert isinstance(result.body, Quantifier)
    assert result.body.quantifier == "forall"


def test_mu_with_nested_forall_complex_predicate() -> None:
    """Test mu with nested forall land complex predicate."""
    text = "mu p : N | forall q : N | p /= q land p > q"
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    result = parser.parse()
    assert isinstance(result, Quantifier)
    assert result.quantifier == "mu"
    assert isinstance(result.body, Quantifier)
    assert result.body.quantifier == "forall"


def test_constrained_quantifier() -> None:
    """Test constrained quantifier: forall x : T | constraint | body.

    Support for constrained quantifiers (filter semantics).
    Syntax: forall x : T | constraint | body
    Semantics: forall x : T | constraint => body (implication, not conjunction)
    """
    text = "forall x : N | x > 0 | x < 10"
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    result = parser.parse()
    assert isinstance(result, Quantifier)
    assert result.quantifier == "forall"
    assert isinstance(result.body, BinaryOp)
    assert result.body.operator == "implies"


def test_constrained_with_nested_quantifier() -> None:
    """Test constrained quantifier with nested quantifier (filter semantics).

    The double-pipe pattern uses implication: constraint => body
    """
    text = "mu p : N | forall q : N | p /= q | p > q"
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    result = parser.parse()
    assert isinstance(result, Quantifier)
    assert result.quantifier == "mu"
    assert isinstance(result.body, Quantifier)
    assert result.body.quantifier == "forall"
    assert isinstance(result.body.body, BinaryOp)
    assert result.body.body.operator == "implies"
