"""Tests for Phase 29: Explicit Parentheses Preservation.

When users write explicit parentheses like (A and B) and C, these should be
preserved in the LaTeX output even if not strictly required by precedence rules.
This maintains semantic grouping clarity from the source text.
"""

from __future__ import annotations

from txt2tex.ast_nodes import BinaryOp
from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser


class TestExplicitParenthesesParsing:
    """Test that parser marks explicitly parenthesized expressions."""

    def test_simple_parenthesized_and(self) -> None:
        """Test that (A and B) sets explicit_parens flag."""
        lexer = Lexer("(A and B)")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        assert isinstance(ast, BinaryOp)
        assert ast.operator == "and"
        assert ast.explicit_parens is True

    def test_nested_explicit_parens(self) -> None:
        """Test that (A and B) and C preserves explicit_parens on left child."""
        lexer = Lexer("(A and B) and C")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        assert isinstance(ast, BinaryOp)
        assert ast.operator == "and"
        assert ast.explicit_parens is False  # Outer expression not parenthesized

        # Left child should have explicit_parens = True
        assert isinstance(ast.left, BinaryOp)
        assert ast.left.explicit_parens is True

    def test_double_nested_explicit_parens(self) -> None:
        """Test ((A and B) and C) with two levels of explicit parens."""
        lexer = Lexer("((A and B) and C)")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        assert isinstance(ast, BinaryOp)
        assert ast.explicit_parens is True  # Outer parens

        # Left child also has explicit parens
        assert isinstance(ast.left, BinaryOp)
        assert ast.left.explicit_parens is True

    def test_no_explicit_parens_without_parentheses(self) -> None:
        """Test that A and B and C has no explicit_parens flags."""
        lexer = Lexer("A and B and C")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        assert isinstance(ast, BinaryOp)
        assert ast.explicit_parens is False

        assert isinstance(ast.left, BinaryOp)
        assert ast.left.explicit_parens is False


class TestExplicitParenthesesLaTeXGeneration:
    """Test that LaTeX generator preserves explicit parentheses."""

    def test_explicit_parens_simple(self) -> None:
        """Test (A and B) generates (A \\land B)."""
        lexer = Lexer("(A and B)")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        generator = LaTeXGenerator(use_fuzz=True)
        latex = generator.generate_document(ast)

        assert r"(A \land B)" in latex

    def test_explicit_parens_nested_left(self) -> None:
        """Test (A and B) and C generates (A \\land B) \\land C."""
        lexer = Lexer("(A and B) and C")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        generator = LaTeXGenerator(use_fuzz=True)
        latex = generator.generate_document(ast)

        assert r"(A \land B) \land C" in latex

    def test_explicit_parens_nested_right(self) -> None:
        """Test A and (B and C) generates A \\land (B \\land C)."""
        lexer = Lexer("A and (B and C)")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        generator = LaTeXGenerator(use_fuzz=True)
        latex = generator.generate_document(ast)

        assert r"A \land (B \land C)" in latex

    def test_explicit_parens_double_nested(self) -> None:
        """Test ((A and B) and C) generates ((A \\land B) \\land C)."""
        lexer = Lexer("((A and B) and C)")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        generator = LaTeXGenerator(use_fuzz=True)
        latex = generator.generate_document(ast)

        assert r"((A \land B) \land C)" in latex

    def test_no_explicit_parens_same_precedence(self) -> None:
        """Test A and B and C generates A \\land B \\land C (no parens)."""
        lexer = Lexer("A and B and C")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        generator = LaTeXGenerator(use_fuzz=True)
        latex = generator.generate_document(ast)

        # Should be no parentheses (left-associative, no explicit parens)
        assert r"A \land B \land C" in latex
        assert r"(A \land B)" not in latex

    def test_explicit_parens_with_quantifier(self) -> None:
        """Test forall x | (A and B) and C preserves grouping."""
        lexer = Lexer("forall x : N | (A and B) and C")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        generator = LaTeXGenerator(use_fuzz=True)
        latex = generator.generate_document(ast)

        # The quantifier body should preserve explicit parens
        assert r"(A \land B) \land C" in latex

    def test_explicit_parens_mixed_operators(self) -> None:
        """Test (A or B) and C preserves parens for clarity."""
        lexer = Lexer("(A or B) and C")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        generator = LaTeXGenerator(use_fuzz=True)
        latex = generator.generate_document(ast)

        # Explicit parens should be preserved
        assert r"(A \lor B) \land C" in latex

    def test_explicit_parens_with_equals(self) -> None:
        """Test (a = b) and (c = d) in quantifier context."""
        lexer = Lexer("forall x | (a = b) and (c = d)")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        generator = LaTeXGenerator(use_fuzz=True)
        latex = generator.generate_document(ast)

        # Both explicit parens should be preserved
        assert r"(a = b) \land (c = d)" in latex

    def test_deeply_nested_explicit_parens(self) -> None:
        """Test (((A and B) and C) and D) with multiple levels."""
        lexer = Lexer("(((A and B) and C) and D)")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        generator = LaTeXGenerator(use_fuzz=True)
        latex = generator.generate_document(ast)

        # All explicit parens should be preserved
        assert r"(((A \land B) \land C) \land D)" in latex


class TestQuestionTenScenario:
    """Test the specific scenario from Question 10(b) and 10(c)."""

    def test_question_10b_grouping(self) -> None:
        """Test the unplayed function grouping from Question 10(b)."""
        # Simplified version of the problematic expression
        txt = "forall pl | (fst(x) = Played and unplayed(y) = z) and unplayed(w) = v"

        lexer = Lexer(txt)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        generator = LaTeXGenerator(use_fuzz=True)
        latex = generator.generate_document(ast)

        # The first part should be grouped with explicit parens
        assert r"(fst(x) = Played \land unplayed(y) = z) \land" in latex

    def test_question_10c_grouping(self) -> None:
        """Test the played function grouping from Question 10(c)."""
        # Simplified version of the problematic expression
        txt = "forall pl | (fst(x) = NotP and played(y) = z) and played(w) = v"

        lexer = Lexer(txt)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        generator = LaTeXGenerator(use_fuzz=True)
        latex = generator.generate_document(ast)

        # The first part should be grouped with explicit parens
        assert r"(fst(x) = NotP \land played(y) = z) \land" in latex
