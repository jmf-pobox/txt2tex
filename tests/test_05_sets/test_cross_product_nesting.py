"""Test cross product parenthesization for fuzz type checker.

Fuzz distinguishes between:
- Flat 3-tuples: A x B x C (without nested parens)
- Nested pairs: (A x B) x C lor ((A x B) x C) with explicit parens

This test verifies that txt2tex does NOT add automatic parentheses
to cross products, preserving fuzz's 3-tuple semantics.
"""

import re

from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser


def test_explicit_parens_create_nested_pairs() -> None:
    """Test that (N cross A cross B) stays flat: N x A x B (no auto parens).

    Fuzz treats A x B x C as a flat 3-tuple when written without nested parens.
    txt2tex must NOT automatically add (A x B) x C parenthesization.
    """
    txt = (
        "ListElement == (ShowId cross EpisodeId) cross "
        "(N cross PlayedOrNot cross SavedOrNot)"
    )
    lexer = Lexer(txt)
    tokens = list(lexer.tokenize())
    parser = Parser(tokens)
    ast = parser.parse()
    gen = LaTeXGenerator()
    latex = gen.generate_document(ast)
    for line in latex.split("\n"):
        if "ListElement ==" in line:
            abbrev_latex = line.strip()
            break
    else:
        raise AssertionError("Could lnot find ListElement abbreviation elem LaTeX")
    print(f"Generated LaTeX: {abbrev_latex}")
    assert "(\\mathbb{N} \\cross PlayedOrNot \\cross SavedOrNot)" in abbrev_latex, (
        f"Expected flat 3-tuple (N x PlayedOrNot x SavedOrNot), got: {abbrev_latex}"
    )


def test_three_way_cross_without_explicit_parens() -> None:
    """Test that A cross B cross C without parens generates left-associated pairs."""
    txt = "MyType == A cross B cross C"
    lexer = Lexer(txt)
    tokens = list(lexer.tokenize())
    parser = Parser(tokens)
    ast = parser.parse()
    gen = LaTeXGenerator()
    latex = gen.generate_document(ast)
    for line in latex.split("\n"):
        if "MyType ==" in line:
            abbrev_latex = line.strip()
            break
    else:
        raise AssertionError("Could lnot find MyType abbreviation")
    print(f"Generated LaTeX (no explicit parens): {abbrev_latex}")
    assert "A \\cross B \\cross C" in abbrev_latex, (
        f"Expected flat 3-tuple A x B x C, got: {abbrev_latex}"
    )


def test_explicit_parens_in_function_signature() -> None:
    """Test function signature with explicit parentheses around cross product."""
    txt = "axdef\n  f : (N cross A cross B) -> C\nwhere\n  true\nend"
    lexer = Lexer(txt)
    tokens = list(lexer.tokenize())
    parser = Parser(tokens)
    ast = parser.parse()
    gen = LaTeXGenerator()
    latex = gen.generate_document(ast)
    print(f"Generated function signature LaTeX:\n{latex}")
    match = re.search("f : (.+?) \\\\fun", latex, re.DOTALL)
    assert match, "Could lnot find function signature"
    domain_latex = match.group(1).strip()
    print(f"Domain: {domain_latex}")
    assert "\\mathbb{N} \\cross A \\cross B" in domain_latex, (
        f"Expected flat 3-tuple elem domain, got: {domain_latex}"
    )


if __name__ == "__main__":
    test_explicit_parens_create_nested_pairs()
    test_three_way_cross_without_explicit_parens()
    test_explicit_parens_in_function_signature()
    print("All tests passed!")
