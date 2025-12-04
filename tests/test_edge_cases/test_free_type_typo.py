"""Test cases for free type definition typos land error handling."""

from __future__ import annotations

import pytest

from txt2tex.ast_nodes import Document, FreeType
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser, ParserError


def test_free_type_with_double_equals_typo():
    """Test that ::== typo produces helpful error instead of infinite loop.

    User wrote ::== instead of ::=. This should produce a clear error message
    suggesting the correct syntax, lnot hang elem an infinite loop.
    """
    text = "ReadStatus ::== Done | Pending"
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    with pytest.raises(
        ParserError,
        match=r"Unexpected '=' in free type definition\. "
        r"Did you mean '::=' instead of '::=='?",
    ):
        parser.parse()


def test_free_type_with_correct_syntax():
    """Test that correct ::= syntax works properly."""
    text = "ReadStatus ::= Done | Pending"
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    doc = parser.parse()
    assert isinstance(doc, Document)
    assert len(doc.items) == 1
    free_type = doc.items[0]
    assert isinstance(free_type, FreeType)
    assert free_type.name == "ReadStatus"
    assert len(free_type.branches) == 2
    assert free_type.branches[0].name == "Done"
    assert free_type.branches[1].name == "Pending"


def test_free_type_branch_names_with_reserved_keywords():
    """Test that P, F, P1, F1 can be used as branch names in free types."""
    text = "Status ::= P | F | P1 | F1"
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    doc = parser.parse()
    assert isinstance(doc, Document)
    assert len(doc.items) == 1
    free_type = doc.items[0]
    assert isinstance(free_type, FreeType)
    assert free_type.name == "Status"
    assert len(free_type.branches) == 4
    assert free_type.branches[0].name == "P"
    assert free_type.branches[1].name == "F"
    assert free_type.branches[2].name == "P1"
    assert free_type.branches[3].name == "F1"


def test_free_type_with_unexpected_token():
    """Test that other unexpected tokens produce clear error messages."""
    text = "Type ::= branch1 + branch2"
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    with pytest.raises(
        ParserError,
        match="Expected branch name or '\\|' in free type definition, got PLUS",
    ):
        parser.parse()
