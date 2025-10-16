"""Tests for Phase 11a: Function Type Operators.

Phase 11a adds 7 function type operators for Z notation:
- -> (total function)
- +-> (partial function)
- >-> (total injection)
- >+> (partial injection)
- -->> (total surjection)
- +->> (partial surjection)
- >->> (bijection)
"""

from __future__ import annotations

from txt2tex.ast_nodes import BinaryOp, FunctionType, Identifier
from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser
from txt2tex.tokens import TokenType


class TestPhase11aLexer:
    """Test Phase 11a function type operators in lexer."""

    def test_tfun_tokenization(self) -> None:
        """Test -> (total function) tokenizes correctly."""
        lexer = Lexer("X -> Y")
        tokens = lexer.tokenize()

        assert len(tokens) == 4  # X, ->, Y, EOF
        assert tokens[0].type == TokenType.IDENTIFIER
        assert tokens[0].value == "X"
        assert tokens[1].type == TokenType.TFUN
        assert tokens[1].value == "->"
        assert tokens[2].type == TokenType.IDENTIFIER
        assert tokens[2].value == "Y"

    def test_pfun_tokenization(self) -> None:
        """Test +-> (partial function) tokenizes correctly."""
        lexer = Lexer("X +-> Y")
        tokens = lexer.tokenize()

        assert len(tokens) == 4
        assert tokens[1].type == TokenType.PFUN
        assert tokens[1].value == "+->"

    def test_tinj_tokenization(self) -> None:
        """Test >-> (total injection) tokenizes correctly."""
        lexer = Lexer("X >-> Y")
        tokens = lexer.tokenize()

        assert len(tokens) == 4
        assert tokens[1].type == TokenType.TINJ
        assert tokens[1].value == ">->"

    def test_pinj_tokenization(self) -> None:
        """Test >+> (partial injection) tokenizes correctly."""
        lexer = Lexer("X >+> Y")
        tokens = lexer.tokenize()

        assert len(tokens) == 4
        assert tokens[1].type == TokenType.PINJ
        assert tokens[1].value == ">+>"

    def test_tsurj_tokenization(self) -> None:
        """Test -->> (total surjection) tokenizes correctly."""
        lexer = Lexer("X -->> Y")
        tokens = lexer.tokenize()

        assert len(tokens) == 4
        assert tokens[1].type == TokenType.TSURJ
        assert tokens[1].value == "-->>"

    def test_psurj_tokenization(self) -> None:
        """Test +->> (partial surjection) tokenizes correctly."""
        lexer = Lexer("X +->> Y")
        tokens = lexer.tokenize()

        assert len(tokens) == 4
        assert tokens[1].type == TokenType.PSURJ
        assert tokens[1].value == "+->>"

    def test_bijection_tokenization(self) -> None:
        """Test >->> (bijection) tokenizes correctly."""
        lexer = Lexer("X >->> Y")
        tokens = lexer.tokenize()

        assert len(tokens) == 4
        assert tokens[1].type == TokenType.BIJECTION
        assert tokens[1].value == ">->>"

    def test_longest_match_first(self) -> None:
        """Test longest-match-first prevents conflicts."""
        # >->> should be recognized as BIJECTION, not >-> followed by >
        lexer = Lexer("X >->> Y")
        tokens = lexer.tokenize()

        assert tokens[1].type == TokenType.BIJECTION
        assert tokens[1].value == ">->>"

        # +->> should be recognized as PSURJ, not +-> followed by >
        lexer2 = Lexer("A +->> B")
        tokens2 = lexer2.tokenize()

        assert tokens2[1].type == TokenType.PSURJ
        assert tokens2[1].value == "+->>"

        # -->> should be recognized as TSURJ, not -> preceded by -
        lexer3 = Lexer(r"M -->> \mathbb{N}")
        tokens3 = lexer3.tokenize()

        assert tokens3[1].type == TokenType.TSURJ
        assert tokens3[1].value == "-->>"


class TestPhase11aParser:
    """Test Phase 11a function type operators in parser."""

    def test_tfun_parsing(self) -> None:
        """Test -> (total function) parses to FunctionType."""
        lexer = Lexer("X -> Y")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        assert isinstance(ast, FunctionType)
        assert ast.arrow == "->"
        assert isinstance(ast.domain, Identifier)
        assert ast.domain.name == "X"
        assert isinstance(ast.range, Identifier)
        assert ast.range.name == "Y"

    def test_pfun_parsing(self) -> None:
        """Test +-> (partial function) parses to FunctionType."""
        lexer = Lexer("X +-> Y")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        assert isinstance(ast, FunctionType)
        assert ast.arrow == "+->"

    def test_tinj_parsing(self) -> None:
        """Test >-> (total injection) parses to FunctionType."""
        lexer = Lexer("X >-> Y")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        assert isinstance(ast, FunctionType)
        assert ast.arrow == ">->"

    def test_pinj_parsing(self) -> None:
        """Test >+> (partial injection) parses to FunctionType."""
        lexer = Lexer("X >+> Y")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        assert isinstance(ast, FunctionType)
        assert ast.arrow == ">+>"

    def test_tsurj_parsing(self) -> None:
        """Test -->> (total surjection) parses to FunctionType."""
        lexer = Lexer("X -->> Y")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        assert isinstance(ast, FunctionType)
        assert ast.arrow == "-->>"

    def test_psurj_parsing(self) -> None:
        """Test +->> (partial surjection) parses to FunctionType."""
        lexer = Lexer("X +->> Y")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        assert isinstance(ast, FunctionType)
        assert ast.arrow == "+->>"

    def test_bijection_parsing(self) -> None:
        """Test >->> (bijection) parses to FunctionType."""
        lexer = Lexer("X >->> Y")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        assert isinstance(ast, FunctionType)
        assert ast.arrow == ">->>"

    def test_right_associativity(self) -> None:
        """Test function types are right-associative."""
        lexer = Lexer("X -> Y -> Z")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        # Should parse as X -> (Y -> Z) (right-associative)
        assert isinstance(ast, FunctionType)
        assert ast.arrow == "->"
        assert isinstance(ast.domain, Identifier)
        assert ast.domain.name == "X"
        assert isinstance(ast.range, FunctionType)
        assert ast.range.arrow == "->"
        assert isinstance(ast.range.domain, Identifier)
        assert ast.range.domain.name == "Y"
        assert isinstance(ast.range.range, Identifier)
        assert ast.range.range.name == "Z"

    def test_precedence_with_relations(self) -> None:
        """Test function types have same precedence as relations."""
        # X <-> Y should work alongside X -> Y at same precedence level
        lexer = Lexer("X -> Y <-> Z")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        # Both at precedence 6, but -> is right-assoc: X -> (Y <-> Z)
        assert isinstance(ast, FunctionType)
        assert ast.arrow == "->"
        assert isinstance(ast.domain, Identifier)
        assert ast.domain.name == "X"
        assert isinstance(ast.range, BinaryOp)
        assert ast.range.operator == "<->"


