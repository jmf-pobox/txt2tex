"""LaTeX generator for txt2tex - converts AST to LaTeX."""

from __future__ import annotations

from typing import ClassVar

from txt2tex.ast_nodes import BinaryOp, Expr, Identifier, UnaryOp


class LaTeXGenerator:
    """Generates LaTeX from AST for Phase 0: simple propositional logic."""

    # Operator mappings
    BINARY_OPS: ClassVar[dict[str, str]] = {
        "and": r"\land",
        "or": r"\lor",
        "=>": r"\Rightarrow",
        "<=>": r"\Leftrightarrow",
    }

    UNARY_OPS: ClassVar[dict[str, str]] = {
        "not": r"\lnot",
    }

    def __init__(self, use_fuzz: bool = False) -> None:
        """Initialize generator with package choice."""
        self.use_fuzz = use_fuzz

    def generate_document(self, expr: Expr) -> str:
        """Generate complete LaTeX document with preamble and postamble."""
        lines: list[str] = []

        # Preamble
        lines.append(r"\documentclass{article}")
        if self.use_fuzz:
            lines.append(r"\usepackage{fuzz}")
        else:
            lines.append(r"\usepackage{zed-cm}")
            lines.append(r"\usepackage{zed-maths}")
        lines.append(r"\usepackage{amsmath}")
        lines.append(r"\begin{document}")
        lines.append("")

        # Content
        latex_expr = self.generate_expr(expr)
        lines.append(f"${latex_expr}$")
        lines.append("")

        # Postamble
        lines.append(r"\end{document}")

        return "\n".join(lines)

    def generate_expr(self, expr: Expr) -> str:
        """Generate LaTeX for expression (without wrapping in math mode)."""
        if isinstance(expr, Identifier):
            return self._generate_identifier(expr)
        if isinstance(expr, UnaryOp):
            return self._generate_unary_op(expr)
        if isinstance(expr, BinaryOp):
            return self._generate_binary_op(expr)

        raise TypeError(f"Unknown expression type: {type(expr)}")

    def _generate_identifier(self, node: Identifier) -> str:
        """Generate LaTeX for identifier."""
        return node.name

    def _generate_unary_op(self, node: UnaryOp) -> str:
        """Generate LaTeX for unary operation."""
        op_latex = self.UNARY_OPS.get(node.operator)
        if op_latex is None:
            raise ValueError(f"Unknown unary operator: {node.operator}")

        operand = self.generate_expr(node.operand)
        return f"{op_latex} {operand}"

    def _generate_binary_op(self, node: BinaryOp) -> str:
        """Generate LaTeX for binary operation."""
        op_latex = self.BINARY_OPS.get(node.operator)
        if op_latex is None:
            raise ValueError(f"Unknown binary operator: {node.operator}")

        left = self.generate_expr(node.left)
        right = self.generate_expr(node.right)
        return f"{left} {op_latex} {right}"
