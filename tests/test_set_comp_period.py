"""Tests for set comprehension with '.' separator (Phase 22)."""

from txt2tex.ast_nodes import SetComprehension
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser


def test_set_comp_with_period_separator() -> None:
    """Test set comprehension with period separator: {x : N . expr}."""
    text = "{p : Person . p |-> f(p)}"
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    result = parser.parse()

    # Should parse as: {p : Person . p |-> f(p)} with predicate=None
    assert isinstance(result, SetComprehension)
    assert result.variables == ["p"]
    assert result.predicate is None
    assert result.expression is not None


def test_set_comp_period_vs_pipe() -> None:
    """Test difference between period and pipe separator."""
    # Period: no predicate
    text1 = "{x : N . x * 2}"
    lexer1 = Lexer(text1)
    result1 = Parser(lexer1.tokenize()).parse()
    assert isinstance(result1, SetComprehension)
    assert result1.predicate is None
    assert result1.expression is not None

    # Pipe: has predicate
    text2 = "{x : N | x > 0 . x * 2}"
    lexer2 = Lexer(text2)
    result2 = Parser(lexer2.tokenize()).parse()
    assert isinstance(result2, SetComprehension)
    assert result2.predicate is not None
    assert result2.expression is not None
