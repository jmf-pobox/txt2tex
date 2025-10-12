#!/usr/bin/env python3
"""Debug script to inspect AST for Example 4."""

import sys
sys.path.insert(0, "src")

from txt2tex.lexer import Lexer
from txt2tex.parser import Parser

input_text = """PROOF:
(p => q) and not q => not p [=> intro from 1]
  [1] (p => q) and not q [assumption]
      :: p => q [and elim]
      :: not q [and elim]
      not p [negation intro from 2]
        [2] p [assumption]
            q [=> elim]
            false [contradiction]
"""

lexer = Lexer(input_text)
tokens = lexer.tokenize()
parser = Parser(tokens)
ast = parser.parse()

def print_proof_tree(node, indent=0):
    """Print proof tree structure."""
    from txt2tex.ast_nodes import ProofTree, ProofNode, CaseAnalysis

    prefix = "  " * indent
    if isinstance(node, ProofTree):
        print(f"{prefix}ProofTree:")
        print_proof_tree(node.conclusion, indent + 1)
    elif isinstance(node, ProofNode):
        expr_str = str(node.expression)[:50]
        just_str = node.justification or "None"
        label_str = node.label or "None"
        print(f"{prefix}ProofNode: {expr_str} [just={just_str}, label={label_str}, is_assumption={node.is_assumption}, is_sibling={node.is_sibling}]")
        for child in node.children:
            print_proof_tree(child, indent + 1)
    elif isinstance(node, CaseAnalysis):
        print(f"{prefix}CaseAnalysis: case {node.case_name}")
        for step in node.steps:
            print_proof_tree(step, indent + 1)

for item in ast.items:
    print_proof_tree(item)
