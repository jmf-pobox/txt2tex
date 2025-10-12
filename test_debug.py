from txt2tex.lexer import Lexer
from txt2tex.parser import Parser

text = """PROOF:
p and (q or r) => (p and q) or (p and r) [=> intro from 1]
  [1] p and (q or r) [assumption]
      p [and elim]
      q or r [and elim]
      (p and q) or (p and r) [or elim]
        case q:
          :: p [from above]
          :: q [from case]
          p and q [and intro]
          (p and q) or (p and r) [or intro]
        case r:
          :: p [from above]
          :: r [from case]
          p and r [and intro]
          (p and q) or (p and r) [or intro]
"""

lexer = Lexer(text)
tokens = lexer.tokenize()
parser = Parser(tokens)
ast = parser.parse()

# Print the tree structure
def print_tree(node, indent=0):
    from txt2tex.ast_nodes import ProofTree, ProofNode, CaseAnalysis, Identifier
    prefix = "  " * indent
    if isinstance(node, ProofTree):
        print(f"{prefix}ProofTree:")
        print_tree(node.conclusion, indent + 1)
    elif isinstance(node, ProofNode):
        expr_str = str(node.expression.name if isinstance(node.expression, Identifier) else "complex")
        print(f"{prefix}ProofNode: {expr_str} [just={node.justification}, label={node.label}, is_assumption={node.is_assumption}, is_sibling={node.is_sibling}]")
        for child in node.children:
            print_tree(child, indent + 1)
    elif isinstance(node, CaseAnalysis):
        print(f"{prefix}CaseAnalysis: case {node.case_name}")
        for step in node.steps:
            print_tree(step, indent + 1)

print_tree(ast.items[0])
