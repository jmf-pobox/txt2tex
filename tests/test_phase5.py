"""Tests for Phase 5: Proof Trees."""

from __future__ import annotations

from txt2tex.ast_nodes import (
    BinaryOp,
    Identifier,
    ProofNode,
    ProofTree,
)
from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser


class TestLexer:
    """Tests for Phase 5 lexer features."""

    def test_proof_keyword(self) -> None:
        """Test lexing PROOF: keyword."""
        lexer = Lexer("PROOF:")
        tokens = lexer.tokenize()
        assert tokens[0].type.name == "PROOF"
        assert tokens[0].value == "PROOF:"


class TestParser:
    """Tests for Phase 5 parser features."""

    def test_simple_proof_tree(self) -> None:
        """Test parsing simple proof tree with no indentation."""
        text = """PROOF:
p
q"""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        # Document with one ProofTree item
        assert len(ast.items) == 1
        proof_tree = ast.items[0]
        assert isinstance(proof_tree, ProofTree)
        assert len(proof_tree.nodes) == 2
        assert isinstance(proof_tree.nodes[0], ProofNode)
        assert isinstance(proof_tree.nodes[1], ProofNode)

    def test_proof_tree_with_children(self) -> None:
        """Test parsing proof tree with nested children."""
        text = """PROOF:
p
  q
  r"""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        proof_tree = ast.items[0]
        assert isinstance(proof_tree, ProofTree)
        assert len(proof_tree.nodes) == 1

        # First node has 2 children
        first_node = proof_tree.nodes[0]
        assert len(first_node.children) == 2

    def test_proof_tree_with_justification(self) -> None:
        """Test parsing proof tree with justifications."""
        text = """PROOF:
p [premise]
  q [from p]"""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        proof_tree = ast.items[0]
        first_node = proof_tree.nodes[0]
        assert first_node.justification == "premise"
        assert first_node.children[0].justification == "from p"

    def test_proof_tree_complex_structure(self) -> None:
        """Test parsing proof tree with complex nested structure."""
        text = """PROOF:
p
  q
    r
  s
t"""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        proof_tree = ast.items[0]
        assert len(proof_tree.nodes) == 2  # p and t at top level

        # p has 2 children: q and s
        p_node = proof_tree.nodes[0]
        assert len(p_node.children) == 2

        # q has 1 child: r
        q_node = p_node.children[0]
        assert len(q_node.children) == 1

        # s has no children
        s_node = p_node.children[1]
        assert len(s_node.children) == 0

        # t has no children
        t_node = proof_tree.nodes[1]
        assert len(t_node.children) == 0

    def test_proof_tree_with_expressions(self) -> None:
        """Test parsing proof tree with complex expressions."""
        text = """PROOF:
p and q
  p
  q"""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        proof_tree = ast.items[0]
        first_node = proof_tree.nodes[0]

        # Expression should be BinaryOp
        assert isinstance(first_node.expression, BinaryOp)
        assert first_node.expression.operator == "and"


class TestLaTeXGenerator:
    """Tests for Phase 5 LaTeX generator."""

    def test_simple_proof_tree(self) -> None:
        """Test generating simple proof tree."""
        gen = LaTeXGenerator()
        ast = ProofTree(
            nodes=[
                ProofNode(
                    expression=Identifier(name="p", line=2, column=1),
                    justification=None,
                    children=[],
                    indent_level=0,
                    line=2,
                    column=1,
                ),
                ProofNode(
                    expression=Identifier(name="q", line=3, column=1),
                    justification=None,
                    children=[],
                    indent_level=0,
                    line=3,
                    column=1,
                ),
            ],
            line=1,
            column=1,
        )
        latex_lines = gen.generate_document_item(ast)
        latex = "\n".join(latex_lines)

        assert r"\begin{itemize}" in latex
        assert r"\item $p$" in latex
        assert r"\item $q$" in latex
        assert r"\end{itemize}" in latex

    def test_proof_tree_with_justification(self) -> None:
        """Test generating proof tree with justifications."""
        gen = LaTeXGenerator()
        ast = ProofTree(
            nodes=[
                ProofNode(
                    expression=Identifier(name="p", line=2, column=1),
                    justification="premise",
                    children=[],
                    indent_level=0,
                    line=2,
                    column=1,
                ),
            ],
            line=1,
            column=1,
        )
        latex_lines = gen.generate_document_item(ast)
        latex = "\n".join(latex_lines)

        assert r"\item $p$ [premise]" in latex

    def test_proof_tree_with_children(self) -> None:
        """Test generating proof tree with nested children."""
        gen = LaTeXGenerator()
        ast = ProofTree(
            nodes=[
                ProofNode(
                    expression=Identifier(name="p", line=2, column=1),
                    justification=None,
                    children=[
                        ProofNode(
                            expression=Identifier(name="q", line=3, column=3),
                            justification=None,
                            children=[],
                            indent_level=2,
                            line=3,
                            column=3,
                        ),
                    ],
                    indent_level=0,
                    line=2,
                    column=1,
                ),
            ],
            line=1,
            column=1,
        )
        latex_lines = gen.generate_document_item(ast)
        latex = "\n".join(latex_lines)

        # Check for nested itemize
        assert latex.count(r"\begin{itemize}") == 2
        assert latex.count(r"\end{itemize}") == 2
        assert r"\item $p$" in latex
        assert r"\item $q$" in latex


class TestIntegration:
    """End-to-end integration tests for Phase 5."""

    def test_complete_proof_tree(self) -> None:
        """Test complete pipeline for proof tree."""
        text = """PROOF:
p => q [premise]
p [premise]
  q [modus ponens]"""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        doc = gen.generate_document(ast)

        assert r"\begin{itemize}" in doc
        assert r"\item $p \Rightarrow q$ [premise]" in doc
        assert r"\item $p$ [premise]" in doc
        assert r"\item $q$ [modus ponens]" in doc
        assert r"\end{itemize}" in doc

    def test_complex_proof_tree(self) -> None:
        """Test complete pipeline for complex proof tree."""
        text = """PROOF:
p and q
  p
  q
r or s [assumption]
  r
    p => r
  s
    q => s"""
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        gen = LaTeXGenerator()
        doc = gen.generate_document(ast)

        assert r"\begin{itemize}" in doc
        assert r"$p \land q$" in doc
        assert r"$r \lor s$ [assumption]" in doc
        # Check for nested structure
        assert doc.count(r"\begin{itemize}") >= 2
