"""Tests for inline math in TEXT blocks."""

from txt2tex.ast_nodes import Document, Paragraph, Part, Section
from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser


class TestInlineMath:
    """Test inline math expressions in TEXT paragraphs."""

    def test_inline_set_comprehension(self) -> None:
        """Test inline set comprehension in TEXT."""
        source = """=== Test ===

TEXT: The set { x : N | x > 0 } contains positive integers.
"""
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        assert isinstance(ast, Document)
        assert len(ast.items) == 1
        assert isinstance(ast.items[0], Section)
        section = ast.items[0]
        assert len(section.items) == 1
        assert isinstance(section.items[0], Paragraph)

        # Generate LaTeX
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # Check that set comprehension is wrapped in $...$
        assert r"$\{ x \colon N \mid x > 0 \}$" in latex
        assert "contains positive integers" in latex

    def test_inline_quantifier(self) -> None:
        """Test inline quantifier in TEXT."""
        source = """=== Test ===

TEXT: We know that forall x : N | x >= 0 is true.
"""
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        assert isinstance(ast, Document)

        # Generate LaTeX
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # Check that quantifier is wrapped in $...$
        assert r"$\forall x \colon N \bullet x \geq 0$" in latex
        assert "We know that" in latex
        assert "is true" in latex

    def test_multiple_inline_math(self) -> None:
        """Test multiple inline math expressions in same TEXT."""
        source = """=== Test ===

TEXT: Both { x : N | x > 0 } and { y : N | y < 10 } are sets.
"""
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        # Generate LaTeX
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # Check both set comprehensions are converted
        assert r"$\{ x \colon N \mid x > 0 \}$" in latex
        assert r"$\{ y \colon N \mid y < 10 \}$" in latex
        assert "Both" in latex
        assert "and" in latex
        assert "are sets" in latex

    def test_non_math_braces(self) -> None:
        """Test that non-math braces are left as-is."""
        source = """=== Test ===

TEXT: Use braces like {this} for grouping in text.
"""
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        # Generate LaTeX
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # Check that invalid set comprehension is NOT converted
        # (should fail to parse and be left as-is)
        assert "{this}" in latex or r"\{this\}" in latex

    def test_inline_math_in_part(self) -> None:
        """Test inline math in part content."""
        source = """=== Test ===

(a)
TEXT: The set { x : N | x > 0 } is non-empty.
"""
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        assert isinstance(ast, Document)
        assert len(ast.items) == 1
        assert isinstance(ast.items[0], Section)
        section = ast.items[0]
        assert len(section.items) == 1
        assert isinstance(section.items[0], Part)

        # Generate LaTeX
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # Check that set comprehension is converted
        assert r"$\{ x \colon N \mid x > 0 \}$" in latex
        assert "is non-empty" in latex

    def test_symbolic_operators_with_inline_math(self) -> None:
        """Test that symbolic operators still work with inline math."""
        source = """=== Test ===

TEXT: We have { x : N | x > 0 } => x != 0 for all members.
"""
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        # Generate LaTeX
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)

        # Check both conversions
        assert r"$\{ x \colon N \mid x > 0 \}$" in latex
        assert r"$\Rightarrow$" in latex
        assert "for all members" in latex
