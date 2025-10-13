"""LaTeX generator for txt2tex - converts AST to LaTeX."""

from __future__ import annotations

import re
from typing import ClassVar

from txt2tex.ast_nodes import (
    Abbreviation,
    AxDef,
    BinaryOp,
    CaseAnalysis,
    Document,
    DocumentItem,
    EquivChain,
    Expr,
    FreeType,
    GivenType,
    Identifier,
    Number,
    Paragraph,
    Part,
    ProofNode,
    ProofTree,
    Quantifier,
    Schema,
    Section,
    SetComprehension,
    Solution,
    Subscript,
    Superscript,
    TruthTable,
    UnaryOp,
)
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser


class LaTeXGenerator:
    """Generates LaTeX from AST for Phase 0-4 + Phase 10a.

    Phase 10a: Supports relation operators (<->, |->, <|, |>, comp, ;)
    and relation functions (dom, ran).
    """

    # Operator mappings
    BINARY_OPS: ClassVar[dict[str, str]] = {
        # Propositional logic
        "and": r"\land",
        "or": r"\lor",
        "=>": r"\Rightarrow",
        "<=>": r"\Leftrightarrow",
        # Comparison operators (Phase 3, enhanced in Phase 7)
        "<": r"<",
        ">": r">",
        "<=": r"\leq",
        ">=": r"\geq",
        "=": r"=",
        "!=": r"\neq",
        # Set operators (Phase 3, enhanced in Phase 7)
        "in": r"\in",
        "notin": r"\notin",
        "subset": r"\subseteq",
        "union": r"\cup",
        "intersect": r"\cap",
        # Relation operators (Phase 10a)
        "<->": r"\rel",  # Relation type
        "|->": r"\mapsto",  # Maplet constructor
        "<|": r"\dres",  # Domain restriction
        "|>": r"\rres",  # Range restriction
        "comp": r"\comp",  # Relational composition
        ";": r"\semi",  # Relational composition (semicolon)
    }

    UNARY_OPS: ClassVar[dict[str, str]] = {
        "not": r"\lnot",
        # Relation functions (Phase 10a)
        "dom": r"\dom",  # Domain of relation
        "ran": r"\ran",  # Range of relation
    }

    # Quantifier mappings (Phase 3, enhanced in Phase 6-7)
    QUANTIFIERS: ClassVar[dict[str, str]] = {
        "forall": r"\forall",
        "exists": r"\exists",
        "exists1": r"\exists_1",  # Unique existence quantifier
        "mu": r"\mu",  # Definite description (mu-operator)
    }

    # Operator precedence (lower number = lower precedence)
    PRECEDENCE: ClassVar[dict[str, int]] = {
        "<=>": 1,  # Lowest precedence
        "=>": 2,
        "or": 3,
        "and": 4,
        # Comparison operators
        "<": 5,
        ">": 5,
        "<=": 5,
        ">=": 5,
        "=": 5,
        "!=": 5,
        # Relation operators (Phase 10a) - between comparison and set ops
        "<->": 6,
        "|->": 6,
        "<|": 6,
        "|>": 6,
        "comp": 6,
        ";": 6,
        # Set operators - highest precedence
        "in": 7,
        "notin": 7,
        "subset": 7,
        "union": 8,
        "intersect": 9,  # Highest precedence (for binary ops)
    }

    # Right-associative operators (need parens on left when same operator)
    # Implication and equivalence are right-associative
    RIGHT_ASSOCIATIVE: ClassVar[set[str]] = {"=>", "<=>"}

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
            lines.append(r"\usepackage{zed-proof}")  # For \infer macros
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
        if isinstance(item, Paragraph):
            return self._generate_paragraph(item)
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
        if isinstance(item, ProofTree):
            return self._generate_proof_tree(item)

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
        if isinstance(expr, SetComprehension):
            return self._generate_set_comprehension(expr)

        raise TypeError(f"Unknown expression type: {type(expr)}")

    def _generate_identifier(self, node: Identifier) -> str:
        """Generate LaTeX for identifier."""
        return node.name

    def _generate_number(self, node: Number) -> str:
        """Generate LaTeX for number."""
        return node.value

    def _generate_unary_op(self, node: UnaryOp) -> str:
        """Generate LaTeX for unary operation.

        Unary operators have higher precedence than all binary operators,
        so parentheses are added around binary operator operands.
        """
        op_latex = self.UNARY_OPS.get(node.operator)
        if op_latex is None:
            raise ValueError(f"Unknown unary operator: {node.operator}")

        operand = self.generate_expr(node.operand)

        # Add parentheses if operand is a binary operator
        # (unary has higher precedence than all binary operators)
        if isinstance(node.operand, BinaryOp):
            operand = f"({operand})"

        return f"{op_latex} {operand}"

    def _needs_parens(self, child: Expr, parent_op: str, is_left_child: bool) -> bool:
        """Check if child expression needs parentheses in parent context.

        Args:
            child: The child expression to check
            parent_op: The parent operator
            is_left_child: True if this is the left child, False if right

        Returns:
            True if parentheses are needed
        """
        # Only binary ops need precedence checking
        if not isinstance(child, BinaryOp):
            return False

        child_prec = self.PRECEDENCE.get(child.operator, 999)
        parent_prec = self.PRECEDENCE.get(parent_op, 999)

        # Need parens if child has lower precedence than parent
        if child_prec < parent_prec:
            return True

        # If same precedence, check associativity
        if child_prec == parent_prec and child.operator == parent_op:
            # For clarity in proofs, always add parentheses for nested
            # implications or equivalences (even if technically not required
            # by associativity)
            if parent_op in {"=>", "<=>"}:
                return True

            # For right-associative operators (general case), left child needs parens
            if parent_op in self.RIGHT_ASSOCIATIVE and is_left_child:
                return True
            # For left-associative operators, right child needs parens
            # Note: and/or are associative so they don't need parens

        return False

    def _generate_binary_op(self, node: BinaryOp) -> str:
        """Generate LaTeX for binary operation."""
        op_latex = self.BINARY_OPS.get(node.operator)
        if op_latex is None:
            raise ValueError(f"Unknown binary operator: {node.operator}")

        left = self.generate_expr(node.left)
        right = self.generate_expr(node.right)

        # Add parentheses if needed for precedence and associativity
        if self._needs_parens(node.left, node.operator, is_left_child=True):
            left = f"({left})"
        if self._needs_parens(node.right, node.operator, is_left_child=False):
            right = f"({right})"

        return f"{left} {op_latex} {right}"

    def _generate_quantifier(self, node: Quantifier) -> str:
        """Generate LaTeX for quantifier (forall, exists, exists1, mu).

        Phase 6 enhancement: Supports multiple variables.
        Phase 7 enhancement: Supports mu-operator (definite description).
        Examples:
        - forall x : N | pred -> \\forall x \\colon N \\bullet pred
        - forall x, y : N | pred -> \\forall x, y \\colon N \\bullet pred
        - exists1 x : N | pred -> \\exists_1 x \\colon N \\bullet pred
        - mu x : N | pred -> \\mu x \\colon N \\bullet pred
        """
        quant_latex = self.QUANTIFIERS.get(node.quantifier)
        if quant_latex is None:
            raise ValueError(f"Unknown quantifier: {node.quantifier}")

        # Generate variables (comma-separated for multi-variable quantifiers)
        variables_str = ", ".join(node.variables)
        parts = [quant_latex, variables_str]

        if node.domain:
            domain_latex = self.generate_expr(node.domain)
            parts.append(r"\colon")
            parts.append(domain_latex)

        # Add bullet separator and body
        parts.append(r"\bullet")
        body_latex = self.generate_expr(node.body)
        parts.append(body_latex)

        return " ".join(parts)

    def _generate_set_comprehension(self, node: SetComprehension) -> str:
        """Generate LaTeX for set comprehension (Phase 8).

        Supports two forms:
        - Set by predicate: { x : X | predicate }
          -> \\{ x \\colon X \\mid predicate \\}
        - Set by expression: { x : X | pred . expr }
          -> \\{ x \\colon X \\mid pred \\bullet expr \\}

        Examples:
        - { x : N | x > 0 }
          -> \\{ x \\colon \\mathbb{N} \\mid x > 0 \\}
        - { x : N | x > 0 . x^2 }
          -> \\{ x \\colon \\mathbb{N} \\mid x > 0 \\bullet x^{2} \\}
        - { x, y : N | x + y = 4 }
          -> \\{ x, y \\colon \\mathbb{N} \\mid x + y = 4 \\}
        """
        # Generate variables (comma-separated for multi-variable)
        variables_str = ", ".join(node.variables)
        parts = [r"\{", variables_str]

        if node.domain:
            domain_latex = self.generate_expr(node.domain)
            parts.append(r"\colon")
            parts.append(domain_latex)

        # Add mid separator
        parts.append(r"\mid")

        # Generate predicate
        predicate_latex = self.generate_expr(node.predicate)
        parts.append(predicate_latex)

        # If expression is present, add bullet and expression
        if node.expression:
            parts.append(r"\bullet")
            expression_latex = self.generate_expr(node.expression)
            parts.append(expression_latex)

        # Close set
        parts.append(r"\}")

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
        lines.append(r"\medskip")  # Add vertical space before content
        lines.append("")

        for item in node.items:
            item_lines = self.generate_document_item(item)
            lines.extend(item_lines)

        return lines

    def _generate_part(self, node: Part) -> list[str]:
        """Generate LaTeX for part label."""
        lines: list[str] = []
        lines.append(f"({node.label})")
        lines.append(r"\par")  # End paragraph cleanly
        lines.append(r"\vspace{11pt}")  # Explicit spacing for all content types

        for item in node.items:
            item_lines = self.generate_document_item(item)
            lines.extend(item_lines)

        lines.append(r"\medskip")
        lines.append("")

        return lines

    def _generate_paragraph(self, node: Paragraph) -> list[str]:
        """Generate LaTeX for plain text paragraph.

        Converts symbolic operators like <=> and => to LaTeX math symbols.
        Supports inline math expressions like { x : N | x > 0 }.
        Does NOT convert words like 'and', 'or', 'not' - these are English prose.
        """
        lines: list[str] = []
        lines.append(r"\bigskip")  # Leading vertical space (larger than medskip)
        lines.append("")

        # Process inline math expressions first
        text = self._process_inline_math(node.text)

        # Then convert remaining symbolic operators to LaTeX math symbols
        # Do NOT convert and/or/not - those are English words in prose context
        text = text.replace("<=>", r"$\Leftrightarrow$")
        text = text.replace("=>", r"$\Rightarrow$")

        lines.append(text)
        lines.append("")
        lines.append(r"\bigskip")  # Trailing vertical space
        lines.append("")
        return lines

    def _process_inline_math(self, text: str) -> str:
        """Process inline math expressions in text.

        Detects patterns like:
        - Set comprehensions: { x : N | x > 0 }
        - Quantifiers: forall x : N | predicate

        Parses them and converts to $...$ wrapped LaTeX.
        """
        result = text

        # Pattern 1: Set comprehensions { ... }
        # Find balanced braces and try to parse as set comprehension
        brace_pattern = r"\{[^{}]+\}"
        matches = list(re.finditer(brace_pattern, text))

        # Process matches in reverse order to preserve positions
        for match in reversed(matches):
            math_text = match.group(0)
            try:
                # Try to parse as math expression
                lexer = Lexer(math_text)
                tokens = lexer.tokenize()
                parser = Parser(tokens)
                ast = parser.parse()

                # Check if it's a single expression (not a document)
                if isinstance(ast, SetComprehension):
                    # Generate LaTeX for the expression
                    math_latex = self.generate_expr(ast)
                    # Wrap in $...$
                    result = (
                        result[: match.start()]
                        + f"${math_latex}$"
                        + result[match.end() :]
                    )
            except Exception:
                # If parsing fails, leave as-is (might be prose)
                pass

        # Pattern 2: Quantifiers (forall, exists, exists1, mu)
        # Strategy: Find keyword, then try parsing increasingly longer substrings
        quant_keywords = ["forall", "exists", "exists1", "mu"]
        for keyword in quant_keywords:
            # Find all occurrences of quantifier keywords
            pattern = rf"\b{keyword}\b"
            matches = list(re.finditer(pattern, result))

            # Process matches in reverse order to preserve positions
            for match in reversed(matches):
                start_pos = match.start()

                # Try to parse increasingly longer substrings from this point
                # Stop at sentence boundaries or when parsing fails
                for end_offset in range(
                    len(result) - start_pos, 0, -1
                ):  # Try longest first
                    end_pos = start_pos + end_offset
                    # Don't go past sentence boundaries
                    if any(
                        result[start_pos:end_pos].count(boundary) > 0
                        for boundary in [". ", "! ", "? "]
                    ):
                        # Found a sentence boundary - try up to that point
                        for boundary in [". ", "! ", "? "]:
                            if boundary in result[start_pos:end_pos]:
                                end_pos = start_pos + result[start_pos:end_pos].index(
                                    boundary
                                )
                                break

                    math_text = result[start_pos:end_pos].strip()

                    # Must contain a pipe for quantifier syntax
                    if "|" not in math_text:
                        continue

                    try:
                        # Try to parse as quantifier
                        lexer = Lexer(math_text)
                        tokens = lexer.tokenize()
                        parser = Parser(tokens)
                        ast = parser.parse()

                        if isinstance(ast, Quantifier):
                            # Successfully parsed! Generate LaTeX
                            math_latex = self.generate_expr(ast)
                            # Wrap in $...$
                            result = (
                                result[:start_pos]
                                + f"${math_latex}$"
                                + result[end_pos:]
                            )
                            break  # Move to next match
                    except Exception:
                        # Try shorter substring
                        continue

        return result

    def _generate_truth_table(self, node: TruthTable) -> list[str]:
        """Generate LaTeX for truth table."""
        lines: list[str] = []

        # Start table environment (no vertical bars, only horizontal line after header)
        # Spacing is controlled by part labels
        num_cols = len(node.headers)
        col_spec = " ".join(["c"] * num_cols)
        lines.append(r"\begin{center}")
        lines.append(r"\begin{tabular}{" + col_spec + r"}")

        # Generate header row
        header_parts: list[str] = []
        for header in node.headers:
            # Convert operators to LaTeX symbols
            header_latex = self._convert_operators_to_latex(header)
            # Wrap header in math mode
            header_parts.append(f"${header_latex}$")
        lines.append(" & ".join(header_parts) + r" \\")
        lines.append(r"\hline")

        # Generate data rows (lowercase t/f in text mode, not math mode)
        for row in node.rows:
            # Don't wrap truth values in math mode - use text mode for lowercase t/f
            row_parts = [val.lower() if val in ("T", "F") else val for val in row]
            lines.append(" & ".join(row_parts) + r" \\")

        lines.append(r"\end{tabular}")
        lines.append(r"\end{center}")
        lines.append("")

        return lines

    def _convert_operators_to_latex(self, text: str) -> str:
        """Convert operator keywords to LaTeX symbols in text."""
        # Replace operators with LaTeX commands using word boundaries
        # Order matters: replace longer operators first
        result = text.replace("<=>", r"\Leftrightarrow")
        result = result.replace("=>", r"\Rightarrow")
        result = re.sub(r"\band\b", r"\\land", result)
        result = re.sub(r"\bor\b", r"\\lor", result)
        result = re.sub(r"\bnot\b", r"\\lnot", result)
        return result

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

        # Compensate for align* automatic spacing (adds ~10px extra)
        lines.append(r"\vspace{-10pt}")
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
        """Generate LaTeX for abbreviation definition.

        Phase 9 enhancement: Supports optional generic parameters.
        """
        lines: list[str] = []
        expr_latex = self.generate_expr(node.expression)

        # Add generic parameters if present
        if node.generic_params:
            params_str = ", ".join(node.generic_params)
            lines.append(f"[{params_str}] {node.name} == {expr_latex}")
        else:
            lines.append(f"{node.name} == {expr_latex}")

        lines.append("")
        return lines

    def _generate_axdef(self, node: AxDef) -> list[str]:
        """Generate LaTeX for axiomatic definition.

        Phase 9 enhancement: Supports optional generic parameters.
        """
        lines: list[str] = []

        # Add generic parameters if present
        if node.generic_params:
            params_str = ", ".join(node.generic_params)
            lines.append(f"\\begin{{axdef}}[{params_str}]")
        else:
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
        """Generate LaTeX for schema definition.

        Phase 9 enhancement: Supports optional generic parameters.
        """
        lines: list[str] = []

        # Add generic parameters if present
        if node.generic_params:
            params_str = ", ".join(node.generic_params)
            lines.append(f"\\begin{{schema}}{{{node.name}}}[{params_str}]")
        else:
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

    def _generate_proof_tree(self, node: ProofTree) -> list[str]:
        """Generate LaTeX for proof tree using \\infer macros from zed-proof.sty."""
        lines: list[str] = []

        # Generate the proof tree left-aligned using \noindent and display math mode
        # Spacing is controlled by part labels (no additional spacing needed)
        proof_latex = self._generate_proof_node_infer(node.conclusion)
        lines.append(r"\noindent")
        lines.append(r"\[")
        lines.append(proof_latex)
        lines.append(r"\]")
        lines.append("")

        return lines

    def _format_boxed_assumption(self, expr: Expr, label: int | None) -> str:
        """Generate boxed assumption with corner brackets ⌈expr⌉[n]."""
        expr_latex = self.generate_expr(expr)
        # Use \ulcorner and \urcorner for corner brackets (requires amsmath)
        if label is not None:
            return f"\\ulcorner {expr_latex} \\urcorner^{{[{label}]}}"
        return f"\\ulcorner {expr_latex} \\urcorner"

    def _calculate_tree_depth(self, node: ProofNode | CaseAnalysis) -> int:
        """Calculate the depth of a proof tree (number of inference levels)."""
        if isinstance(node, CaseAnalysis):
            if not node.steps:
                return 0

            # For case analysis, count sequential steps (not just nested depth)
            # Sequential steps stack vertically, increasing height
            sibling_count = 0
            sequential_count = 0

            for step in node.steps:
                if step.is_sibling:
                    if sequential_count == 0:
                        sibling_count += 1
                    else:
                        # Sibling after sequential - treat as sequential
                        sequential_count += 1
                else:
                    sequential_count += 1

            # Height is based on sequential steps + 1 for sibling layer (if any)
            # Plus the depth of any nested children
            sibling_layer = 1 if sibling_count > 0 else 0
            max_child_depth = max(
                (self._calculate_tree_depth(step) for step in node.steps), default=0
            )

            return sibling_layer + sequential_count + max_child_depth

        if not node.children:
            return 0

        return 1 + max(self._calculate_tree_depth(child) for child in node.children)

    def _generate_proof_node_infer(self, node: ProofNode) -> str:
        """
        Generate \\infer macro for a proof node (bottom-up natural deduction).

        Returns LaTeX string for this node and its supporting premises.
        """
        # If this is an assumption node, it should appear as a boxed premise
        if node.is_assumption:
            # The assumption itself is a premise (leaf)
            assumption_latex = self._format_boxed_assumption(
                node.expression, node.label
            )

            # If it has children, they are derivations from this assumption
            # The assumption should be the base of the tree
            if not node.children:
                return assumption_latex

            # For now, treat the first child as the main derivation from the
            # assumption. This is a simplified approach - full natural deduction
            # requires dependency analysis.
            if len(node.children) == 1 and isinstance(node.children[0], ProofNode):
                single_child = node.children[0]
                # Generate child with assumption as its premise
                return self._generate_inference_from_assumption(
                    single_child, assumption_latex, node.label
                )

            # Multiple children or case analysis - need special handling
            return self._generate_complex_assumption_scope(node, assumption_latex)

        # Generate expression for conclusion
        expr_latex = self.generate_expr(node.expression)

        # If no children, return expression (possibly with justification)
        if not node.children:
            # Check if justification indicates a reference (not a derivation rule)
            if node.justification:
                just_lower = node.justification.lower()
                # References like "from 1", "copy", etc. should not be wrapped in \infer
                # They're just referencing an existing fact
                if "from" in just_lower or "copy" in just_lower:
                    # Extract assumption label if present (e.g., "from 1" -> "1")
                    from_match = re.search(r"from\s+(\d+)", just_lower)
                    if from_match:
                        ref_label = from_match.group(1)
                        # Render as boxed assumption reference
                        return f"\\ulcorner {expr_latex} \\urcorner^{{[{ref_label}]}}"
                    # Just return the expression - it's a reference without label
                    return expr_latex
                # Otherwise it's a derivation rule, wrap in \infer
                just = self._format_justification_label(node.justification)
                return f"\\infer[{just}]{{{expr_latex}}}{{}}"
            return expr_latex

        # Group children by siblings
        # Siblings (marked with ::) should be rendered side-by-side with &
        child_groups: list[list[str]] = []
        current_group: list[str] = []
        # Track case analysis with indices for raiseproof handling
        case_children: list[tuple[int, CaseAnalysis]] = []

        for idx, child in enumerate(node.children):
            if isinstance(child, CaseAnalysis):
                # Track case analysis for raiseproof handling
                case_children.append((idx, child))
                # Close current group before case
                if current_group:
                    child_groups.append(current_group)
                    current_group = []
            elif isinstance(child, ProofNode):
                # Regular proof node
                child_latex = self._generate_proof_node_infer(child)

                if child.is_sibling and current_group:
                    # Add to current sibling group
                    current_group.append(child_latex)
                else:
                    # Start new group
                    if current_group:
                        child_groups.append(current_group)
                    current_group = [child_latex]

        # Add last group
        if current_group:
            child_groups.append(current_group)

        # Generate premises by joining siblings with &
        non_case_premises = [" & ".join(group) for group in child_groups]

        # If we have case analysis, apply raiseproof for vertical layout
        if case_children:
            # Identify disjunction siblings (for or-elim)
            disjunction_premises = []
            for group in child_groups:
                for premise in group:
                    # Check if this is a disjunction (contains \lor)
                    if r"\lor" in premise:
                        disjunction_premises.append(premise)

            # Generate raised cases with staggered heights
            raised_cases = []
            for case_position, (_idx, case) in enumerate(case_children):
                case_latex = self._generate_case_analysis(case)
                depth = self._calculate_tree_depth(case)

                # STAGGERED HEIGHT FORMULA:
                # First case: 6-8ex (minimal)
                # Subsequent cases: 18-24ex (much taller to avoid overlap)
                if case_position == 0:
                    # First case: minimal height
                    height = 6 + (depth * 2)  # Conservative for first case
                    raised = f"\\raiseproof{{{height}ex}}{{{case_latex}}}"
                else:
                    # Subsequent cases: taller + horizontal spacing
                    height = 18 + (depth * 4)  # Much taller for subsequent cases
                    raised = f"\\hskip 6em \\raiseproof{{{height}ex}}{{{case_latex}}}"

                raised_cases.append(raised)

            # Combine: disjunction premises first (if any), then raised case branches
            if disjunction_premises:
                all_premises = disjunction_premises + raised_cases
            else:
                # No disjunction - might be other premises before cases
                all_premises = non_case_premises + raised_cases

            premises = " & ".join(all_premises)
        else:
            # No case analysis - use normal premises
            premises = "\n  ".join(non_case_premises)

        # Generate justification label
        if node.justification:
            # Escape LaTeX special characters in justification
            just = self._format_justification_label(node.justification)
            return f"\\infer[{just}]{{{expr_latex}}}{{\n  {premises}\n}}"
        else:
            # No justification - use plain \infer
            return f"\\infer{{{expr_latex}}}{{\n  {premises}\n}}"

    def _generate_inference_from_assumption(
        self, node: ProofNode, assumption_latex: str, assumption_label: int | None
    ) -> str:
        """Generate an inference that derives from a boxed assumption."""
        expr_latex = self.generate_expr(node.expression)

        # If this node has no children, it directly derives from the assumption
        if not node.children:
            if node.justification:
                just = self._format_justification_label(node.justification)
                return f"\\infer[{just}]{{{expr_latex}}}{{{assumption_latex}}}"
            return f"\\infer{{{expr_latex}}}{{{assumption_latex}}}"

        # Node has children - generate them recursively
        # Children should ultimately reference the assumption as their premise
        child_latex = self._generate_proof_node_infer_with_assumption(
            node, assumption_latex, assumption_label
        )
        return child_latex

    def _generate_proof_node_infer_with_assumption(
        self, node: ProofNode, assumption_latex: str, assumption_label: int | None
    ) -> str:
        """Generate inference node with leaves referencing the given assumption."""
        expr_latex = self.generate_expr(node.expression)

        # Base case: no children means this should derive from the assumption
        if not node.children:
            if node.justification:
                just_lower = node.justification.lower()
                # References like "from 1", "copy", etc. should not be wrapped in \infer
                if "from" in just_lower or "copy" in just_lower:
                    # Extract assumption label if present (e.g., "from 1" -> "1")
                    from_match = re.search(r"from\s+(\d+)", just_lower)
                    if from_match:
                        ref_label = from_match.group(1)
                        # Render as boxed assumption reference
                        return f"\\ulcorner {expr_latex} \\urcorner^{{[{ref_label}]}}"
                    # Just return the expression - it's a reference without label
                    return expr_latex
                # Otherwise it's a derivation rule
                just = self._format_justification_label(node.justification)
                return f"\\infer[{just}]{{{expr_latex}}}{{{assumption_latex}}}"
            return expr_latex

        # Process children
        premises: list[str] = []
        for child in node.children:
            if isinstance(child, CaseAnalysis):
                premises.append(self._generate_case_analysis(child))
            elif child.is_assumption:
                # Child is its own assumption - process independently
                child_latex = self._generate_proof_node_infer(child)
                premises.append(child_latex)
            else:
                child_latex = self._generate_proof_node_infer_with_assumption(
                    child, assumption_latex, assumption_label
                )
                premises.append(child_latex)

        # Join premises
        premises_str = " & ".join(premises) if premises else assumption_latex

        # Generate with justification
        if node.justification:
            just = self._format_justification_label(node.justification)
            return f"\\infer[{just}]{{{expr_latex}}}{{{premises_str}}}"
        return f"\\infer{{{expr_latex}}}{{{premises_str}}}"

    def _generate_complex_assumption_scope(
        self, assumption_node: ProofNode, assumption_latex: str
    ) -> str:
        """Handle complex assumption scopes with multiple children or case analysis."""
        # Group children into sibling groups and sequential derivations
        # Siblings (marked with ::) are horizontal, non-siblings nest vertically

        children = assumption_node.children
        if not children:
            return assumption_latex

        # Separate siblings from sequential derivations
        sibling_group: list[ProofNode | CaseAnalysis] = []
        sequential: list[ProofNode | CaseAnalysis] = []

        for child in children:
            if isinstance(child, CaseAnalysis):
                # Case analysis can appear in sibling position
                if not sequential:
                    sibling_group.append(child)
                else:
                    sequential.append(child)
            elif child.is_sibling:
                # Only add to sibling group if we haven't started sequential yet
                if not sequential:
                    sibling_group.append(child)
                else:
                    # Sibling after non-sibling - this is a new context
                    sequential.append(child)
            else:
                # Non-sibling - starts sequential derivations
                sequential.append(child)

        # Generate sibling group (derives directly from assumption)
        sibling_latex_parts: list[str] = []
        for child in sibling_group:
            if isinstance(child, CaseAnalysis):
                sibling_latex_parts.append(self._generate_case_analysis(child))
            else:
                child_latex = self._generate_proof_node_infer_with_assumption(
                    child, assumption_latex, assumption_node.label
                )
                sibling_latex_parts.append(child_latex)

        # Combine siblings horizontally with &
        if sibling_latex_parts:
            current_premises = " & ".join(sibling_latex_parts)
        else:
            current_premises = assumption_latex

        # Now build sequential derivations vertically on top
        # Each sequential step uses the previous result as its premise
        for child in sequential:
            if isinstance(child, CaseAnalysis):
                child_latex = self._generate_case_analysis(child)
            else:
                # Generate the child
                # If it has children, we need to process them recursively
                if child.children:
                    # This node has children - need to generate a full subtree
                    # The subtree should use current_premises as its base
                    expr_latex = self.generate_expr(child.expression)

                    # Generate children
                    child_premises_parts: list[str] = []
                    has_case_analysis = False
                    for grandchild in child.children:
                        if isinstance(grandchild, CaseAnalysis):
                            child_premises_parts.append(
                                self._generate_case_analysis(grandchild)
                            )
                            has_case_analysis = True
                        else:
                            # Recurse to handle nested structure
                            grandchild_latex = self._generate_proof_node_infer(
                                grandchild
                            )
                            child_premises_parts.append(grandchild_latex)

                    # Include siblings from parent scope as additional premises.
                    # Special case: for or-elim with case analysis, only include
                    # disjunction siblings. Other siblings (like extracted
                    # conjuncts) are handled within case branches.
                    if sibling_latex_parts and child_premises_parts:
                        if has_case_analysis:
                            # Only include disjunction siblings as top-level
                            # premises for or-elim
                            disjunction_siblings = []
                            for i, sib_child in enumerate(sibling_group):
                                if (
                                    isinstance(sib_child, ProofNode)
                                    and isinstance(sib_child.expression, BinaryOp)
                                    and sib_child.expression.operator == "or"
                                ):
                                    disjunction_siblings.append(sibling_latex_parts[i])

                            # Apply \raiseproof to case branches for vertical
                            # layout. STAGGERED STRATEGY: Different cases get
                            # different heights + horizontal spacing
                            raised_cases = []

                            # Collect all case indices first
                            case_indices = []
                            for idx, grandchild in enumerate(child.children):
                                if isinstance(grandchild, CaseAnalysis):
                                    case_indices.append(idx)

                            # Generate raised cases with staggered heights
                            for case_position, idx in enumerate(case_indices):
                                grandchild = child.children[idx]
                                depth = self._calculate_tree_depth(grandchild)
                                case_latex = child_premises_parts[idx]

                                # STAGGERED HEIGHT FORMULA:
                                # First case: 6-8ex (minimal)
                                # Subsequent cases: 18-24ex (much taller to
                                # avoid overlap)
                                if case_position == 0:
                                    # First case: minimal height
                                    height = 6 + (
                                        depth * 2
                                    )  # Conservative for first case
                                    raised = (
                                        f"\\raiseproof{{{height}ex}}{{{case_latex}}}"
                                    )
                                else:
                                    # Subsequent cases: taller + horizontal
                                    # spacing
                                    height = 18 + (
                                        depth * 4
                                    )  # Much taller for subsequent cases
                                    raised = (
                                        f"\\hskip 6em "
                                        f"\\raiseproof{{{height}ex}}"
                                        f"{{{case_latex}}}"
                                    )

                                raised_cases.append(raised)

                            # Combine: disjunction siblings first, then raised
                            # case branches
                            all_premises = disjunction_siblings + raised_cases
                            child_premises = " & ".join(all_premises)
                        else:
                            # Not case analysis - include all siblings
                            all_premises = sibling_latex_parts + child_premises_parts
                            child_premises = " & ".join(all_premises)
                    elif child_premises_parts:
                        child_premises = " & ".join(child_premises_parts)
                    else:
                        child_premises = current_premises

                    if child.justification:
                        just = self._format_justification_label(child.justification)
                        child_latex = (
                            f"\\infer[{just}]{{{expr_latex}}}{{{child_premises}}}"
                        )
                    else:
                        child_latex = f"\\infer{{{expr_latex}}}{{{child_premises}}}"
                else:
                    # No children - derive directly from current_premises
                    expr_latex = self.generate_expr(child.expression)

                    if child.justification:
                        just = self._format_justification_label(child.justification)
                        child_latex = (
                            f"\\infer[{just}]{{{expr_latex}}}{{{current_premises}}}"
                        )
                    else:
                        child_latex = f"\\infer{{{expr_latex}}}{{{current_premises}}}"

            # This becomes the new premise for next step
            current_premises = child_latex

        return current_premises

    def _generate_case_analysis(self, case: CaseAnalysis) -> str:
        """Generate LaTeX for case analysis branch."""
        # For each case, generate the proof steps
        # Cases are typically rendered as separate inference branches
        if not case.steps:
            return f"\\text{{case {case.case_name}}}"

        # Generate the first step (usually the conclusion of this case)
        # In many cases, there's just one step per case
        if len(case.steps) == 1:
            return self._generate_proof_node_infer(case.steps[0])

        # Multiple steps - need to group siblings horizontally, rest vertically
        # Separate siblings from sequential steps
        sibling_group: list[ProofNode] = []
        sequential: list[ProofNode] = []

        for step in case.steps:
            if step.is_sibling:
                # Only add to sibling group if we haven't started sequential yet
                if not sequential:
                    sibling_group.append(step)
                else:
                    sequential.append(step)
            else:
                # Non-sibling - starts sequential derivations
                sequential.append(step)

        # Generate sibling group (horizontal with &)
        if sibling_group:
            sibling_parts = [self._generate_proof_node_infer(s) for s in sibling_group]
            current_result = " & ".join(sibling_parts)
        else:
            # No siblings, start with first sequential
            if not sequential:
                return ""
            current_result = self._generate_proof_node_infer(sequential[0])
            sequential = sequential[1:]

        # Build sequential steps vertically on top
        for step in sequential:
            expr_latex = self.generate_expr(step.expression)

            if step.justification:
                just = self._format_justification_label(step.justification)
                current_result = f"\\infer[{just}]{{{expr_latex}}}{{{current_result}}}"
            else:
                current_result = f"\\infer{{{expr_latex}}}{{{current_result}}}"

        return current_result

    def _format_justification_label(self, just: str) -> str:
        """
        Format justification text for \\infer label.

        Converts patterns:
        - "=> intro from 1" → "$\\Rightarrow$-intro^{[1]}" (discharge superscript)
        - "and elim 1" → "$\\land$-elim-1" (left/right projection, regular text)
        - "or intro 2" → "$\\lor$-intro-2" (left/right injection, regular text)
        """
        # First, check for discharge pattern: "rule from N" or "rule[N]"
        # Match: operator + rule name + (from N | [N])
        discharge_pattern = r"^(.*?)\s+(intro|elim)\s+(?:from\s+(\d+)|\[(\d+)\])$"
        match = re.match(discharge_pattern, just)

        if match:
            operator_part = match.group(1).strip()
            rule_name = match.group(2)
            label_num = match.group(3) or match.group(4)

            # Convert operator to LaTeX
            op_latex = operator_part.replace("<=>", r"$\Leftrightarrow$")
            op_latex = op_latex.replace("=>", r"$\Rightarrow$")
            op_latex = re.sub(r"\band\b", r"$\\land$", op_latex)
            op_latex = re.sub(r"\bor\b", r"$\\lor$", op_latex)
            op_latex = re.sub(r"\bnot\b", r"$\\lnot$", op_latex)

            # Format as: operator-rule^{[label]}
            return f"{op_latex}\\text{{-{rule_name}}}^{{[{label_num}]}}"

        # Check for rule subscript pattern: "operator rule N" (like "and elim 1")
        # Match: operator + rule name + number (1 or 2)
        subscript_pattern = r"^(.*?)\s+(intro|elim)\s*([12])$"
        match = re.match(subscript_pattern, just)

        if match:
            operator_part = match.group(1).strip()
            rule_name = match.group(2)
            subscript_num = match.group(3)

            # Convert operator to LaTeX
            op_latex = operator_part.replace("<=>", r"$\Leftrightarrow$")
            op_latex = op_latex.replace("=>", r"$\Rightarrow$")
            op_latex = re.sub(r"\band\b", r"$\\land$", op_latex)
            op_latex = re.sub(r"\bor\b", r"$\\lor$", op_latex)
            op_latex = re.sub(r"\bnot\b", r"$\\lnot$", op_latex)

            # Format as: operator-rule-number (just regular text, no subscript)
            return f"{op_latex}\\text{{-{rule_name}-{subscript_num}}}"

        # No special pattern - process normally
        # Replace logical operators with LaTeX symbols
        result = just.replace("<=>", r"\Leftrightarrow")
        result = result.replace("=>", r"\Rightarrow")
        result = re.sub(r"\band\b", r"\\land", result)
        result = re.sub(r"\bor\b", r"\\lor", result)
        result = re.sub(r"\bnot\b", r"\\lnot", result)

        # Wrap text parts in \text{}
        # If it contains "elim", "intro", "assumption", etc., wrap in \text{}
        if any(
            word in result
            for word in [
                "elim",
                "intro",
                "assumption",
                "premise",
                "from",
                "case",
                "contradiction",
                "middle",
            ]
        ):
            # Replace operators with proper spacing
            result = result.replace(r"\land", r"$\land$")
            result = result.replace(r"\lor", r"$\lor$")
            result = result.replace(r"\lnot", r"$\lnot$")
            result = result.replace(r"\Rightarrow", r"$\Rightarrow$")
            result = result.replace(r"\Leftrightarrow", r"$\Leftrightarrow$")
            return r"\text{" + result + "}"

        return result
