"""LaTeX generator for txt2tex - converts AST to LaTeX."""

from __future__ import annotations

import re
from typing import ClassVar

from txt2tex.ast_nodes import (
    Abbreviation,
    AxDef,
    BagLiteral,
    BinaryOp,
    CaseAnalysis,
    Conditional,
    Document,
    DocumentItem,
    EquivChain,
    Expr,
    FreeType,
    FunctionApp,
    FunctionType,
    GenDef,
    GenericInstantiation,
    GivenType,
    GuardedBranch,
    GuardedCases,
    Identifier,
    Lambda,
    LatexBlock,
    Number,
    PageBreak,
    Paragraph,
    Part,
    ProofNode,
    ProofTree,
    PureParagraph,
    Quantifier,
    Range,
    RelationalImage,
    Schema,
    Section,
    SequenceLiteral,
    SetComprehension,
    SetLiteral,
    Solution,
    Subscript,
    Superscript,
    TruthTable,
    Tuple,
    TupleProjection,
    UnaryOp,
)
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser


class LaTeXGenerator:
    """Generates LaTeX from AST for Phase 0-4 + Phase 10a-b + Phase 11 + Phase 12.

    Phase 10a: Supports relation operators (<->, |->, <|, |>, comp, ;)
    and relation functions (dom, ran).
    Phase 10b: Supports extended relation operators (<<|, |>>, o9, inv, id, ~, +, *).
    Phase 11: Supports function types, lambda, tuples, relational images, generics.
    Phase 12: Supports sequences (⟨⟩, head, tail, last, front, rev, ⌢, .1),
    bags ([[x]]), and tuple projection.
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
        "/=": r"\neq",  # Z notation slash negation (Phase 16+)
        # Set operators (Phase 3, enhanced in Phase 7, Phase 11.5)
        "in": r"\in",
        "notin": r"\notin",
        "/in": r"\notin",  # Z notation slash negation (Phase 16+)
        "subset": r"\subseteq",
        "union": r"\cup",
        "intersect": r"\cap",
        "cross": r"\cross",  # Cartesian product
        "×": r"\cross",  # Cartesian product (Unicode)  # noqa: RUF001
        "\\": r"\setminus",  # Set difference
        "++": r"\oplus",  # Override (Phase 13)
        # Relation operators (Phase 10a)
        "<->": r"\rel",  # Relation type
        "|->": r"\mapsto",  # Maplet constructor
        "<|": r"\dres",  # Domain restriction
        "|>": r"\rres",  # Range restriction
        "comp": r"\comp",  # Relational composition
        ";": r"\semi",  # Relational composition (semicolon)
        # Extended relation operators (Phase 10b)
        "<<|": r"\ndres",  # Domain subtraction (anti-restriction)
        "|>>": r"\nrres",  # Range subtraction (anti-restriction)
        "o9": r"\circ",  # Forward/backward composition
        # Function type operators (Phase 11a, enhanced Phase 18)
        "->": r"\fun",  # Total function
        "+->": r"\pfun",  # Partial function
        ">->": r"\inj",  # Total injection
        ">+>": r"\pinj",  # Partial injection
        "-|>": r"\pinj",  # Partial injection (alternative notation)
        "-->>": r"\surj",  # Total surjection
        "+->>": r"\psurj",  # Partial surjection
        ">->>": r"\bij",  # Bijection
        # Arithmetic operators
        "+": r"+",  # Addition (also postfix in relational context)
        "-": r"-",  # Subtraction (Phase 16)
        "*": r"*",  # Multiplication (also postfix in relational context)
        "mod": r"\mod",  # Modulo (use \mod not \bmod for fuzz compatibility)
        # Sequence operators (Phase 12)
        "⌢": r"\cat",  # Sequence concatenation (Unicode)
        "^": r"\cat",  # Sequence concatenation (ASCII alternative, Phase 14)
    }

    UNARY_OPS: ClassVar[dict[str, str]] = {
        "not": r"\lnot",
        "-": r"-",  # Unary negation (Phase 16)
        "#": r"\#",  # Cardinality (Phase 8)
        # Relation functions (Phase 10a)
        "dom": r"\dom",  # Domain of relation
        "ran": r"\ran",  # Range of relation
        # Extended relation functions (Phase 10b)
        "inv": r"\inv",  # Inverse function
        "id": r"\id",  # Identity relation
        # Set functions (Phase 11.5, enhanced Phase 19)
        "P": r"\power",  # Power set
        "P1": r"\power_1",  # Non-empty power set
        "F": r"\finset",  # Finite set
        "F1": r"\finset_1",  # Non-empty finite set
        "bigcup": r"\bigcup",  # Distributed union (Phase 20)
        # Sequence operators (Phase 12)
        "head": r"\head",  # First element
        "tail": r"\tail",  # All but first
        "last": r"\last",  # Last element
        "front": r"\front",  # All but last
        "rev": r"\rev",  # Reverse sequence
        # Postfix operators (Phase 10b) - special handling needed
        "~": r"^{-1}",  # Relational inverse (superscript -1)
        "+": r"^+",  # Transitive closure (superscript +)
        "*": r"^*",  # Reflexive-transitive closure (superscript *)
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
        # Relation operators (Phase 10a-b) - between comparison and set ops
        "<->": 6,
        "|->": 6,
        "<|": 6,
        "|>": 6,
        "<<|": 6,  # Phase 10b
        "|>>": 6,  # Phase 10b
        "o9": 6,  # Phase 10b
        "comp": 6,
        ";": 6,
        # Function type operators (Phase 11a) - same as relations
        "->": 6,
        "+->": 6,
        ">->": 6,
        ">+>": 6,
        "-->>": 6,
        "+->>": 6,
        ">->>": 6,
        # Set operators - highest precedence
        "in": 7,
        "notin": 7,
        "subset": 7,
        "union": 8,
        "cross": 8,  # Cartesian product (Phase 11.5) - same as union
        "×": 8,  # Cartesian product (Unicode) - same as union  # noqa: RUF001
        "intersect": 9,
        "\\": 9,  # Set difference (Phase 11.5) - same as intersect
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
        # Use fleqn option to left-align all equations (no centering)
        # a4paper for A4 page size, 10pt font (matches instructor's format)
        lines.append(r"\documentclass[a4paper,10pt,fleqn]{article}")
        # Standard 1 inch margins on all sides
        lines.append(r"\usepackage[margin=1in]{geometry}")
        # Load amssymb for \mathbb{N} and \mathbb{Z} blackboard bold
        # Note: amsmath removed - using array{lll} instead of align* for EQUIV
        lines.append(r"\usepackage{amssymb}")  # For \mathbb{N} and \mathbb{Z}
        if self.use_fuzz:
            lines.append(r"\usepackage{fuzz}")  # Replaces zed-cm (fonts/styling)
        else:
            lines.append(r"\usepackage{zed-cm}")  # Computer Modern fonts/styling
        # These packages work with both fuzz and zed-cm
        lines.append(r"\usepackage{zed-maths}")  # Mathematical operators
        lines.append(r"\usepackage{zed-proof}")  # Proof tree macros (\infer)
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
        if isinstance(item, PureParagraph):
            return self._generate_pure_paragraph(item)
        if isinstance(item, LatexBlock):
            return self._generate_latex_block(item)
        if isinstance(item, PageBreak):
            return self._generate_pagebreak(item)
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
        if isinstance(item, GenDef):
            return self._generate_gendef(item)
        if isinstance(item, Schema):
            return self._generate_schema(item)
        if isinstance(item, ProofTree):
            return self._generate_proof_tree(item)

        # Item is an Expr - render as left-aligned paragraph with inline math
        # Don't center expressions - use noindent paragraph instead
        latex_expr = self.generate_expr(item)
        return [r"\noindent", f"${latex_expr}$", "", ""]

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
        if isinstance(expr, Lambda):
            return self._generate_lambda(expr)
        if isinstance(expr, Subscript):
            return self._generate_subscript(expr)
        if isinstance(expr, Superscript):
            return self._generate_superscript(expr)
        if isinstance(expr, SetComprehension):
            return self._generate_set_comprehension(expr)
        if isinstance(expr, SetLiteral):
            return self._generate_set_literal(expr)
        if isinstance(expr, FunctionApp):
            return self._generate_function_app(expr)
        if isinstance(expr, FunctionType):
            return self._generate_function_type(expr)
        if isinstance(expr, Tuple):
            return self._generate_tuple(expr)
        if isinstance(expr, RelationalImage):
            return self._generate_relational_image(expr)
        if isinstance(expr, GenericInstantiation):
            return self._generate_generic_instantiation(expr)
        if isinstance(expr, Range):
            return self._generate_range(expr)
        if isinstance(expr, SequenceLiteral):
            return self._generate_sequence_literal(expr)
        if isinstance(expr, TupleProjection):
            return self._generate_tuple_projection(expr)
        if isinstance(expr, BagLiteral):
            return self._generate_bag_literal(expr)
        if isinstance(expr, Conditional):
            return self._generate_conditional(expr)
        if isinstance(expr, GuardedCases):
            return self._generate_guarded_cases(expr)
        if isinstance(expr, GuardedBranch):
            return self._generate_guarded_branch(expr)

        raise TypeError(f"Unknown expression type: {type(expr)}")

    def _generate_identifier(self, node: Identifier) -> str:
        """Generate LaTeX for identifier (Phase 15: smart underscore handling).

        Handles three cases:
        1. No underscore: return as-is (e.g., 'x' → 'x')
        2. Simple subscript: return as-is (e.g., 'a_i' → 'a_i', 'x_0' → 'x_0')
        3. Multi-char subscript: add braces (e.g., 'a_max' → 'a_{max}')
        4. Multi-word identifier: escape/mathit (e.g., 'cumulative_total')

        Special keywords (Issue #3 from QA):
        - emptyset → \\emptyset (empty set symbol)
        """
        name = node.name

        # Special keywords (Issue #2 and #3 from QA)
        special_keywords = {
            "emptyset": r"\emptyset",
            "forall": r"\forall",
            "exists": r"\exists",
        }
        if name in special_keywords:
            return special_keywords[name]

        # Mathematical type names: use blackboard bold (or fuzz built-in types)
        # N = naturals, Z = integers
        # Only convert N and Z, not Q/R/C which are commonly used as variables
        if name == "Z":
            # Fuzz uses \num for integers, LaTeX uses \mathbb{Z}
            return r"\num" if self.use_fuzz else r"\mathbb{Z}"
        if name == "N":
            # Fuzz uses \nat for naturals, LaTeX uses \mathbb{N}
            return r"\nat" if self.use_fuzz else r"\mathbb{N}"

        # No underscore: return as-is
        if "_" not in name:
            return name

        # Fuzz: keep underscores as-is, no escaping or mathit wrapper
        if self.use_fuzz:
            return name

        # Check for multi-word identifier pattern
        # Heuristic: if prefix OR suffix is > 3 chars, it's a multi-word identifier
        parts = name.split("_")

        # Multiple underscores OR long words → multi-word identifier
        if len(parts) > 2 or any(len(part) > 3 for part in parts):
            escaped = name.replace("_", r"\_")
            return rf"\mathit{{{escaped}}}"

        # Single underscore with short parts: subscript
        if len(parts) == 2:
            prefix, suffix = parts
            # Simple subscript: single character after underscore
            if len(suffix) == 1:
                return f"{prefix}_{suffix}"
            # Multi-char subscript: needs braces
            else:
                return f"{prefix}_{{{suffix}}}"

        # Fallback: escape and use mathit
        escaped = name.replace("_", r"\_")
        return rf"\mathit{{{escaped}}}"

    def _generate_number(self, node: Number) -> str:
        """Generate LaTeX for number."""
        return node.value

    def _generate_unary_op(self, node: UnaryOp) -> str:
        """Generate LaTeX for unary operation.

        Unary operators have higher precedence than all binary operators,
        so parentheses are added around binary operator operands.

        Phase 10b: Postfix operators (~, +, *) are rendered as superscripts
        on the operand, not as prefix operators.
        """
        op_latex = self.UNARY_OPS.get(node.operator)
        if op_latex is None:
            raise ValueError(f"Unknown unary operator: {node.operator}")

        operand = self.generate_expr(node.operand)

        # Add parentheses if operand is a binary operator
        # (unary has higher precedence than all binary operators)
        if isinstance(node.operand, BinaryOp):
            operand = f"({operand})"

        # Add parentheses for function application with fuzz mode
        # Fuzz has different precedence: # binds less tightly than application
        # So # s(i) means (# s)(i), but we want # (s(i))
        if self.use_fuzz and isinstance(node.operand, FunctionApp):
            operand = f"({operand})"

        # Phase 10b: Check if this is a postfix operator (rendered as superscript)
        if node.operator in {"~", "+", "*"}:
            # Postfix: operand^{superscript}
            return f"{operand}{op_latex}"
        # Phase 11.5, 19: Generic instantiation operators (P, P1, F, F1)
        # Per fuzz manual p.23: prefix generic symbols are operator symbols,
        # LaTeX inserts thin space automatically - NO TILDE needed
        elif node.operator in {"P", "P1", "F", "F1"}:
            # Generic instantiation: \power X or \finset X (no tilde)
            return f"{op_latex} {operand}"
        else:
            # Prefix: operator operand
            # Special case: no space for unary minus (Phase 16)
            if node.operator == "-":
                return f"{op_latex}{operand}"
            else:
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
        Phase 11.5 enhancement: Supports mu with expression part (mu x : X | P . E).
        Examples:
        - forall x : N | pred -> \\forall x \\colon N \\bullet pred
        - forall x, y : N | pred -> \\forall x, y \\colon N \\bullet pred
        - exists1 x : N | pred -> \\exists_1 x \\colon N \\bullet pred
        - mu x : N | pred -> \\mu x \\colon N \\bullet pred
        - mu x : N | pred . expr -> \\mu x \\colon N \\mid pred \\bullet expr
        """
        quant_latex = self.QUANTIFIERS.get(node.quantifier)
        if quant_latex is None:
            raise ValueError(f"Unknown quantifier: {node.quantifier}")

        # Generate variables (comma-separated for multi-variable quantifiers)
        variables_str = ", ".join(node.variables)
        parts = [quant_latex, variables_str]

        if node.domain:
            domain_latex = self.generate_expr(node.domain)
            # Fuzz uses : instead of \colon
            parts.append(":" if self.use_fuzz else r"\colon")
            parts.append(domain_latex)

        # Phase 11.5: Check if mu has expression part
        if node.quantifier == "mu" and node.expression:
            # Use | or \mid for predicate separator
            parts.append("|" if self.use_fuzz else r"\mid")
            body_latex = self.generate_expr(node.body)
            parts.append(body_latex)
            # Add @ or bullet separator and expression
            # Fuzz uses @ (at sign), LaTeX uses \bullet
            parts.append("@" if self.use_fuzz else r"\bullet")
            expr_latex = self.generate_expr(node.expression)
            parts.append(expr_latex)
        else:
            # Standard quantifier: @ or bullet separator and body
            # Fuzz uses @ (at sign), LaTeX uses \bullet
            parts.append("@" if self.use_fuzz else r"\bullet")
            body_latex = self.generate_expr(node.body)
            parts.append(body_latex)

        return " ".join(parts)

    def _generate_lambda(self, node: Lambda) -> str:
        """Generate LaTeX for lambda expression (Phase 11d).

        Examples:
        - lambda x : N . x^2 -> \\lambda x : \\nat \\bullet x^{2}
        - lambda x, y : N . x + y -> \\lambda x, y : \\nat \\bullet x + y
        - lambda f : X -> Y . f(x) -> \\lambda f : X \\fun Y \\bullet f(x)

        Note: Uses : (colon) for lambda binding, not \\colon.
        """
        # Generate variables (comma-separated for multi-variable)
        variables_str = ", ".join(node.variables)
        parts = [r"\lambda", variables_str, ":"]

        # Generate domain (required for lambda)
        domain_latex = self.generate_expr(node.domain)
        parts.append(domain_latex)

        # Add bullet separator and body
        parts.append(r"\bullet")
        body_latex = self.generate_expr(node.body)
        parts.append(body_latex)

        return " ".join(parts)

    def _generate_set_comprehension(self, node: SetComprehension) -> str:
        """Generate LaTeX for set comprehension (Phase 8, enhanced Phase 22).

        Supports three forms:
        - Set by predicate: { x : X | predicate }
          -> \\{ x \\colon X \\mid predicate \\}
        - Set by expression with predicate: { x : X | pred . expr }
          -> \\{ x \\colon X \\mid pred \\bullet expr \\}
        - Set by expression only: { x : X . expr }
          -> \\{ x \\colon X \\bullet expr \\}

        Examples:
        - { x : N | x > 0 }
          -> \\{ x \\colon \\mathbb{N} \\mid x > 0 \\}
        - { x : N | x > 0 . x^2 }
          -> \\{ x \\colon \\mathbb{N} \\mid x > 0 \\bullet x^{2} \\}
        - { x : N . x^2 }
          -> \\{ x \\colon \\mathbb{N} \\bullet x^{2} \\}
        """
        # Generate variables (comma-separated for multi-variable)
        variables_str = ", ".join(node.variables)
        # Both fuzz and LaTeX use \{ \} for set braces
        parts = [r"\{", variables_str]

        if node.domain:
            domain_latex = self.generate_expr(node.domain)
            # Fuzz uses : instead of \colon
            parts.append(":" if self.use_fuzz else r"\colon")
            parts.append(domain_latex)

        # Phase 22: Handle case with no predicate
        if node.predicate is None:
            # No predicate: { x : X . expr } -> use bullet/@ directly
            if node.expression:
                # Fuzz uses @ (at sign) inside Z environments, LaTeX uses \bullet
                parts.append("@" if self.use_fuzz else r"\bullet")
                expression_latex = self.generate_expr(node.expression)
                parts.append(expression_latex)
            # else: {x : T} with no predicate or expression - just the binding
        else:
            # Has predicate: add mid/pipe separator
            parts.append("|" if self.use_fuzz else r"\mid")

            # Generate predicate
            predicate_latex = self.generate_expr(node.predicate)
            parts.append(predicate_latex)

            # If expression is present, add bullet/@ and expression
            if node.expression:
                # Fuzz uses @ (at sign) inside Z environments, LaTeX uses \bullet
                parts.append("@" if self.use_fuzz else r"\bullet")
                expression_latex = self.generate_expr(node.expression)
                parts.append(expression_latex)

        # Close set
        parts.append(r"\}")

        return " ".join(parts)

    def _generate_set_literal(self, node: SetLiteral) -> str:
        """Generate LaTeX for set literal (Phase 11.5).

        Examples:
        - {1, 2, 3} -> \\{1, 2, 3\\}
        - {a, b} -> \\{a, b\\}
        - {} -> \\{\\} (empty set)
        """
        if not node.elements:
            # Empty set - render as \{\}
            return r"\{\}"

        # Generate comma-separated elements
        elements_latex = ", ".join(self.generate_expr(elem) for elem in node.elements)
        return f"\\{{{elements_latex}\\}}"

    def _generate_subscript(self, node: Subscript) -> str:
        """Generate LaTeX for subscript (a_1, x_i)."""
        base = self.generate_expr(node.base)
        index = self.generate_expr(node.index)

        # Wrap index in braces if it's more than one character
        if len(index) > 1:
            return f"{base}_{{{index}}}"
        return f"{base}_{index}"

    def _generate_superscript(self, node: Superscript) -> str:
        """Generate LaTeX for superscript (x^2, 2^n, (z^2)^3)."""
        base = self.generate_expr(node.base)
        exponent = self.generate_expr(node.exponent)

        # Wrap base in braces if it contains a superscript (for nesting)
        if isinstance(node.base, Superscript):
            base = f"{{{base}}}"

        # Wrap exponent in braces if it's more than one character
        if len(exponent) > 1:
            return f"{base}^{{{exponent}}}"
        return f"{base}^{exponent}"

    def _generate_function_app(self, node: FunctionApp) -> str:
        """Generate LaTeX for function application (Phase 11b, enhanced in Phase 13).

        Phase 13 enhancement: Supports applying any expression, not just identifiers.

        Examples:
        - f(x) → f(x)
        - g(x, y, z) → g(x, y, z)
        - seq(N) → \\seq~N
        - seq seq N → \\seq \\seq N (nested special functions)
        - seq1 seq X → \\seq_1 \\seq X (nested special functions)
        - ⟨a, b, c⟩(2) → \\langle a, b, c \\rangle(2)
        - (f ++ g)(x) → (f \\oplus g)(x)
        """
        # Special Z notation functions with LaTeX commands
        special_functions = {
            "seq": r"\seq",
            "seq1": r"\seq_1",  # Non-empty sequences
            "iseq": r"\iseq",
            "bag": r"\bag",
            "P": r"\power",  # Power set
            "F": r"\finset",  # Finite set
        }

        # Check if function is a simple identifier with special handling
        if isinstance(node.function, Identifier):
            func_name = node.function.name
            if func_name in special_functions and len(node.args) == 1:
                # Generic instantiation: \seq N (no tilde)
                # Per fuzz manual p.23: prefix generic symbols are operator symbols,
                # LaTeX inserts thin space automatically
                func_latex = special_functions[func_name]
                arg_latex = self.generate_expr(node.args[0])
                # Add parentheses if arg is a function app (e.g., seq1 (seq X))
                if isinstance(node.args[0], FunctionApp):
                    arg_latex = f"({arg_latex})"
                return f"{func_latex} {arg_latex}"

            # Standard function application with identifier: f(x, y, z)
            # Process identifier through _generate_identifier for underscore handling
            func_latex = self._generate_identifier(node.function)
            args_latex = ", ".join(self.generate_expr(arg) for arg in node.args)
            return f"{func_latex}({args_latex})"

        # Check for nested special functions: seq seq X or seq1 seq X
        # Parser treats "seq seq X" as ((seq seq) X) due to left-associativity
        # We need to recognize this pattern and generate \seq (\seq X) with parens
        if isinstance(node.function, FunctionApp):
            inner_func = node.function.function
            # Check if inner function is special and has one special function arg
            if (
                isinstance(inner_func, Identifier)
                and inner_func.name in special_functions
                and len(node.function.args) == 1
                and isinstance(node.function.args[0], Identifier)
                and node.function.args[0].name in special_functions
            ):
                # Pattern: (special_fn1(special_fn2))(args)
                # Generate: special_fn1 (special_fn2 args) with parens
                outer_latex = special_functions[inner_func.name]
                inner_latex = special_functions[node.function.args[0].name]
                args_latex = " ".join(self.generate_expr(arg) for arg in node.args)
                return f"{outer_latex} ({inner_latex} {args_latex})"

        # General function application: expr(args)
        func_latex = self.generate_expr(node.function)

        # Add parentheses around function if it's a binary operator
        if isinstance(node.function, BinaryOp):
            func_latex = f"({func_latex})"

        args_latex = ", ".join(self.generate_expr(arg) for arg in node.args)
        return f"{func_latex}({args_latex})"

    def _generate_function_type(self, node: FunctionType) -> str:
        """Generate LaTeX for function type arrows (Phase 11c).

        Examples:
        - X -> Y → X \\fun Y
        - X +-> Y → X \\pfun Y
        - X >-> Y → X \\inj Y
        - N +-> N → N \\pfun N
        - A -> B -> C → A \\fun (B \\fun C) [right-associative]
        """
        arrow_latex = self.BINARY_OPS.get(node.arrow)
        if arrow_latex is None:
            raise ValueError(f"Unknown function arrow: {node.arrow}")

        domain_latex = self.generate_expr(node.domain)
        range_latex = self.generate_expr(node.range)

        # Add parentheses to range if it's also a function type (for clarity)
        # Function types are right-associative: A -> B -> C means A -> (B -> C)
        if isinstance(node.range, FunctionType):
            range_latex = f"({range_latex})"

        return f"{domain_latex} {arrow_latex} {range_latex}"

    def _generate_tuple(self, node: Tuple) -> str:
        """Generate LaTeX for tuple expression (Phase 11.6).

        Examples:
        - (1, 2) -> (1, 2)
        - (x, y, z) -> (x, y, z)
        - (a, b+1, f(c)) -> (a, b+1, f(c))

        Tuples are rendered as comma-separated expressions in parentheses.
        """
        elements_latex = ", ".join(self.generate_expr(elem) for elem in node.elements)
        return f"({elements_latex})"

    def _generate_relational_image(self, node: RelationalImage) -> str:
        """Generate LaTeX for relational image (Phase 11.8).

        The relational image R(| S |) gives the image of set S under relation R.

        Examples:
        - R(| {1, 2} |) -> (R \\limg \\{1, 2\\} \\rimg)
        - parentOf(| {john} |) -> (parentOf \\limg \\{john\\} \\rimg)
        - (R o9 S)(| A |) -> ((R \\circ S) \\limg A \\rimg)

        LaTeX rendering uses \\limg and \\rimg delimiters with spaces.
        Note: fuzz requires the entire expression wrapped in parentheses with
        spaces around \\limg/\\rimg, not function application syntax.
        """
        relation_latex = self.generate_expr(node.relation)
        set_latex = self.generate_expr(node.set)
        return f"({relation_latex} \\limg {set_latex} \\rimg)"

    def _generate_generic_instantiation(self, node: GenericInstantiation) -> str:
        """Generate LaTeX for generic type instantiation (Phase 11.9).

        Generic types can be instantiated with specific type parameters using
        bracket notation. Special Z notation types use special LaTeX commands.

        Examples:
        - ∅[N] -> \\emptyset[N] or special empty set notation
        - seq[N] -> \\seq[N]
        - P[X] -> \\power[X]
        - Type[A, B] -> Type[A, B]
        - ∅[N cross N] -> \\emptyset[N \\cross N]

        Strategy: Check if base is a special Z notation identifier, use special
        rendering if so, otherwise use standard bracket notation.
        """
        base_latex = self.generate_expr(node.base)

        # Generate comma-separated type parameters
        type_params_latex = ", ".join(
            self.generate_expr(param) for param in node.type_params
        )

        # Special Z notation types that might have custom rendering
        # For now, use standard bracket notation for all types
        # Future enhancement: Could use special notation like \emptyset~N
        return f"{base_latex}[{type_params_latex}]"

    def _generate_range(self, node: Range) -> str:
        """Generate LaTeX for range expression (Phase 13).

        Represents integer range expressions: m..n represents {m, m+1, ..., n}

        Examples:
        - 1..10 -> 1 \\upto 10
        - 1993..current -> 1993 \\upto current
        - x.2..x.3 -> x.2 \\upto x.3

        LaTeX rendering uses \\upto command.
        """
        start_latex = self.generate_expr(node.start)
        end_latex = self.generate_expr(node.end)
        return f"{start_latex} \\upto {end_latex}"

    def _generate_sequence_literal(self, node: SequenceLiteral) -> str:
        """Generate LaTeX for sequence literal (Phase 12).

        Examples:
        - ⟨⟩ -> \\langle \\rangle (empty sequence)
        - ⟨a⟩ -> \\langle a \\rangle
        - ⟨1, 2, 3⟩ -> \\langle 1, 2, 3 \\rangle
        """
        if not node.elements:
            # Empty sequence
            return r"\langle \rangle"

        # Generate comma-separated elements
        elements_latex = ", ".join(self.generate_expr(elem) for elem in node.elements)
        return f"\\langle {elements_latex} \\rangle"

    def _generate_tuple_projection(self, node: TupleProjection) -> str:
        """Generate LaTeX for tuple projection (Phase 12).

        Examples:
        - x.1 -> x.1
        - (a, b).2 -> (a, b).2
        - f(x).3 -> f(x).3

        Tuple projection is rendered as-is (stays the same in LaTeX).
        """
        base_latex = self.generate_expr(node.base)

        # Add parentheses if base is a binary operator
        if isinstance(node.base, BinaryOp):
            base_latex = f"({base_latex})"

        return f"{base_latex}.{node.index}"

    def _generate_bag_literal(self, node: BagLiteral) -> str:
        """Generate LaTeX for bag literal (Phase 12).

        Examples:
        - [[x]] -> \\lbag x \\rbag
        - [[1, 2, 2, 3]] -> \\lbag 1, 2, 2, 3 \\rbag

        Bags are multisets where elements can appear multiple times.
        """
        # Generate comma-separated elements
        elements_latex = ", ".join(self.generate_expr(elem) for elem in node.elements)
        return f"\\lbag {elements_latex} \\rbag"

    def _generate_conditional(self, node: Conditional) -> str:
        """Generate LaTeX for conditional expression (Phase 16).

        Examples:
        - if x > 0 then x else -x
        - if s = <> then 0 else head s

        Rendered as: (\\mbox{if } condition \\mbox{ then } expr1 \\mbox{ else } expr2)
        """
        condition_latex = self.generate_expr(node.condition)
        then_latex = self.generate_expr(node.then_expr)
        else_latex = self.generate_expr(node.else_expr)

        # Render as inline conditional with mbox keywords (standard LaTeX)
        return (
            f"(\\mbox{{if }} {condition_latex} "
            f"\\mbox{{ then }} {then_latex} "
            f"\\mbox{{ else }} {else_latex})"
        )

    def _generate_guarded_cases(self, node: GuardedCases) -> str:
        """Generate LaTeX for guarded cases expression (Phase 23).

        Examples:
        premium_plays(<x> ^ s) =
          <x> ^ (premium_plays s) if user_status(x.2) = premium
          premium_plays s if user_status(x.2) = standard

        Rendered as multi-line with alignment and \\mbox{if} guards:
          <x> ^ (premium_plays~s) \\\\
          \\mbox{if } user_status(x.2) = premium \\\\
          premium_plays~s \\\\
          \\mbox{if } user_status(x.2) = standard
        """
        lines: list[str] = []
        for branch in node.branches:
            expr_latex = self.generate_expr(branch.expression)
            guard_latex = self.generate_expr(branch.guard)
            lines.append(f"{expr_latex} \\\\")
            lines.append(f"\\mbox{{if }} {guard_latex}")
            if branch != node.branches[-1]:  # Add line break between branches
                lines.append("\\\\")

        return "\n".join(lines)

    def _generate_guarded_branch(self, node: GuardedBranch) -> str:
        """Generate LaTeX for single guarded branch (Phase 23).

        This is typically not called directly; GuardedCases handles the rendering.
        """
        expr_latex = self.generate_expr(node.expression)
        guard_latex = self.generate_expr(node.guard)
        return f"{expr_latex} \\mbox{{if }} {guard_latex}"

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
        """Generate LaTeX for part label.

        - Single Paragraph: inline with hanging indent
        - Single Expr: inline math
        - Starts with Expr + more content: inline Expr, then continue below
        - Multiple items or structural elements: traditional multi-line format
        """
        lines: list[str] = []

        # Check if part contains single paragraph (from TEXT: parsing)
        if len(node.items) == 1 and isinstance(node.items[0], Paragraph):
            # Hanging indent format for prose paragraphs
            paragraph = node.items[0]
            # Remove the leading \bigskip from paragraph generation
            para_lines = self._generate_paragraph(paragraph)
            # Filter out \bigskip and empty lines at start
            while para_lines and (para_lines[0] == r"\bigskip" or para_lines[0] == ""):
                para_lines.pop(0)
            # Use noindent and hangindent for proper alignment
            lines.append(r"\noindent")
            lines.append(r"\hangindent=2em")  # Indent continuation lines
            if para_lines:
                lines.append(f"({node.label}) {para_lines[0]}")
                lines.extend(para_lines[1:])
            else:
                lines.append(f"({node.label})")
            lines.append("")
            lines.append(r"\medskip")
        elif len(node.items) == 1 and isinstance(node.items[0], Expr):
            # Single expression: inline math (like Solution 1)
            expr = node.items[0]
            expr_latex = self.generate_expr(expr)
            lines.append(r"\noindent")
            lines.append(r"\hangindent=2em")  # Indent continuation lines
            lines.append(f"({node.label}) ${expr_latex}$")
            lines.append("")
            lines.append(r"\medskip")
        elif len(node.items) >= 2 and isinstance(node.items[0], Expr):
            # Starts with expression followed by more content
            # Render first expression inline, then rest below
            expr = node.items[0]
            expr_latex = self.generate_expr(expr)
            lines.append(r"\noindent")
            lines.append(r"\hangindent=2em")  # Indent continuation lines
            lines.append(f"({node.label}) ${expr_latex}$")
            lines.append("")

            # Render remaining items
            for item in node.items[1:]:
                item_lines = self.generate_document_item(item)
                lines.extend(item_lines)

            lines.append(r"\medskip")
            lines.append("")
        else:
            # Traditional format: label on separate line
            lines.append(f"({node.label})")
            lines.append(r"\par")  # End paragraph cleanly
            lines.append(r"\vspace{11pt}")  # Explicit spacing for all content types

            for item in node.items:
                item_lines = self.generate_document_item(item)
                lines.extend(item_lines)

            lines.append(r"\medskip")
            lines.append("")

        return lines

    def _replace_outside_math(self, text: str, pattern: str, replacement: str) -> str:
        """Replace pattern with LaTeX command only when NOT inside $...$ math mode."""
        result = []
        in_math = False
        i = 0

        while i < len(text):
            # Check for $ to toggle math mode
            if text[i] == "$":
                in_math = not in_math
                result.append("$")
                i += 1
            # Check for pattern match
            elif not in_math and text[i : i + len(pattern)] == pattern:
                result.append(f"${replacement}$")
                i += len(pattern)
            else:
                result.append(text[i])
                i += 1

        return "".join(result)

    def _generate_paragraph(self, node: Paragraph) -> list[str]:
        """Generate LaTeX for plain text paragraph.

        Converts symbolic operators like <=> and => to LaTeX math symbols.
        Supports inline math expressions like { x : N | x > 0 }.
        Does NOT convert words like 'and', 'or', 'not' - these are English prose.
        """
        lines: list[str] = []
        lines.append(r"\bigskip")  # Leading vertical space (larger than medskip)
        lines.append("")

        # Convert sequence literals FIRST to protect <x> patterns
        # Must happen before _process_inline_math() which can break up < and >
        text = self._convert_sequence_literals(node.text)

        # Process inline math expressions (includes formula detection)
        text = self._process_inline_math(text)

        # Then convert remaining symbolic operators to LaTeX math symbols
        # Only replace if NOT already wrapped in math mode
        # Do NOT convert and/or/not - those are English words in prose context
        text = self._replace_outside_math(text, "<=>", r"\Leftrightarrow")
        text = self._replace_outside_math(text, "=>", r"\Rightarrow")

        # Convert Z notation operators (garbled character fix)
        # Order matters: longer operators first to avoid partial matches
        text = text.replace("|>>", r"$\nrres$")  # Range anti-restriction
        text = text.replace("<<|", r"$\ndres$")  # Domain anti-restriction
        text = text.replace("-|>", r"$\pinj$")  # Partial injection
        text = text.replace("+->", r"$\pfun$")  # Partial function
        text = text.replace(">->", r"$\inj$")  # Total injection
        text = text.replace("<->", r"$\rel$")  # Relation type
        text = text.replace("|->", r"$\mapsto$")  # Maplet
        text = text.replace("<|", r"$\dres$")  # Domain restriction
        text = text.replace("|>", r"$\rres$")  # Range restriction
        text = text.replace("->", r"$\fun$")  # Total function

        # Convert keywords to symbols (QA fixes)
        # Negative lookbehind (?<!\\) ensures we don't match LaTeX commands like \forall
        # These are for standalone keywords in prose, not parsed quantifier expressions
        # Order matters: exists1+ must come before exists1 to avoid partial match
        text = re.sub(r"(?<!\\)exists1\+", r"$\\exists$", text)  # exists1+ → ∃
        text = re.sub(r"(?<!\\)\bexists1\b", r"$\\exists_1$", text)  # exists1 → ∃₁
        text = re.sub(r"(?<!\\)\bemptyset\b", r"$\\emptyset$", text)  # emptyset → ∅
        text = re.sub(r"(?<!\\)\bforall\b", r"$\\forall$", text)  # forall → ∀

        # Convert "not <variable>" to logical not symbol
        # Only when "not" is followed by a single identifier (variable name)
        # Examples: "not p", "not q", but NOT "not a tautology", "not every"
        # Pattern: \bnot\s+([a-zA-Z]\b) - "not" followed by single letter
        text = re.sub(r"\bnot\s+([a-zA-Z])\b", r"$\\lnot \1$", text)  # not p → ¬p

        # Convert "not in" and "in" for set membership (e.g., "0 in N", "x not in S")
        # Pattern: simple expression followed by "not in"/"in" + capitalized set name
        # Matches: identifier/number, optionally with operators (-, +, *, /)
        # Examples: "0 in N", "4 - 0 in N", "x - 1 not in N"
        # Only convert when set name starts with capital to avoid "in" in English prose
        text = re.sub(
            r"\b(\w+(?:\s*[\+\-\*/]\s*\w+)*)\s+not\s+in\s+([A-Z]\w*)\b",
            r"$\1 \\notin \2$",
            text,
        )  # x - 1 not in N → $x - 1 \notin N$
        text = re.sub(
            r"\b(\w+(?:\s*[\+\-\*/]\s*\w+)*)\s+in\s+([A-Z]\w*)\b",
            r"$\1 \\in \2$",
            text,
        )  # 4 - 0 in N → $4 - 0 \in N$

        # Convert bare comparison operators (garbled character fix - final pass)
        # Catches cases not handled by _process_inline_math() (complex expressions)
        # Tracks math mode to avoid nested $...$
        text = self._convert_comparison_operators(text)

        lines.append(text)
        lines.append("")
        lines.append(r"\bigskip")  # Trailing vertical space
        lines.append("")
        return lines

    def _generate_pure_paragraph(self, node: PureParagraph) -> list[str]:
        """Generate LaTeX for pure text paragraph with NO processing.

        PURETEXT: blocks are output with:
        - NO formula detection
        - NO operator conversion
        - NO inline math processing
        - Only basic LaTeX character escaping
        """
        lines: list[str] = []
        lines.append(r"\bigskip")  # Leading vertical space
        lines.append("")

        # Only escape LaTeX special characters, no other processing
        text = self._escape_latex(node.text)

        lines.append(text)
        lines.append("")
        lines.append(r"\bigskip")  # Trailing vertical space
        lines.append("")
        return lines

    def _generate_latex_block(self, node: LatexBlock) -> list[str]:
        """Generate LaTeX for raw LaTeX passthrough block.

        LATEX: blocks output raw LaTeX with NO escaping.
        The LaTeX is passed directly through to the output.
        """
        lines: list[str] = []
        lines.append("")  # Blank line before
        lines.append(node.latex)  # Raw LaTeX, no processing
        lines.append("")  # Blank line after
        return lines

    def _generate_pagebreak(self, node: PageBreak) -> list[str]:
        """Generate LaTeX for page break.

        PAGEBREAK: inserts a page break in PDF output.
        """
        return [r"\newpage", ""]

    def _convert_comparison_operators(self, text: str) -> str:
        """Convert bare comparison operators to math mode, avoiding nested math.

        Handles: >=, <=, >, <, | (pipe)
        Only converts when NOT inside existing $...$ math mode.
        """
        result = []
        i = 0
        in_math = False  # Track if we're inside $...$ math mode

        while i < len(text):
            # Check for $ to track math mode transitions
            if text[i] == "$":
                in_math = not in_math
                result.append(text[i])
                i += 1
                continue

            # Only try conversions if NOT in math mode
            if not in_math:
                # Try >= first (multi-char before single-char)
                if i + 1 < len(text) and text[i : i + 2] == ">=":
                    result.append(r"$\geq$")
                    i += 2
                    continue
                # Try <=
                if i + 1 < len(text) and text[i : i + 2] == "<=":
                    result.append(r"$\leq$")
                    i += 2
                    continue
                # Try > (only with surrounding spaces)
                if (
                    text[i] == ">"
                    and (i == 0 or text[i - 1].isspace())
                    and (i + 1 >= len(text) or text[i + 1].isspace())
                ):
                    result.append(r"$>$")
                    i += 1
                    continue
                # Try < (only with surrounding spaces or end of string)
                # Special case: also convert at end like "then <x>"
                if (
                    text[i] == "<"
                    and (i == 0 or text[i - 1].isspace())
                    and (i + 1 >= len(text) or text[i + 1].isspace())
                ):
                    result.append(r"$<$")
                    i += 1
                    continue
                # Try | (pipe/bullet - causes garbled output in text mode)
                # Only convert if preceded by space or $ (end of math mode)
                # and followed by space/newline/end
                if text[i] == "|":
                    prev_ok = i == 0 or text[i - 1].isspace() or text[i - 1] == "$"
                    next_ok = (
                        i + 1 >= len(text)
                        or text[i + 1].isspace()
                        or text[i + 1] == "\n"
                    )
                    if prev_ok and next_ok:
                        result.append(r"$\mid$")
                        i += 1
                        continue

            # No match, copy character as-is
            result.append(text[i])
            i += 1

        return "".join(result)

    def _convert_sequence_literals(self, text: str) -> str:
        """Convert sequence literals <...> to math mode \\langle ... \\rangle.

        Handles patterns like:
        - <> → $\\langle \\rangle$
        - <a> → $\\langle a \\rangle$
        - <x, y> → $\\langle x, y \\rangle$
        - <1, 2, 3> → $\\langle 1, 2, 3 \\rangle$

        Uses regex to find angle bracket pairs and converts them to LaTeX.
        Must NOT match operators like <=> or <-> or comparison operators.
        """
        # Strategy: Only match sequences where the content is:
        # - Empty: <>
        # - Word characters, numbers, spaces, commas, parentheses, dots, ^: <x>, <a, b>
        # This prevents matching <=> (has =), <-> (has -), < > (comparison with space)
        # Pattern: < followed by (empty OR word chars/nums/spaces/commas/parens/dots/^),
        # then >
        # We need to be careful not to match partial patterns
        pattern = r"<([\w\s,\.\^\(\)]*)>"

        def replace_sequence(match: re.Match[str]) -> str:
            full_match = match.group(0)
            content = match.group(1)

            # Additional validation: check if this looks like an operator
            # Reject if: contains = or - or if it's empty and followed/preceded by =
            if "=" in full_match or "-" in full_match:
                return full_match  # Don't convert operators
            if "|" in full_match or "#" in full_match:
                return full_match  # Don't convert other operators

            # Check if this is truly a sequence or just < > comparison
            # Sequences should have specific patterns:
            # 1. Empty: <>
            # 2. Single identifier: <x>, <abc>
            # 3. Comma-separated: <x, y>, <a, b, c>
            content_stripped = content.strip()

            # Empty sequence
            if not content_stripped:
                return r"$\langle \rangle$"

            # Check if it looks like a valid sequence content
            # Valid: word characters, numbers, commas, spaces, parentheses, dots, ^
            # Invalid: if it has suspicious patterns
            # For safety, only convert if it matches common sequence patterns
            if re.match(r"^[\w\s,\.\^\(\)]+$", content_stripped):
                return rf"$\langle {content_stripped} \rangle$"

            # Not a sequence, return as-is
            return full_match

        result = re.sub(pattern, replace_sequence, text)
        return result

    def _find_balanced_braces(self, text: str) -> list[tuple[int, int]]:
        """Find all balanced brace pairs in text.

        Returns list of (start_pos, end_pos) tuples for each balanced {...}.
        Handles nested braces correctly.
        """
        matches: list[tuple[int, int]] = []
        i = 0
        while i < len(text):
            if text[i] == "{":
                # Found opening brace, find matching closing brace
                depth = 1
                start = i
                i += 1
                while i < len(text) and depth > 0:
                    if text[i] == "{":
                        depth += 1
                    elif text[i] == "}":
                        depth -= 1
                    i += 1
                if depth == 0:
                    # Found balanced pair
                    matches.append((start, i))
            else:
                i += 1
        return matches

    def _find_balanced_parens(self, text: str) -> list[tuple[int, int]]:
        """Find all balanced parenthesis pairs in text.

        Returns list of (start_pos, end_pos) tuples for each balanced (...).
        Handles nested parentheses correctly.
        """
        matches: list[tuple[int, int]] = []
        i = 0
        while i < len(text):
            if text[i] == "(":
                # Found opening paren, find matching closing paren
                depth = 1
                start = i
                i += 1
                while i < len(text) and depth > 0:
                    if text[i] == "(":
                        depth += 1
                    elif text[i] == ")":
                        depth -= 1
                    i += 1
                if depth == 0:
                    # Found balanced pair
                    matches.append((start, i))
            else:
                i += 1
        return matches

    def _process_inline_math(self, text: str) -> str:
        """Process inline math expressions in text.

        Detects patterns like:
        - Superscripts: x^2, a_i^2, 2^n (wrap in math mode)
        - Set comprehensions: { x : N | x > 0 }
        - Set comprehensions with nested braces: {p : P . p |-> {p}}
        - Quantifiers: forall x : N | predicate

        Parses them and converts to $...$ wrapped LaTeX.
        """
        result = text

        # Pattern -1.5: Manual operator markup [operator]
        # Convert bracketed operator keywords to symbols
        # Example: "([not], [and], [or])" becomes "(symbols)" in LaTeX
        # Must come FIRST before any expression parsing
        # This provides explicit markup when auto-detection doesn't work
        markup_operators = {
            r"\[not\]": r"$\\lnot$",
            r"\[and\]": r"$\\land$",
            r"\[or\]": r"$\\lor$",
            r"\[=>\]": r"$\\Rightarrow$",
            r"\[<=>\]": r"$\\Leftrightarrow$",
            r"\[forall\]": r"$\\forall$",
            r"\[exists\]": r"$\\exists$",
            r"\[exists1\]": r"$\\exists_1$",
        }

        for pattern, replacement in markup_operators.items():
            result = re.sub(pattern, replacement, result)

        # Pattern -1: Logical formulas with =>, <=>, not, and, or (MUST come FIRST)
        # Detect expressions like "p => (not p => p)" or "(not p => not q) <=> (q => p)"
        # Look for patterns starting with identifier/paren/not and containing => or <=>
        # Stop at sentence boundaries (is, as, are, etc.) or punctuation
        formula_pattern = (
            r"(\()?(?:not\s+)?([a-zA-Z]\w*)\s*(=>|<=>)\s*[^.!?]*?"
            r"(?=\s+(?:is|as|are|for|to|be|a|an|the|in|on|at|by|with)\b|[.!?]|$)"
        )

        matches = list(re.finditer(formula_pattern, result))
        for match in reversed(matches):
            start_pos = match.start()
            end_pos = match.end()

            # Check if already in math mode
            before = result[:start_pos]
            dollars_before = before.count("$")
            if dollars_before % 2 == 1:
                continue

            formula_text = result[start_pos:end_pos].strip()

            # Try to parse as logical expression
            try:
                lexer = Lexer(formula_text)
                tokens = lexer.tokenize()
                parser = Parser(tokens)
                ast = parser.parse()

                if isinstance(ast, Expr):
                    math_latex = self.generate_expr(ast)
                    result = result[:start_pos] + f"${math_latex}$" + result[end_pos:]
            except Exception:
                # Parsing failed, leave as-is
                pass

        # Pattern -0.5: Parenthesized logical expressions
        # Detect expressions like "(p or q)", "(p and q)", "((p => r) and (q => r))"
        # Also handles "(not p => not q)" which Pattern -1 misses due to greedy matching
        # Use balanced parenthesis matching to handle nested expressions
        paren_matches = self._find_balanced_parens(result)

        for start_pos, end_pos in reversed(paren_matches):
            # Check if already in math mode
            before = result[:start_pos]
            dollars_before = before.count("$")
            if dollars_before % 2 == 1:
                continue

            paren_text = result[start_pos:end_pos]

            # Only process if it contains logical operators or keywords
            # Look for: or, and, not, =>, <=>
            has_logic = bool(
                re.search(r"\bor\b", paren_text)
                or re.search(r"\band\b", paren_text)
                or re.search(r"\bnot\b", paren_text)
                or "=>" in paren_text
                or "<=>" in paren_text
            )

            if not has_logic:
                continue

            # Try to parse as logical expression
            try:
                lexer = Lexer(paren_text)
                tokens = lexer.tokenize()
                parser = Parser(tokens)
                ast = parser.parse()

                if isinstance(ast, Expr):
                    math_latex = self.generate_expr(ast)
                    result = result[:start_pos] + f"${math_latex}$" + result[end_pos:]
            except Exception:
                # Parsing failed, leave as-is (might be prose)
                pass

        # Pattern 0: Standalone superscripts (MUST come before other patterns)
        # Match: identifier/number followed by ^ and exponent
        # Examples: x^2, a_i^2, 2^n, x^{2n}
        # Strategy: Match \w+^{?[\w]+}? but NOT if already in math mode
        superscript_pattern = r"(\w+_?\w*)\^(\{[^}]+\}|\w+)"

        matches = list(re.finditer(superscript_pattern, result))
        for match in reversed(matches):
            start_pos = match.start()
            end_pos = match.end()

            # Check if already in math mode
            before = result[:start_pos]
            dollars_before = before.count("$")
            if dollars_before % 2 == 1:
                continue  # Already in math mode

            # Check if this looks like sequence concatenation (<x> ^ <y>)
            # Look for closing > before the ^
            context_before = result[max(0, start_pos - 10) : start_pos]
            if ">" in context_before and context_before.rstrip().endswith(">"):
                continue  # This is sequence concatenation, skip

            expr = match.group(0)
            # Wrap in math mode: x^2 → $x^{2}$
            result = result[:start_pos] + f"${expr}$" + result[end_pos:]

        # Pattern 1: Set expressions { ... }
        # Find balanced braces (handles nested braces)
        brace_matches = self._find_balanced_braces(result)

        # Process matches in reverse order to preserve positions
        for start_pos, end_pos in reversed(brace_matches):
            math_text = result[start_pos:end_pos]
            try:
                # Try to parse as math expression
                lexer = Lexer(math_text)
                tokens = lexer.tokenize()
                parser = Parser(tokens)
                ast = parser.parse()

                # Check if it's a set expression (comprehension or literal)
                if isinstance(ast, (SetComprehension, SetLiteral)):
                    # Generate LaTeX for the expression
                    math_latex = self.generate_expr(ast)
                    # Wrap in $...$
                    result = result[:start_pos] + f"${math_latex}$" + result[end_pos:]
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
                            # Check if parsed expression contains prose words
                            # (due to space-separated application)
                            prose_words = {
                                "is",
                                "are",
                                "be",
                                "was",
                                "were",
                                "true",
                                "false",
                                "the",
                                "a",
                                "an",
                                "in",
                                "on",
                                "at",
                                "to",
                                "of",
                                "for",
                                "with",
                                "as",
                                "by",
                                "from",
                                "that",
                                "syntax",
                                "valid",
                                "here",
                                "there",
                            }

                            # Check if math_text ends with any prose words
                            # Split and check last few tokens
                            text_words = math_text.lower().split()
                            if text_words and text_words[-1] in prose_words:
                                # Contains prose word - try shorter substring
                                continue
                            if len(text_words) >= 2 and text_words[-2] in prose_words:
                                # Second-to-last word is prose - try shorter
                                continue

                            # Check if we're cutting off a word ("is" -> "i" + "s")
                            if end_pos < len(result) and end_pos > 0:
                                prev_char = result[end_pos - 1]
                                next_char = result[end_pos]
                                # If both sides are alphanumeric, splitting a word
                                if prev_char.isalnum() and next_char.isalnum():
                                    # We're in the middle of a word - skip this
                                    continue

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

        # Pattern 2.5: Type declarations (identifier : type_expression)
        # Match patterns like "large_coins : Collection -> N"
        # This must come before Pattern 3 to catch the identifier before the colon
        type_decl_pattern = (
            r"\b([a-zA-Z_]\w*)\s*:\s*([a-zA-Z_][\w\s\*\(\)\[\]<>,\+\->|]+)"
        )

        matches = list(re.finditer(type_decl_pattern, result))
        for match in reversed(matches):
            start_pos = match.start()
            end_pos = match.end()

            # Check if already in math mode
            before = result[:start_pos]
            dollars_before = before.count("$")
            if dollars_before % 2 == 1:
                continue  # Already in math mode

            # Extract the matched expression
            expr = match.group(0)

            # Try to parse as a type declaration
            try:
                lexer = Lexer(expr)
                tokens = lexer.tokenize()
                parser = Parser(tokens)
                ast = parser.parse()

                # If it parses successfully, generate LaTeX
                if isinstance(ast, Expr):
                    math_latex = self.generate_expr(ast)
                    result = result[:start_pos] + f"${math_latex}$" + result[end_pos:]
            except Exception:
                # If parsing fails, check if this looks like prose (not math)
                # Common English words that appear in prose but not in math
                prose_words = {
                    "the",
                    "a",
                    "an",
                    "is",
                    "are",
                    "was",
                    "were",
                    "be",
                    "been",
                    "have",
                    "has",
                    "had",
                    "do",
                    "does",
                    "did",
                    "will",
                    "would",
                    "should",
                    "could",
                    "may",
                    "might",
                    "must",
                    "can",
                    "this",
                    "that",
                    "these",
                    "those",
                    "whatever",
                    "whoever",
                    "of",
                    "for",
                    "with",
                    "as",
                    "by",
                    "from",
                    "to",
                    "in",
                    "on",
                    "at",
                }
                expr_words = set(expr.lower().split())
                if expr_words & prose_words:
                    # Contains prose words - skip this match
                    continue

                # If parsing fails, manually process the identifier and operators
                # Extract identifier from "identifier : type_expr" pattern
                match_parts = re.match(r"([a-zA-Z_]\w*)\s*:\s*(.+)", expr)
                if match_parts:
                    identifier_name = match_parts.group(1)
                    type_part = match_parts.group(2)

                    # Process identifier through normal logic for underscore handling
                    id_node = Identifier(line=0, column=0, name=identifier_name)
                    identifier_latex = self._generate_identifier(id_node)

                    # Convert operators in type part
                    type_latex = type_part.replace("->", r"\fun")

                    # Combine
                    full_latex = f"{identifier_latex} : {type_latex}"
                    result = result[:start_pos] + f"${full_latex}$" + result[end_pos:]
                else:
                    # Fallback: just convert operators
                    expr_with_ops = expr.replace("->", r"\fun")
                    result = (
                        result[:start_pos] + f"${expr_with_ops}$" + result[end_pos:]
                    )

        # Pattern 2.75: Function application followed by operator
        # Match: func_name arg operator value (e.g., "cumulative_total hd <= 12000")
        # ONLY matches identifiers with underscores to avoid false positives with prose
        # This must come before Pattern 3 to catch function applications
        math_op_pattern = r"(\+->|-\|>|<-\||->|>->|>->>|<=>|=>|>=|<=|!=|>|<|=)"
        func_app_pattern = (
            r"\b([a-zA-Z_]\w*_\w+)\s+"  # Function name (must contain underscore)
            r"([a-zA-Z_]\w*)\s*"  # Argument
            + math_op_pattern  # Operator
            + r"\s*([a-zA-Z_0-9]\w*)"  # Value
        )

        matches = list(re.finditer(func_app_pattern, result))
        for match in reversed(matches):
            start_pos = match.start()
            end_pos = match.end()

            # Check if already in math mode
            before = result[:start_pos]
            dollars_before = before.count("$")
            if dollars_before % 2 == 1:
                continue  # Already in math mode

            expr = match.group(0)

            # Try to parse the full expression
            try:
                lexer = Lexer(expr)
                tokens = lexer.tokenize()
                parser = Parser(tokens)
                ast = parser.parse()

                if isinstance(ast, Expr):
                    math_latex = self.generate_expr(ast)
                    result = result[:start_pos] + f"${math_latex}$" + result[end_pos:]
            except Exception:
                # If parsing fails, manually process components
                # Extract: func_name arg operator value
                parts = expr.split()
                if len(parts) >= 3:
                    func_name = parts[0]
                    arg_name = parts[1]
                    op_and_value = " ".join(parts[2:])

                    # Process function identifier
                    func_node = Identifier(line=0, column=0, name=func_name)
                    func_latex = self._generate_identifier(func_node)

                    # Process argument identifier
                    arg_node = Identifier(line=0, column=0, name=arg_name)
                    arg_latex = self._generate_identifier(arg_node)

                    # Convert operators in rest
                    op_and_value_latex = op_and_value.replace("<=", r"\leq")
                    op_and_value_latex = op_and_value_latex.replace(">=", r"\geq")
                    op_and_value_latex = op_and_value_latex.replace("!=", r"\neq")

                    # Combine as function application
                    full_latex = f"{func_latex}({arg_latex}) {op_and_value_latex}"
                    result = result[:start_pos] + f"${full_latex}$" + result[end_pos:]

        # Pattern 3: Simple inline math expressions (x > 1, f +-> g, etc.)
        # Match expressions with math operators that need wrapping
        # Strategy: Match sequences of identifiers/numbers connected by operators

        # All operators that need math mode (already defined above for Pattern 2.75)

        # Pattern: identifier/number, followed by (operator identifier/number)+
        # This matches chains like "p <=> x > 1"
        full_pattern = (
            r"\b([a-zA-Z_]\w*)\s*"  # First identifier
            + math_op_pattern  # Operator
            + r"\s*([a-zA-Z_0-9]\w*)"  # Second operand
            + r"(?:\s*"
            + math_op_pattern
            + r"\s*([a-zA-Z_0-9]\w*))*"  # More ops
        )

        matches = list(re.finditer(full_pattern, result))

        # Process matches in reverse order to preserve positions
        for match in reversed(matches):
            # Check if already in math mode (look for $ before)
            start_pos = match.start()
            end_pos = match.end()

            # Look backwards for $
            before = result[:start_pos]

            # Count $ symbols before this position
            dollars_before = before.count("$")
            # If odd number of $, we're already in math mode
            if dollars_before % 2 == 1:
                continue

            # Extract the matched expression
            expr = match.group(0)

            # Convert the operator to LaTeX
            try:
                # Try to parse and generate proper LaTeX
                lexer = Lexer(expr)
                tokens = lexer.tokenize()
                parser = Parser(tokens)
                ast = parser.parse()

                # Generate LaTeX for the expression if it's an Expr
                if isinstance(ast, Expr):
                    math_latex = self.generate_expr(ast)
                    # Wrap in $...$
                    result = result[:start_pos] + f"${math_latex}$" + result[end_pos:]
            except Exception:
                # If parsing fails, just wrap as-is
                # Still need to convert operators
                result = result[:start_pos] + f"${expr}$" + result[end_pos:]

        return result

    def _generate_truth_table(self, node: TruthTable) -> list[str]:
        """Generate LaTeX for truth table."""
        lines: list[str] = []

        # Start table environment with vertical bars between columns (not at edges)
        # Spacing is controlled by part labels
        num_cols = len(node.headers)
        col_spec = "|".join(["c"] * num_cols)
        lines.append(r"\begin{tabular}{" + col_spec + r"}")

        # Generate header row (last column in bold as it's the overall assessment)
        header_parts: list[str] = []
        for i, header in enumerate(node.headers):
            # Convert operators to LaTeX symbols
            header_latex = self._convert_operators_to_latex(header)
            # Last column in bold, all in math mode
            if i == len(node.headers) - 1:
                header_parts.append(r"$\mathbf{" + header_latex + r"}$")
            else:
                header_parts.append(f"${header_latex}$")
        lines.append(" & ".join(header_parts) + r" \\")
        lines.append(r"\hline")

        # Generate data rows (lowercase t/f in italic, last column in bold non-italic)
        for row in node.rows:
            row_parts = []
            for i, val in enumerate(row):
                # Lowercase t/f for truth values
                cell = val.lower() if val in ("T", "F") else val
                # Last column in bold (no italic), others in italic
                if i == len(row) - 1:
                    row_parts.append(r"\textbf{" + cell + r"}")
                else:
                    row_parts.append(r"\textit{" + cell + r"}")
            lines.append(" & ".join(row_parts) + r" \\")

        lines.append(r"\end{tabular}")
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

    def _escape_latex(self, text: str) -> str:
        """Escape LaTeX special characters.

        Escapes: & % $ # _ { } ~ ^ \
        Does NOT convert operators or detect formulas.
        """
        # Escape backslash first to avoid double-escaping
        result = text.replace("\\", r"\textbackslash{}")
        # Escape other special characters
        result = result.replace("&", r"\&")
        result = result.replace("%", r"\%")
        result = result.replace("$", r"\$")
        result = result.replace("#", r"\#")
        result = result.replace("_", r"\_")
        result = result.replace("{", r"\{")
        result = result.replace("}", r"\}")
        result = result.replace("~", r"\textasciitilde{}")
        result = result.replace("^", r"\textasciicircum{}")
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
        r"""Generate LaTeX for equivalence chain using array environment.

        Uses standard LaTeX array{lll} instead of amsmath align* to avoid
        package dependency. Wraps array in display math \[...\] for proper
        spacing without confusing fuzz type checker.
        """
        lines: list[str] = []

        lines.append(r"\[")
        # Use ll@{\hspace{2em}}l to add extra space before justification column
        lines.append(r"\begin{array}{ll@{\hspace{2em}}l}")

        # Generate steps
        for i, step in enumerate(node.steps):
            expr_latex = self.generate_expr(step.expression)

            # All lines start with & for consistent left alignment
            # First step: & expression; subsequent: &\Leftrightarrow expression
            line = r"& " + expr_latex if i == 0 else r"&\Leftrightarrow " + expr_latex

            # Add justification if present (flush right)
            if step.justification:
                escaped_just = self._escape_justification(step.justification)
                line += r" & [\mbox{" + escaped_just + "}]"

            # Add line break except for last line
            if i < len(node.steps) - 1:
                line += r" \\"

            lines.append(line)

        lines.append(r"\end{array}")
        lines.append(r"\]")
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
        """Generate LaTeX for free type definition (Phase 17: Recursive Free Types).

        Examples:
        - Status ::= active | inactive (simple branches)
        - Tree ::= stalk | leaf \\ldata N \\rdata |
          branch \\ldata Tree \\cross Tree \\rdata
        """
        lines: list[str] = []

        # Generate each branch with proper LaTeX formatting
        branch_strs: list[str] = []
        for branch in node.branches:
            if branch.parameters is None:
                # Simple branch: just the name
                branch_strs.append(branch.name)
            else:
                # Parameterized constructor: name \\ldata params \\rdata
                params_latex = self.generate_expr(branch.parameters)
                branch_strs.append(f"{branch.name} \\ldata {params_latex} \\rdata")

        # Join branches with |
        branches_str = " | ".join(branch_strs)

        # Wrap in zed environment for proper formatting
        lines.append(f"\\begin{{zed}}{node.name} ::= {branches_str}\\end{{zed}}")
        lines.append("")
        return lines

    def _generate_abbreviation(self, node: Abbreviation) -> list[str]:
        r"""Generate LaTeX for abbreviation definition.

        Phase 9 enhancement: Supports optional generic parameters.

        Note: Abbreviations must be wrapped in \begin{zed}...\end{zed}
        for fuzz type checker to recognize them.
        """
        lines: list[str] = []
        expr_latex = self.generate_expr(node.expression)

        # Wrap in zed environment for fuzz compatibility
        if node.generic_params:
            params_str = ", ".join(node.generic_params)
            abbrev = f"[{params_str}]{node.name} == {expr_latex}"
            lines.append(f"\\begin{{zed}}{abbrev}\\end{{zed}}")
        else:
            abbrev = f"{node.name} == {expr_latex}"
            lines.append(f"\\begin{{zed}}{abbrev}\\end{{zed}}")

        lines.append("")
        return lines

    def _generate_axdef(self, node: AxDef) -> list[str]:
        """Generate LaTeX for axiomatic definition.

        Phase 9 enhancement: Supports optional generic parameters.
        Multiple declarations appear on separate lines with line breaks.
        """
        lines: list[str] = []

        # Add generic parameters if present
        if node.generic_params:
            params_str = ", ".join(node.generic_params)
            lines.append(f"\\begin{{axdef}}[{params_str}]")
        else:
            lines.append(r"\begin{axdef}")

        # Generate declarations on separate lines
        if node.declarations:
            for i, decl in enumerate(node.declarations):
                # Process variable through identifier logic for underscore handling
                var_latex = self._generate_identifier(
                    Identifier(line=0, column=0, name=decl.variable)
                )
                type_latex = self.generate_expr(decl.type_expr)

                # Add line break after each declaration except the last
                if i < len(node.declarations) - 1:
                    lines.append(f"{var_latex} : {type_latex} \\\\")
                else:
                    lines.append(f"{var_latex} : {type_latex}")

        # Generate where clause if predicates exist
        if node.predicates:
            lines.append(r"\where")
            for pred in node.predicates:
                pred_latex = self.generate_expr(pred)
                lines.append(pred_latex)

        lines.append(r"\end{axdef}")
        lines.append("")

        return lines

    def _generate_gendef(self, node: GenDef) -> list[str]:
        """Generate LaTeX for generic definition.

        Generic definitions always have generic parameters (required).
        Multiple declarations appear on separate lines with line breaks.
        """
        lines: list[str] = []

        # Generic parameters are always present for gendef
        params_str = ", ".join(node.generic_params)
        lines.append(f"\\begin{{gendef}}[{params_str}]")

        # Generate declarations on separate lines
        if node.declarations:
            for i, decl in enumerate(node.declarations):
                # Process variable through identifier logic for underscore handling
                var_latex = self._generate_identifier(
                    Identifier(line=0, column=0, name=decl.variable)
                )
                type_latex = self.generate_expr(decl.type_expr)

                # Add line break after each declaration except the last
                if i < len(node.declarations) - 1:
                    lines.append(f"  {var_latex}: {type_latex} \\\\")
                else:
                    lines.append(f"  {var_latex}: {type_latex}")

        # Generate where clause if predicates exist
        if node.predicates:
            lines.append(r"\where")
            for pred in node.predicates:
                pred_latex = self.generate_expr(pred)
                # Add indentation and line break for predicates
                lines.append(f"  {pred_latex} \\\\")

        lines.append(r"\end{gendef}")
        lines.append("")

        return lines

    def _generate_schema(self, node: Schema) -> list[str]:
        """Generate LaTeX for schema definition.

        Phase 9 enhancement: Supports optional generic parameters.
        Phase 13 enhancement: Supports anonymous schemas (name=None).
        Multiple declarations appear on separate lines with line breaks.
        """
        lines: list[str] = []

        # Determine schema name (empty string for anonymous)
        schema_name = node.name if node.name is not None else ""

        # Add generic parameters if present
        if node.generic_params:
            params_str = ", ".join(node.generic_params)
            lines.append(f"\\begin{{schema}}{{{schema_name}}}[{params_str}]")
        else:
            lines.append(r"\begin{schema}{" + schema_name + "}")

        # Generate declarations on separate lines
        if node.declarations:
            for i, decl in enumerate(node.declarations):
                # Process variable through identifier logic for underscore handling
                var_latex = self._generate_identifier(
                    Identifier(line=0, column=0, name=decl.variable)
                )
                type_latex = self.generate_expr(decl.type_expr)

                # Add line break after each declaration except the last
                if i < len(node.declarations) - 1:
                    lines.append(f"{var_latex} : {type_latex} \\\\")
                else:
                    lines.append(f"{var_latex} : {type_latex}")

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

        # Generate proof tree in display math without centering
        # Use negative hspace to shift left and compensate for centering
        proof_latex = self._generate_proof_node_infer(node.conclusion)
        lines.append(r"\noindent")
        lines.append(r"$\displaystyle")
        lines.append(proof_latex)
        lines.append(r"$")
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

        # Check for assumption reference FIRST (before checking children)
        # Pattern: "from N" where N is a digit
        # This should render as boxed assumption notation regardless of children
        if node.justification:
            just_lower = node.justification.lower()
            # Check if this is purely a "from N" reference (not "rule from N")
            from_only_match = re.match(r"^\s*from\s+(\d+)\s*$", just_lower)
            if from_only_match:
                ref_label = from_only_match.group(1)
                # Render as boxed assumption reference
                # If this node has children, they should be rendered below
                if node.children:
                    # Generate children as premises
                    child_latexes = [
                        self._generate_proof_node_infer(child)
                        for child in node.children
                        if isinstance(child, ProofNode)
                    ]
                    premises = "\n  ".join(child_latexes)
                    boxed = f"\\ulcorner {expr_latex} \\urcorner^{{[{ref_label}]}}"
                    return f"\\infer{{{boxed}}}{{\n  {premises}\n}}"
                else:
                    # Leaf node - just return the boxed reference
                    return f"\\ulcorner {expr_latex} \\urcorner^{{[{ref_label}]}}"

        # If no children, return expression (possibly with justification)
        if not node.children:
            # Check if justification indicates a reference (not a derivation rule)
            if node.justification:
                just_lower = node.justification.lower()
                # References like "copy", etc. should not be wrapped in \infer
                if "copy" in just_lower:
                    # Just return the expression - it's a reference
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
                elif child.is_assumption and current_group:
                    # Assumptions should be laid out horizontally with siblings
                    # for proper spacing (e.g., in => elim with p => r & p)
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
        # Put & on its own line to avoid LaTeX parser issues with nested contexts
        non_case_premises = ["\n&\n".join(group) for group in child_groups]

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
                    # raiseproof naturally protects nested & from outer \infer alignment
                    raised = f"\\raiseproof{{{height}ex}}{{{case_latex}}}"
                else:
                    # Subsequent cases: taller + horizontal spacing
                    height = 18 + (depth * 4)  # Much taller for subsequent cases
                    # raiseproof naturally protects nested & from outer \infer alignment
                    raised = f"\\hskip 6em \\raiseproof{{{height}ex}}{{{case_latex}}}"

                raised_cases.append(raised)

            # Combine: disjunction premises first (if any), then raised case branches
            if disjunction_premises:
                all_premises = disjunction_premises + raised_cases
            else:
                # No disjunction - might be other premises before cases
                all_premises = non_case_premises + raised_cases

            # Put & on its own line to avoid LaTeX parser issues with nested contexts
            premises = "\n&\n".join(all_premises)
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
            return f"\\mbox{{case {case.case_name}}}"

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

        # Generate sibling group
        # When multiple siblings exist in a case, the LAST one wraps earlier
        # This ensures each \raiseproof contains exactly ONE top-level \infer
        if sibling_group:
            if len(sibling_group) == 1:
                # Single step - straightforward
                current_result = self._generate_proof_node_infer(sibling_group[0])
            else:
                # Multiple sibling steps: last step wraps earlier ones as premises
                # Generate earlier siblings as complete inference trees
                earlier_parts = [
                    self._generate_proof_node_infer(s) for s in sibling_group[:-1]
                ]

                # Last step becomes the outer wrapper
                last_step = sibling_group[-1]
                expr_latex = self.generate_expr(last_step.expression)

                # Combine earlier siblings with last step's own premises
                all_premises = earlier_parts.copy()
                if last_step.children:
                    # Last step has its own children/premises too
                    for child in last_step.children:
                        if isinstance(child, ProofNode):
                            all_premises.append(self._generate_proof_node_infer(child))
                        elif isinstance(child, CaseAnalysis):
                            all_premises.append(self._generate_case_analysis(child))

                premises_str = " & ".join(all_premises) if all_premises else ""

                # Generate outer infer for last step
                if last_step.justification:
                    just = self._format_justification_label(last_step.justification)
                    current_result = (
                        f"\\infer[{just}]{{{expr_latex}}}{{{premises_str}}}"
                    )
                else:
                    current_result = f"\\infer{{{expr_latex}}}{{{premises_str}}}"
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

            # Convert operator to LaTeX (no $ delimiters - already in math mode)
            op_latex = operator_part.replace("<=>", r"\Leftrightarrow")
            op_latex = op_latex.replace("=>", r"\Rightarrow")
            op_latex = re.sub(r"\band\b", r"\\land", op_latex)
            op_latex = re.sub(r"\bor\b", r"\\lor", op_latex)
            op_latex = re.sub(r"\bnot\b", r"\\lnot", op_latex)

            # Format as: operator-rule^{[label]}
            # Use \textrm instead of \mbox to work correctly in math mode contexts
            return f"{op_latex}\\textrm{{-{rule_name}}}^{{[{label_num}]}}"

        # Check for rule subscript pattern: "operator rule N" (like "and elim 1")
        # Match: operator + rule name + number (1 or 2)
        subscript_pattern = r"^(.*?)\s+(intro|elim)\s*([12])$"
        match = re.match(subscript_pattern, just)

        if match:
            operator_part = match.group(1).strip()
            rule_name = match.group(2)
            subscript_num = match.group(3)

            # Convert operator to LaTeX (no $ delimiters - already in math mode)
            op_latex = operator_part.replace("<=>", r"\Leftrightarrow")
            op_latex = op_latex.replace("=>", r"\Rightarrow")
            op_latex = re.sub(r"\band\b", r"\\land", op_latex)
            op_latex = re.sub(r"\bor\b", r"\\lor", op_latex)
            op_latex = re.sub(r"\bnot\b", r"\\lnot", op_latex)

            # Format as: operator-rule-number (just regular text, no subscript)
            # Use \textrm instead of \mbox to work correctly in math mode contexts
            return f"{op_latex}\\textrm{{-{rule_name}-{subscript_num}}}"

        # No special pattern - process normally
        # Replace logical operators with LaTeX symbols
        result = just.replace("<=>", r"\Leftrightarrow")
        result = result.replace("=>", r"\Rightarrow")
        result = re.sub(r"\band\b", r"\\land", result)
        result = re.sub(r"\bor\b", r"\\lor", result)
        result = re.sub(r"\bnot\b", r"\\lnot", result)

        # Already in math mode - don't need extra wrapping
        # Just use \mathrm{} for text parts to get roman font
        for word in [
            "elim",
            "intro",
            "assumption",
            "premise",
            "from",
            "case",
            "contradiction",
            "middle",
            "excluded",
            "false",
        ]:
            # Replace text words with \mathrm{} for roman font in math mode
            result = re.sub(rf"\b{word}\b", rf"\\mathrm{{{word}}}", result)

        return result
