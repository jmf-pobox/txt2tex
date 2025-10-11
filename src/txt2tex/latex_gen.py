"""LaTeX generator for txt2tex - converts AST to LaTeX."""

from __future__ import annotations

import re
from typing import ClassVar

from txt2tex.ast_nodes import (
    Abbreviation,
    AxDef,
    BinaryOp,
    Declaration,
    Document,
    DocumentItem,
    EquivChain,
    Expr,
    FreeType,
    GivenType,
    Identifier,
    Number,
    Part,
    Quantifier,
    Schema,
    Section,
    Solution,
    Subscript,
    Superscript,
    TruthTable,
    UnaryOp,
)


class LaTeXGenerator:
    """Generates LaTeX from AST for Phase 0 + Phase 1 + Phase 2 + Phase 3 + Phase 4."""

    # Operator mappings
    BINARY_OPS: ClassVar[dict[str, str]] = {
        # Propositional logic
        "and": r"\land",
        "or": r"\lor",
        "=>": r"\Rightarrow",
        "<=>": r"\Leftrightarrow",
        # Comparison operators (Phase 3)
        "<": r"<",
        ">": r">",
        "<=": r"\leq",
        ">=": r"\geq",
        "=": r"=",
        # Set operators (Phase 3)
        "in": r"\in",
        "subset": r"\subseteq",
        "union": r"\cup",
        "intersect": r"\cap",
    }

    UNARY_OPS: ClassVar[dict[str, str]] = {
        "not": r"\lnot",
    }

    # Quantifier mappings (Phase 3)
    QUANTIFIERS: ClassVar[dict[str, str]] = {
        "forall": r"\forall",
        "exists": r"\exists",
    }

    # Operator precedence (lower number = lower precedence)
    PRECEDENCE: ClassVar[dict[str, int]] = {
        "<=>": 1,  # Lowest precedence
        "=>": 2,
        "or": 3,
        "and": 4,  # Highest precedence (for binary ops)
    }

    def __init__(self, use_fuzz: bool = False) -> None:
        """Initialize generator with package choice."""
        self.use_fuzz = use_fuzz

    def generate_document(self, ast: Document | Expr) -> str:
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

        # Content - handle both Document and single Expr
        if isinstance(ast, Document):
            # Multi-line document: generate each item
            for item in ast.items:
                item_lines = self.generate_document_item(item)
                lines.extend(item_lines)
        else:
            # Single expression (Phase 0 backward compatibility)
            latex_expr = self.generate_expr(ast)
            lines.append(f"${latex_expr}$")
            lines.append("")

        # Postamble
        lines.append(r"\end{document}")

        return "\n".join(lines)

    def generate_document_item(self, item: DocumentItem) -> list[str]:
        """Generate LaTeX lines for a document item."""
        if isinstance(item, Section):
            return self._generate_section(item)
        if isinstance(item, Solution):
            return self._generate_solution(item)
        if isinstance(item, Part):
            return self._generate_part(item)
        if isinstance(item, TruthTable):
            return self._generate_truth_table(item)
        if isinstance(item, EquivChain):
            return self._generate_equiv_chain(item)
        if isinstance(item, GivenType):
            return self._generate_given_type(item)
        if isinstance(item, FreeType):
            return self._generate_free_type(item)
        if isinstance(item, Abbreviation):
            return self._generate_abbreviation(item)
        if isinstance(item, AxDef):
            return self._generate_axdef(item)
        if isinstance(item, Schema):
            return self._generate_schema(item)

        # Item is an Expr - wrap in math mode
        latex_expr = self.generate_expr(item)
        return [f"${latex_expr}$", ""]

    def generate_expr(self, expr: Expr) -> str:
        """Generate LaTeX for expression (without wrapping in math mode)."""
        if isinstance(expr, Identifier):
            return self._generate_identifier(expr)
        if isinstance(expr, Number):
            return self._generate_number(expr)
        if isinstance(expr, UnaryOp):
            return self._generate_unary_op(expr)
        if isinstance(expr, BinaryOp):
            return self._generate_binary_op(expr)
        if isinstance(expr, Quantifier):
            return self._generate_quantifier(expr)
        if isinstance(expr, Subscript):
            return self._generate_subscript(expr)
        if isinstance(expr, Superscript):
            return self._generate_superscript(expr)

        raise TypeError(f"Unknown expression type: {type(expr)}")

    def _generate_identifier(self, node: Identifier) -> str:
        """Generate LaTeX for identifier."""
        return node.name

    def _generate_number(self, node: Number) -> str:
        """Generate LaTeX for number."""
        return node.value

    def _generate_unary_op(self, node: UnaryOp) -> str:
        """Generate LaTeX for unary operation."""
        op_latex = self.UNARY_OPS.get(node.operator)
        if op_latex is None:
            raise ValueError(f"Unknown unary operator: {node.operator}")

        operand = self.generate_expr(node.operand)
        return f"{op_latex} {operand}"

    def _needs_parens(self, child: Expr, parent_op: str) -> bool:
        """Check if child expression needs parentheses in parent context."""
        # Only binary ops need precedence checking
        if not isinstance(child, BinaryOp):
            return False

        child_prec = self.PRECEDENCE.get(child.operator, 999)
        parent_prec = self.PRECEDENCE.get(parent_op, 999)

        # Need parens if child has lower precedence than parent
        return child_prec < parent_prec

    def _generate_binary_op(self, node: BinaryOp) -> str:
        """Generate LaTeX for binary operation."""
        op_latex = self.BINARY_OPS.get(node.operator)
        if op_latex is None:
            raise ValueError(f"Unknown binary operator: {node.operator}")

        left = self.generate_expr(node.left)
        right = self.generate_expr(node.right)

        # Add parentheses if needed for precedence
        if self._needs_parens(node.left, node.operator):
            left = f"({left})"
        if self._needs_parens(node.right, node.operator):
            right = f"({right})"

        return f"{left} {op_latex} {right}"

    def _generate_quantifier(self, node: Quantifier) -> str:
        """Generate LaTeX for quantifier (forall, exists)."""
        quant_latex = self.QUANTIFIERS.get(node.quantifier)
        if quant_latex is None:
            raise ValueError(f"Unknown quantifier: {node.quantifier}")

        # Generate variable and domain
        parts = [quant_latex, node.variable]

        if node.domain:
            domain_latex = self.generate_expr(node.domain)
            parts.append(r"\colon")
            parts.append(domain_latex)

        # Add bullet separator and body
        parts.append(r"\bullet")
        body_latex = self.generate_expr(node.body)
        parts.append(body_latex)

        return " ".join(parts)

    def _generate_subscript(self, node: Subscript) -> str:
        """Generate LaTeX for subscript (a_1, x_i)."""
        base = self.generate_expr(node.base)
        index = self.generate_expr(node.index)

        # Wrap index in braces if it's more than one character
        if len(index) > 1:
            return f"{base}_{{{index}}}"
        return f"{base}_{index}"

    def _generate_superscript(self, node: Superscript) -> str:
        """Generate LaTeX for superscript (x^2, 2^n)."""
        base = self.generate_expr(node.base)
        exponent = self.generate_expr(node.exponent)

        # Wrap exponent in braces if it's more than one character
        if len(exponent) > 1:
            return f"{base}^{{{exponent}}}"
        return f"{base}^{exponent}"

    def _generate_section(self, node: Section) -> list[str]:
        """Generate LaTeX for section."""
        lines: list[str] = []
        lines.append(r"\section*{" + node.title + "}")
        lines.append("")

        for item in node.items:
            item_lines = self.generate_document_item(item)
            lines.extend(item_lines)

        return lines

    def _generate_solution(self, node: Solution) -> list[str]:
        """Generate LaTeX for solution."""
        lines: list[str] = []
        lines.append(r"\bigskip")
        lines.append(r"\noindent")
        lines.append(r"\textbf{" + node.number + "}")
        lines.append("")

        for item in node.items:
            item_lines = self.generate_document_item(item)
            lines.extend(item_lines)

        return lines

    def _generate_part(self, node: Part) -> list[str]:
        """Generate LaTeX for part label."""
        lines: list[str] = []
        lines.append(f"({node.label})")

        for item in node.items:
            item_lines = self.generate_document_item(item)
            lines.extend(item_lines)

        lines.append(r"\medskip")
        lines.append("")

        return lines

    def _generate_truth_table(self, node: TruthTable) -> list[str]:
        """Generate LaTeX for truth table."""
        lines: list[str] = []

        # Start table environment
        num_cols = len(node.headers)
        col_spec = "|".join(["c"] * num_cols)
        lines.append(r"\begin{center}")
        lines.append(r"\begin{tabular}{|" + col_spec + r"|}")

        # Generate header row
        header_parts: list[str] = []
        for header in node.headers:
            # Wrap header in math mode
            header_parts.append(f"${header}$")
        lines.append(" & ".join(header_parts) + r" \\")
        lines.append(r"\hline")

        # Generate data rows
        for row in node.rows:
            lines.append(" & ".join(row) + r" \\")

        lines.append(r"\end{tabular}")
        lines.append(r"\end{center}")
        lines.append("")

        return lines

    def _escape_justification(self, text: str) -> str:
        """Escape operators in justification text for LaTeX."""
        # Replace operators with LaTeX commands using word boundaries
        # Order matters: replace longer operators first
        result = text.replace("<=>", r"$\Leftrightarrow$")
        result = result.replace("=>", r"$\Rightarrow$")
        result = re.sub(r"\band\b", r"$\\land$", result)
        result = re.sub(r"\bor\b", r"$\\lor$", result)
        result = re.sub(r"\bnot\b", r"$\\lnot$", result)
        return result

    def _generate_equiv_chain(self, node: EquivChain) -> list[str]:
        """Generate LaTeX for equivalence chain using align* environment."""
        lines: list[str] = []

        lines.append(r"\begin{align*}")

        # Generate steps
        for i, step in enumerate(node.steps):
            expr_latex = self.generate_expr(step.expression)

            # First step: just expression; subsequent: &\Leftrightarrow expression
            line = expr_latex if i == 0 else r"&\Leftrightarrow " + expr_latex

            # Add justification if present
            if step.justification:
                escaped_just = self._escape_justification(step.justification)
                line += r" && \text{[" + escaped_just + "]}"

            # Add line break except for last line
            if i < len(node.steps) - 1:
                line += r" \\"

            lines.append(line)

        lines.append(r"\end{align*}")
        lines.append("")

        return lines

    def _generate_given_type(self, node: GivenType) -> list[str]:
        """Generate LaTeX for given type declaration."""
        lines: list[str] = []
        # Generate as: given [A, B, C]
        names_str = ", ".join(node.names)
        lines.append(f"\\begin{{zed}}[{names_str}]\\end{{zed}}")
        lines.append("")
        return lines

    def _generate_free_type(self, node: FreeType) -> list[str]:
        """Generate LaTeX for free type definition."""
        lines: list[str] = []
        # Generate as: Type ::= branch1 | branch2 | ...
        branches_str = " | ".join(node.branches)
        lines.append(f"{node.name} ::= {branches_str}")
        lines.append("")
        return lines

    def _generate_abbreviation(self, node: Abbreviation) -> list[str]:
        """Generate LaTeX for abbreviation definition."""
        lines: list[str] = []
        expr_latex = self.generate_expr(node.expression)
        lines.append(f"{node.name} == {expr_latex}")
        lines.append("")
        return lines

    def _generate_axdef(self, node: AxDef) -> list[str]:
        """Generate LaTeX for axiomatic definition."""
        lines: list[str] = []

        lines.append(r"\begin{axdef}")

        # Generate declarations
        for decl in node.declarations:
            type_latex = self.generate_expr(decl.type_expr)
            lines.append(f"{decl.variable} : {type_latex}")

        # Generate where clause if predicates exist
        if node.predicates:
            lines.append(r"\where")
            for pred in node.predicates:
                pred_latex = self.generate_expr(pred)
                lines.append(pred_latex)

        lines.append(r"\end{axdef}")
        lines.append("")

        return lines

    def _generate_schema(self, node: Schema) -> list[str]:
        """Generate LaTeX for schema definition."""
        lines: list[str] = []

        lines.append(r"\begin{schema}{" + node.name + "}")

        # Generate declarations
        for decl in node.declarations:
            type_latex = self.generate_expr(decl.type_expr)
            lines.append(f"{decl.variable} : {type_latex}")

        # Generate where clause if predicates exist
        if node.predicates:
            lines.append(r"\where")
            for pred in node.predicates:
                pred_latex = self.generate_expr(pred)
                lines.append(pred_latex)

        lines.append(r"\end{schema}")
        lines.append("")

        return lines