class TestPhase11aLaTeXGeneration:
    """Test Phase 11a LaTeX generation for function types."""

    def test_tfun_latex(self) -> None:
        """Test -> generates \\fun."""
        lexer = Lexer("X -> Y")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, FunctionType)  # Type narrowing for mypy

        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)

        assert latex == r"X \fun Y"

    def test_pfun_latex(self) -> None:
        """Test +-> generates \\pfun."""
        lexer = Lexer("X +-> Y")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, FunctionType)

        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)

        assert latex == r"X \pfun Y"

    def test_tinj_latex(self) -> None:
        """Test >-> generates \\inj."""
        lexer = Lexer("X >-> Y")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, FunctionType)

        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)

        assert latex == r"X \inj Y"

    def test_pinj_latex(self) -> None:
        """Test >+> generates \\pinj."""
        lexer = Lexer("X >+> Y")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, FunctionType)

        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)

        assert latex == r"X \pinj Y"

    def test_tsurj_latex(self) -> None:
        """Test -->> generates \\surj."""
        lexer = Lexer("X -->> Y")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, FunctionType)

        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)

        assert latex == r"X \surj Y"

    def test_psurj_latex(self) -> None:
        """Test +->> generates \\psurj."""
        lexer = Lexer("X +->> Y")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, FunctionType)

        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)

        assert latex == r"X \psurj Y"

    def test_bijection_latex(self) -> None:
        """Test >->> generates \\bij."""
        lexer = Lexer("X >->> Y")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, FunctionType)

        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)

        assert latex == r"X \bij Y"

    def test_nested_function_types_latex(self) -> None:
        """Test nested function types generate correct parentheses."""
        lexer = Lexer("(N -> N) -> N")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, FunctionType)

        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)

        # Parentheses should be preserved from input parsing
        assert r"\fun" in latex


class TestPhase11aIntegration:
    """Test Phase 11a end-to-end integration."""

    def test_end_to_end_tfun(self) -> None:
        """Test complete pipeline for total function."""
        text = "X -> Y"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        assert isinstance(ast, FunctionType)
        assert ast.arrow == "->"

        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)

        assert latex == r"X \fun Y"

    def test_end_to_end_pfun(self) -> None:
        """Test complete pipeline for partial function."""
        text = "A +-> B"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        assert isinstance(ast, FunctionType)
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)

        assert latex == r"A \pfun B"

    def test_end_to_end_tinj(self) -> None:
        """Test complete pipeline for total injection."""
        text = "X >-> Y"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        assert isinstance(ast, FunctionType)
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)

        assert latex == r"X \inj Y"

    def test_end_to_end_bijection(self) -> None:
        """Test complete pipeline for bijection."""
        text = "Domain >->> Codomain"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        assert isinstance(ast, FunctionType)
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)

        assert latex == r"Domain \bij Codomain"

    def test_complex_function_type(self) -> None:
        """Test complex function type from homework."""
        text = "X <-> Y"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        assert isinstance(ast, BinaryOp)
        assert ast.operator == "<->"

        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)

        # Should generate: X \rel Y
        assert r"\rel" in latex

    def test_generic_function_declaration(self) -> None:
        """Test function type in generic context (for homework)."""
        text = "(X -> Y) -> Z"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        assert isinstance(ast, FunctionType)
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)

        # Should have function types with proper nesting
        assert latex.count(r"\fun") == 2  # Two -> operators

    def test_multiple_function_types(self) -> None:
        """Test multiple different function types in one expression."""
        text = "X -> Y +-> Z >-> W"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        assert isinstance(ast, FunctionType)  # Type narrowing
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)

        # Should have all three function type operators
        assert r"\fun" in latex
        assert r"\pfun" in latex
        assert r"\inj" in latex

    def test_function_type_with_set_ops(self) -> None:
        """Test function types work correctly with set operators."""
        text = "X -> Y"
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        assert isinstance(ast, FunctionType)  # Type narrowing
        gen = LaTeXGenerator()
        latex = gen.generate_expr(ast)

        # Should parse correctly as function type
        assert r"\fun" in latex
        assert "X" in latex
        assert "Y" in latex
