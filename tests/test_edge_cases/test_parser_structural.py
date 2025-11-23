"""Tests for parser structural elements to increase coverage.

These tests target uncovered structural parsing code paths.
All test inputs use valid, working syntax.
"""

from __future__ import annotations

from txt2tex.ast_nodes import (
    Abbreviation,
    AxDef,
    Document,
    FreeType,
    GivenType,
    Part,
    Schema,
    Section,
    Solution,
)
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser


def test_solution_with_parts() -> None:
    """Test solution containing part labels."""
    text = """** Solution 1 **

(a) x > 0

(b) y > 0
"""
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    result = parser.parse()

    assert isinstance(result, Document)
    # Should have solution with parts inside
    assert isinstance(result.items[0], Solution)


def test_multiple_solutions() -> None:
    """Test multiple solutions in sequence."""
    text = """** Solution 1 **

x = 1

** Solution 2 **

y = 2
"""
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    result = parser.parse()

    assert isinstance(result, Document)
    assert len(result.items) >= 2


def test_section_with_content() -> None:
    """Test section containing other items."""
    text = """=== Chapter 1 ===

x = 1
"""
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    result = parser.parse()

    assert isinstance(result, Document)
    assert isinstance(result.items[0], Section)


def test_section_with_prose_starter_words() -> None:
    """Test section headers with words that trigger prose detection.

    Regression test for bug where prose-starter words in section headers
    (like "First", "Show", "Using") were incorrectly treated as prose,
    consuming the rest of the line including the closing ===.
    """
    # Test the exact example from README
    text = """=== My First Proof ===

** Solution 1 **

x = 1
"""
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    result = parser.parse()

    assert isinstance(result, Document)
    assert isinstance(result.items[0], Section)
    assert result.items[0].title == "My First Proof"

    # Test other prose-starter words
    test_cases = [
        "=== First Steps ===",
        "=== Show Your Work ===",
        "=== Using Natural Deduction ===",
        "=== Prove the Theorem ===",
        "=== Second Attempt ===",
        "=== Given These Assumptions ===",
        "=== Consider the Following ===",
    ]

    for section_header in test_cases:
        text = f"{section_header}\n\nx = 1\n"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        result = parser.parse()

        assert isinstance(result, Document)
        assert isinstance(result.items[0], Section)
        # Verify title was extracted correctly (strip === markers)
        expected_title = section_header.strip("= ")
        assert result.items[0].title == expected_title


def test_given_types_multiple() -> None:
    """Test given clause with multiple types."""
    text = "given Person, Address, Company"
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    result = parser.parse()

    assert isinstance(result, Document)
    assert isinstance(result.items[0], GivenType)
    assert len(result.items[0].names) == 3


def test_free_type_three_branches() -> None:
    """Test free type with three branches."""
    text = "Color ::= red | green | blue"
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    result = parser.parse()

    assert isinstance(result, Document)
    assert isinstance(result.items[0], FreeType)
    assert len(result.items[0].branches) == 3


def test_abbreviation_simple() -> None:
    """Test simple abbreviation."""
    text = "positive == {x : N | x > 0}"
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    result = parser.parse()

    assert isinstance(result, Document)
    assert isinstance(result.items[0], Abbreviation)


def test_axdef_with_where() -> None:
    """Test axdef with where clause."""
    text = """axdef
  count : N
where
  count > 0
end
"""
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    result = parser.parse()

    assert isinstance(result, Document)
    assert isinstance(result.items[0], AxDef)
    assert len(result.items[0].predicates) > 0


def test_schema_with_where() -> None:
    """Test schema with where clause."""
    text = """schema State
  x : N
where
  x >= 0
end
"""
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    result = parser.parse()

    assert isinstance(result, Document)
    assert isinstance(result.items[0], Schema)
    assert len(result.items[0].predicates) > 0


def test_part_standalone() -> None:
    """Test part label as standalone item."""
    text = "(a) First part"
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    result = parser.parse()

    assert isinstance(result, Document)
    assert isinstance(result.items[0], Part)
    assert result.items[0].label == "a"


def test_complex_quantifier() -> None:
    """Test quantifier with complex predicate."""
    text = "forall x : N | x > 0 and x < 100 or x = 0"
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    result = parser.parse()

    # Should parse without error
    assert result is not None


def test_nested_set_operations() -> None:
    """Test nested set operations."""
    text = "(A union B) intersect (C union D)"
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    result = parser.parse()

    # Should parse without error
    assert result is not None


def test_function_composition() -> None:
    """Test function composition operator.

    Note: Using o9 for composition - semicolon is reserved for declarations.
    """
    text = "f o9 g"
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    result = parser.parse()

    # Should parse without error
    assert result is not None


def test_relational_operators() -> None:
    """Test various relational operators."""
    text = "x <= y and y >= z and a != b"
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    result = parser.parse()

    # Should parse without error
    assert result is not None


def test_schema_operations() -> None:
    """Test schema composition."""
    text = "State and OtherState"
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    result = parser.parse()

    # Should parse without error
    assert result is not None


def test_hiding_operator() -> None:
    """Test hiding operator."""
    text = "State \\ (x, y)"
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    result = parser.parse()

    # Should parse without error
    assert result is not None
