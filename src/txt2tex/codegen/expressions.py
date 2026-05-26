"""Codegen handlers for general expression constructs.

Covers: Identifier, Number, UnaryOp, BinaryOp, Quantifier (logical /
lambda / schema), Lambda, SetComprehension, FunctionApp, Range,
Conditional, GuardedCases, GuardedBranch.  Includes the quantifier /
lambda chain helpers and the schema-binding emitter that are only
called from this family.

This mixin is composed into :class:`LaTeXGenerator` via multiple
inheritance.  Methods are byte-identical to their counterparts in the
pre-refactor monolithic ``latex_gen.py``; only their file location has
changed.
"""

from __future__ import annotations

from txt2tex.ast_nodes import (
    BagLiteral,
    BinaryOp,
    Conditional,
    Expr,
    FunctionApp,
    GenericInstantiation,
    GuardedBranch,
    GuardedCases,
    Identifier,
    Lambda,
    Number,
    Quantifier,
    Range,
    RelationalImage,
    SchemaBinding,
    SequenceLiteral,
    SetComprehension,
    SetLiteral,
    StringLit,
    Subscript,
    Superscript,
    Tuple,
    TupleProjection,
    UnaryOp,
)
from txt2tex.codegen._dispatch import CodegenDispatch, expr_register
from txt2tex.free_vars import expr_free_vars


def _is_atomic_predicate(node: Expr) -> bool:
    """Return True when node is an atomic predicate in fuzz's grammar.

    Atomic predicates (Z RM §3.8.1, fuzz parser restriction):

    1. A predicate name — ``Identifier``.
    2. The constants ``true`` and ``false`` — also ``Identifier``.
    3. A relation application ``e_1 R e_2`` — ``BinaryOp``.  These are
       already wrapped by the BinaryOp rule in ``_generate_unary_op``,
       so treating them as atomic here prevents double-parenthesisation.
    4. A schema reference — ``Identifier`` (same as category 1).
    5. An already-parenthesised predicate — ``BinaryOp`` with
       ``explicit_parens=True`` (the BinaryOp generator emits its own
       outer parens; the UnaryOp handler skips the BinaryOp rule for it).

    Quantifiers, lambdas, and all other compound forms return False.
    """
    return isinstance(node, (Identifier, Number, BinaryOp))


class _ExpressionsCodegen(CodegenDispatch):  # pyright: ignore[reportUnusedClass]
    """Mixin: handlers for general expression constructs."""

    @expr_register.register(Identifier)
    def _generate_identifier(
        self,
        node: Identifier,
        parent: Expr | None = None,
    ) -> str:
        """Generate LaTeX for identifier with smart underscore handling.

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

        # Handle compound identifiers with postfix closure operators (R+, R*, R~, Rr)
        # Appears in abbreviation and schema names
        # (partial support, GitHub #3 still open)
        if name.endswith("+"):
            base = name[:-1]
            # Render as R^+ (transitive closure)
            base_id = Identifier(line=0, column=0, name=base)
            return f"{self._generate_identifier(base_id)}^+"
        if name.endswith("*"):
            base = name[:-1]
            # Render as R^* (reflexive-transitive closure)
            base_id = Identifier(line=0, column=0, name=base)
            return f"{self._generate_identifier(base_id)}^*"
        if name.endswith("~"):
            base = name[:-1]
            # Render as R^{-1} (standard) or R^{\sim} (fuzz)
            base_id = Identifier(line=0, column=0, name=base)
            base_latex = self._generate_identifier(base_id)
            return self._get_closure_operator_latex("~", base_latex)

        # Check if this is an operator/function from UNARY_OPS dictionary
        # This handles operators like id, inv, dom, ran when used as identifiers
        # (e.g., in generic instantiations like id[Person])
        # Skip postfix operators (~, +, *) which have special handling
        if name in self.UNARY_OPS and name not in ["~", "+", "*"]:
            return self.UNARY_OPS[name]

        # Mathematical type names: use blackboard bold (or fuzz built-in types)
        # N = naturals, Z = integers, N1 = positive integers (≥ 1)
        # Only convert N and Z, not Q/R/C which are commonly used as variables
        type_latex = self._get_type_latex(name)
        if type_latex is not None:
            return type_latex

        # No underscore: return as-is
        if "_" not in name:
            return name

        # Check for multi-word identifier pattern
        # Heuristic: subscripts only for 1-2 char suffixes (e.g., z_1, x_10)
        # Anything 3+ chars is a multi-word identifier (e.g., cumulative_total)
        parts = name.split("_")

        # Multiple underscores → multi-word identifier
        if len(parts) > 2:
            return self._format_multiword_identifier(name)

        # Single underscore: prioritize suffix length for subscript detection
        if len(parts) == 2:
            prefix, suffix = parts
            # Priority 1: Single-char suffix → subscript (e.g., x_1, count_N)
            if len(suffix) == 1:
                if self.use_fuzz:
                    # Fuzz: numeric subscripts are decorations (bare _)
                    # Letter suffixes are identifier parts (escaped \_)
                    if suffix.isdigit():
                        return f"{prefix}_{suffix}"  # z_1 (decoration)
                    return f"{prefix}\\_{suffix}"  # length\_L (identifier)
                # Standard LaTeX: bare underscore for subscript
                return f"{prefix}_{suffix}"
            # Priority 2: Two-char suffix → subscript with braces (e.g., x_10)
            if len(suffix) == 2:
                if self.use_fuzz:
                    # Fuzz: all-numeric subscripts are decorations (bare _)
                    # Mixed/letter suffixes are identifier parts (escaped \_)
                    if suffix.isdigit():
                        return f"{prefix}_{{{suffix}}}"  # z_10 (decoration)
                    return f"{prefix}\\_{{{suffix}}}"  # state\_AB (identifier)
                # Standard LaTeX: bare underscore
                return f"{prefix}_{{{suffix}}}"
            # Priority 3: Long suffix → multi-word identifier (e.g., cumulative_total)
            # len(suffix) >= 3  # noqa: ERA001
            return self._format_multiword_identifier(name)

        # Fallback: multi-word identifier
        return self._format_multiword_identifier(name)

    @expr_register.register(Number)
    def _generate_number(self, node: Number, parent: Expr | None = None) -> str:
        """Generate LaTeX for number."""
        return node.value

    @expr_register.register(UnaryOp)
    def _generate_unary_op(self, node: UnaryOp, parent: Expr | None = None) -> str:
        """Generate LaTeX for unary operation.

        Unary operators bind more tightly than all binary operators (see
        UNARY_PRECEDENCE — level 20 exceeds the highest binary level of 11).
        Parentheses are added around binary-operator operands using this
        table as the single source of truth (Gap #2).

        Postfix operators (~, +, *) are rendered as superscripts on the
        operand, not as prefix operators.
        """
        op_latex = self.UNARY_OPS.get(node.operator)
        if op_latex is None:
            raise ValueError(f"Unknown unary operator: {node.operator}")

        operand = self.generate_expr(node.operand)

        # UNARY_PRECEDENCE-driven rule: unary always binds tighter than binary.
        # Wrap the operand when it is a BinaryOp whose precedence is below the
        # unary level (which is every binary operator in the table).
        # Skip when the BinaryOp already carries explicit_parens — it will emit
        # its own wrapping parens.
        if isinstance(node.operand, BinaryOp) and not node.operand.explicit_parens:
            operand = f"({operand})"

        # Fuzz grammar quirk: # binds less tightly than function application.
        # Fuzz manual §2.4: "# s(i)" is parsed as "(# s)(i)"; we want
        # "# (s(i))".  Wrap FunctionApp operands of # in fuzz mode.
        if self.use_fuzz and isinstance(node.operand, FunctionApp):
            operand = f"({operand})"

        # Fuzz grammar quirk: # followed by a prefix-function unary operator
        # (dom, ran, …) would be parsed as "(# dom) R" without parens.
        # Fuzz manual §2.3: prefix generic symbols are operator symbols that
        # require their argument to be a simple expression or a parenthesised
        # compound.  Wrap to yield "# (dom R)".
        if (
            self.use_fuzz
            and node.operator == "#"
            and isinstance(node.operand, UnaryOp)
            and node.operand.operator in self._FUZZ_FUNCTION_LIKE_UNARY
        ):
            operand = f"({operand})"

        # Fuzz grammar rule (Z RM §3.7 / fuzz §2.3): prefix-generic operators
        # require an atomic Expression0 as their immediate right operand.
        # A nested prefix application is not atomic, so wrap it.
        # Generalised form subsumes the earlier bigcup/bigcap-only rule:
        # any _FUZZ_FUNCTION_LIKE_UNARY outer with a _FUZZ_FUNCTION_LIKE_UNARY
        # inner operand must be wrapped.  Example: \ran (\bigcup (\ran s)).
        if (
            self.use_fuzz
            and node.operator in self._FUZZ_FUNCTION_LIKE_UNARY
            and isinstance(node.operand, UnaryOp)
            and node.operand.operator in self._FUZZ_FUNCTION_LIKE_UNARY
        ):
            operand = f"({operand})"

        # Fuzz parser restriction (jms ruling 2026-05-22, Z RM §3.8.1):
        # \lnot requires an atomic predicate as its direct operand.
        # Quantifiers, lambdas, and other non-atomic forms must be parenthesised.
        # BinaryOp operands are already wrapped by the rule above (line 1056),
        # so only non-atomic non-BinaryOp nodes need treatment here.
        if (
            self.use_fuzz
            and node.operator == "lnot"
            and not _is_atomic_predicate(node.operand)
        ):
            operand = f"({operand})"

        # Check if this is a postfix operator (rendered as superscript)
        if node.operator in {"~", "+", "*"}:
            return self._get_closure_operator_latex(node.operator, operand)
        # Generic instantiation operators (P, P1, F, F1)
        # Per fuzz manual p.23: prefix generic symbols are operator symbols,
        # LaTeX inserts thin space automatically - NO TILDE needed
        if node.operator in {"P", "P1", "F", "F1"}:
            # Generic instantiation: \power X or \finset X (no tilde)
            return f"{op_latex} {operand}"
        # Prefix: operator operand
        # Special case: no space for unary minus
        if node.operator == "-":
            return f"{op_latex}{operand}"
        return f"{op_latex} {operand}"

    @expr_register.register(BinaryOp)
    def _generate_binary_op(self, node: BinaryOp, parent: Expr | None = None) -> str:
        """Generate LaTeX for binary operation.

        Supports line breaks with \\\\ for long expressions.
        """
        op_latex = self.BINARY_OPS.get(node.operator)
        if op_latex is None:
            raise ValueError(f"Unknown binary operator: {node.operator}")

        # o9 (relational composition) uses context-sensitive LaTeX.
        # fuzz.sty declares:
        #   \comp  math class 2 (binary op)   — required inside Z environments
        #   \semi  math class 3 (closing/separator) — correct in $...$, display math
        # All other operators are context-independent.
        if node.operator == "o9" and self._in_z_paragraph:
            op_latex = r"\comp"

        # Apply fuzz-specific operator mappings
        op_latex = self._map_binary_operator(node.operator, op_latex)

        # Pass this node as parent to children
        left = self.generate_expr(node.left, parent=node)
        right = self.generate_expr(node.right, parent=node)

        # Add parentheses if needed for precedence and associativity
        if self._needs_parens(node.left, node, is_left_child=True):
            left = f"({left})"
        if self._needs_parens(node.right, node, is_left_child=False):
            right = f"({right})"

        # Check for line break after operator
        if node.line_break_after:
            # Multi-line expression: insert \\ and indent continuation.
            # In argue-block (array) context, do NOT use & for the continuation
            # prefix: & jumps to the right column, which would produce three cells
            # in a two-column array when the step also carries a justification.
            # The continuation stays in the left column without &; the justification
            # column separator is added later by _generate_argue_chain when needed.
            indent = self._get_indentation()
            result = f"{left} {op_latex} \\\\\n{indent} {right}"
        else:
            # Single-line expression
            result = f"{left} {op_latex} {right}"

        # Honor explicit parentheses from source
        # If the user explicitly wrote (expr), preserve those parentheses
        # regardless of precedence rules. This maintains semantic grouping clarity.
        if node.explicit_parens:
            result = f"({result})"

        return result

    def _collect_lambda_chain(
        self, node: Quantifier
    ) -> tuple[list[tuple[list[str], Expr | None, str]], Expr, Expr | None]:
        """Walk a nested lambda Quantifier chain and collect all bindings.

        Returns:
            A triple (bindings, predicate, expression) where:
            - bindings: list of (variables, raw_domain, domain_latex) triples,
              one per collected level
            - predicate: the innermost body (predicate before @ separator), or
              the un-collapsed inner Quantifier when a dependency stops early
            - expression: the expression after @, or None if absent/stopped

        The innermost Quantifier("lambda") node is the one whose body is NOT
        itself a Quantifier("lambda"); it carries the predicate and expression.

        When a later level's domain references a variable already accumulated
        in the chain, collection stops early: the returned predicate is the
        inner Quantifier node and expression is None (dependency-stop sentinel).
        """
        bindings: list[tuple[list[str], Expr | None, str]] = []
        accumulated_names: frozenset[str] = frozenset()
        current: Quantifier = node
        while True:
            domain_latex = (
                self.generate_expr(current.domain, parent=current)
                if current.domain is not None
                else ""
            )
            bindings.append((list(current.variables), current.domain, domain_latex))
            accumulated_names = accumulated_names | frozenset(current.variables)
            inner = current.body
            if isinstance(inner, Quantifier) and inner.quantifier == "lambda":
                # Check whether the next level's domain references a bound name.
                if inner.domain is not None:
                    inner_domain_free = expr_free_vars(inner.domain)
                    if inner_domain_free & accumulated_names:
                        # Dependency detected: stop here.
                        return bindings, inner, None
                current = inner
            else:
                # Base case: body is the predicate, expression is after @
                return bindings, current.body, current.expression

    def _generate_lambda_quantifier(
        self, node: Quantifier, parent: Expr | None = None
    ) -> str:
        """Emit Spivey-canonical LaTeX for multi-decl lambda Quantifier nodes.

        Collects the full binding chain into a single SchemaText and emits:
            \\lambda v0, ... : D0; v1, ... : D1; ... | predicate @ expression

        When a later domain references an earlier-bound variable (dependent domain),
        collection stops at the dependency boundary.  The prefix is emitted as a
        single-level lambda and the remainder is recursed into afresh.

        Wrapped in parentheses in fuzz mode when appearing inside an expression.
        """
        bindings, predicate, expression = self._collect_lambda_chain(node)

        colon = self._get_colon_separator()

        # Dependency-stop case: predicate is the un-collapsed inner Quantifier.
        if (
            isinstance(predicate, Quantifier)
            and predicate.quantifier == "lambda"
            and expression is None
        ):
            decl_parts: list[str] = []
            for variables, _raw_domain, domain_latex in bindings:
                vars_str = ", ".join(variables)
                decl_parts.append(f"{vars_str} {colon} {domain_latex}")
            schema_text = "; ".join(decl_parts)

            pipe_sep = self._get_mid_separator()
            # Recurse: the inner lambda will attempt its own collapse from scratch.
            inner_latex = self._generate_lambda_quantifier(predicate, parent=node)
            result = rf"\lambda {schema_text} {pipe_sep} {inner_latex}"
            if self.use_fuzz:
                result = f"({result})"
            return result

        # Normal full-collapse path.
        decl_parts = []
        for variables, _raw_domain, domain_latex in bindings:
            vars_str = ", ".join(variables)
            decl_parts.append(f"{vars_str} {colon} {domain_latex}")
        schema_text = "; ".join(decl_parts)

        parts = [r"\lambda", schema_text]

        # Predicate (before @) — always present in the multi-decl form
        pipe_sep = self._get_mid_separator()
        pred_latex = self.generate_expr(predicate, parent=node)
        parts.append(f"{pipe_sep} {pred_latex}")

        # Expression (after @)
        if expression is not None:
            bullet_sep = self._get_bullet_separator()
            expr_latex = self.generate_expr(expression, parent=node)
            parts.append(f"{bullet_sep} {expr_latex}")

        result = " ".join(parts)

        # Fuzz requires parentheses around every lambda expression
        if self.use_fuzz:
            result = f"({result})"

        return result

    def _collect_quantifier_chain(
        self, node: Quantifier
    ) -> tuple[list[tuple[list[str], Expr | None, str]], Expr, Expr | None, Quantifier]:
        """Walk a nested same-quantifier chain and collect all bindings.

        Mirrors _collect_lambda_chain but works for forall/exists/exists1/mu.
        Stops when the body is not a Quantifier with the same quantifier attribute.

        Returns:
            A 4-tuple (bindings, predicate, expression, innermost) where:
            - bindings: list of (variables, raw_domain, domain_latex) triples,
              one per collected level
            - predicate: the innermost body (predicate before @ or | separator),
              or the un-collapsed inner Quantifier when dependency stops early
            - expression: the expression after @, or None if absent/stopped
            - innermost: the innermost Quantifier node in the chain (carries
              the line_break_after_pipe / line_break_after_bullet flags that
              the parser set when scanning the actual `|` or `.` separator)

        When a later level's domain references a variable already accumulated
        in the chain, collection stops early: the returned predicate is the
        inner Quantifier node and expression is None (dependency-stop sentinel).
        """
        bindings: list[tuple[list[str], Expr | None, str]] = []
        accumulated_names: frozenset[str] = frozenset()
        current: Quantifier = node
        while True:
            domain_latex = (
                self.generate_expr(current.domain, parent=current)
                if current.domain is not None
                else ""
            )
            bindings.append((list(current.variables), current.domain, domain_latex))
            accumulated_names = accumulated_names | frozenset(current.variables)
            inner = current.body
            if isinstance(inner, Quantifier) and inner.quantifier == node.quantifier:
                # Check whether the next level's domain references a bound name.
                if inner.domain is not None:
                    inner_domain_free = expr_free_vars(inner.domain)
                    if inner_domain_free & accumulated_names:
                        # Dependency detected: stop here.
                        return bindings, inner, None, current
                current = inner
            else:
                return bindings, current.body, current.expression, current

    def _generate_logical_quantifier(
        self, node: Quantifier, parent: Expr | None = None
    ) -> str:
        """Emit Spivey-canonical LaTeX for multi-decl logical Quantifier nodes.

        Collects the full binding chain into a single SchemaText and emits one
        of two forms depending on whether a bullet (.) separator was present:

        Without bullet (body is the whole predicate, no constraint):
            \\forall v0 : D0; v1 : D1; ... @ predicate

        With bullet (body is a range constraint, expression is the predicate):
            \\forall v0 : D0; v1 : D1; ... | constraint @ expression

        Mu always uses | before its predicate, per Z RM §3.8:
            (\\mu v0 : D0; v1 : D1; ... | predicate @ expression)

        Single-decl nodes never reach this method; they flow through the
        existing _generate_quantifier body unchanged.
        """
        quant_latex = self.QUANTIFIERS[node.quantifier]
        bindings, predicate, expression, innermost = self._collect_quantifier_chain(
            node
        )

        colon = self._get_colon_separator()
        bullet_sep = self._get_bullet_separator()

        # Dependency-stop case: predicate is the un-collapsed inner Quantifier.
        if (
            isinstance(predicate, Quantifier)
            and predicate.quantifier == node.quantifier
            and expression is None
        ):
            decl_parts: list[str] = []
            for variables, _raw_domain, domain_latex in bindings:
                vars_str = ", ".join(variables)
                decl_parts.append(f"{vars_str} {colon} {domain_latex}")
            schema_text = "; ".join(decl_parts)

            # Recursively generate the inner quantifier (fresh collapse attempt).
            inner_latex = self._generate_logical_quantifier(predicate, parent=node)
            result = f"{quant_latex} {schema_text} {bullet_sep} {inner_latex}"

            if node.quantifier == "mu" and self.use_fuzz:
                return f"({result})"
            if node.quantifier != "mu" and self._quantifier_needs_parens(node, parent):
                return f"({result})"
            return result

        # Normal full-collapse path.
        decl_parts = []
        for variables, _raw_domain, domain_latex in bindings:
            vars_str = ", ".join(variables)
            decl_parts.append(f"{vars_str} {colon} {domain_latex}")
        schema_text = "; ".join(decl_parts)

        parts = [quant_latex, schema_text]

        self._quantifier_depth += 1
        indent = self._get_indentation()
        pred_latex = self.generate_expr(predicate, parent=node)
        self._quantifier_depth -= 1

        # Honour line_break_after_pipe / line_break_after_bullet from the
        # innermost Quantifier (where the parser scanned the actual `|` or
        # `.` separator). Collapsed chains otherwise drop these flags.
        pipe_break = innermost.line_break_after_pipe
        bullet_break = innermost.line_break_after_bullet

        if node.quantifier == "mu":
            # Mu always uses | before the predicate, then optional @ expression.
            pipe_sep = self._get_mid_separator()
            if pipe_break:
                parts.append(f"{pipe_sep} \\\\\n{indent} {pred_latex}")
            else:
                parts.append(f"{pipe_sep} {pred_latex}")
            if expression is not None:
                expr_latex = self.generate_expr(expression, parent=node)
                if bullet_break:
                    parts.append(f"{bullet_sep} \\\\\n{indent} {expr_latex}")
                else:
                    parts.append(f"{bullet_sep} {expr_latex}")
        elif expression is not None:
            # Constraint + body: | constraint @ body
            pipe_sep = self._get_mid_separator()
            if pipe_break:
                parts.append(f"{pipe_sep} \\\\\n{indent} {pred_latex}")
            else:
                parts.append(f"{pipe_sep} {pred_latex}")
            expr_latex = self.generate_expr(expression, parent=node)
            if bullet_break:
                parts.append(f"{bullet_sep} \\\\\n{indent} {expr_latex}")
            else:
                parts.append(f"{bullet_sep} {expr_latex}")
        else:
            # No constraint: @ predicate (body is the sole predicate)
            if pipe_break:
                parts.append(f"{bullet_sep} \\\\\n{indent} {pred_latex}")
            else:
                parts.append(f"{bullet_sep} {pred_latex}")

        result = " ".join(parts)

        # Mu always parenthesized in fuzz mode (consistent with single-decl mu)
        if node.quantifier == "mu" and self.use_fuzz:
            return f"({result})"

        # Smart parenthesization for other quantifiers
        if node.quantifier != "mu" and self._quantifier_needs_parens(node, parent):
            return f"({result})"

        return result

    def _generate_schema_binding_latex(self, sb: SchemaBinding) -> str:
        """Return the LaTeX fragment for a schema-text binding (Z RM §3.10).

        Forms emitted (jms ruling 2026-05-21: no thin-space between decoration
        and schema name):
        - decoration="Delta" → ``\\Delta S``
        - decoration="Xi"    → ``\\Xi S``
        - decoration="None"  → ``S``
        - decoration="Prime" → ``S^{\\prime}``  (the name already carries ``'``)

        The prime form uses fuzz's superscript-prime convention.  The raw
        identifier value (e.g., ``"S'"``]) is stripped of its trailing ``'``
        and the ``^{\\prime}`` superscript is appended so fuzz recognises
        the primed schema reference correctly.
        """
        schema_name = sb.schema_name
        if sb.decoration == "Delta":
            return rf"\Delta {schema_name}"
        if sb.decoration == "Xi":
            return rf"\Xi {schema_name}"
        if sb.decoration == "Prime":
            # Strip trailing primes and emit as superscript for fuzz compatibility.
            base = schema_name.rstrip("'")
            primes = len(schema_name) - len(base)
            suffix = r"^{\prime}" * primes
            return f"{base}{suffix}"
        return schema_name  # decoration is None

    @expr_register.register(Quantifier)
    def _generate_quantifier(self, node: Quantifier, parent: Expr | None = None) -> str:
        """Generate LaTeX for quantifier (forall, exists, exists1, mu).

        Supports multiple variables, tuple patterns, expression parts, and
        schema-text quantification (Z RM §3.10).

        Args:
            node: The quantifier node to generate.
            parent: The parent expression context (None if top-level).

        Returns:
            LaTeX string for the quantifier expression.

        Examples:
            forall x : N | pred -> \\forall x \\colon N \\bullet pred
            forall x, y : N | pred -> \\forall x, y \\colon N \\bullet pred
            forall (x, y) : T | pred -> \\forall (x, y) \\colon T \\bullet pred
            mu x : N | pred . expr -> \\mu x \\colon N \\mid pred \\bullet expr
            exists Delta S | P -> \\exists \\Delta S \\spot P
            exists Xi S | P    -> \\exists \\Xi S \\spot P
            exists S | P       -> \\exists S \\spot P
            exists S' | P      -> \\exists S^{\\prime} \\spot P
        """
        # Schema-text quantification path (Z RM §3.10).
        if node.schema_binding is not None:
            return self._generate_schema_quantifier(node, parent)

        # Multi-decl lambda: specialize to emit Spivey-canonical single-token form.
        # Single-decl lambda uses Lambda AST node and routes through _generate_lambda.
        if node.quantifier == "lambda":
            return self._generate_lambda_quantifier(node, parent)

        # Multi-decl chain: route to Spivey-canonical single-quantifier form.
        # A chain exists when the body is a Quantifier with the same operator.
        if (
            isinstance(node.body, Quantifier)
            and node.body.quantifier == node.quantifier
        ):
            return self._generate_logical_quantifier(node, parent)

        quant_latex = self.QUANTIFIERS.get(node.quantifier)
        if quant_latex is None:
            raise ValueError(f"Unknown quantifier: {node.quantifier}")

        # Generate variables (tuple pattern or comma-separated list)
        if node.tuple_pattern:
            # Tuple pattern: forall (x, y) : T | P
            variables_str = self.generate_expr(node.tuple_pattern, parent=node)
        else:
            # Simple variables: forall x, y : T | P
            variables_str = ", ".join(node.variables)
        parts = [quant_latex, variables_str]

        if node.domain:
            domain_latex = self.generate_expr(node.domain, parent=node)
            parts.append(self._get_colon_separator())
            parts.append(domain_latex)

        # Special handling for mu operator in fuzz mode
        # Fuzz requires: (\mu decl | pred) with parentheses around ENTIRE mu expression
        if node.quantifier == "mu" and self.use_fuzz:
            mu_parts = [quant_latex, variables_str]
            if node.domain:
                domain_latex = self.generate_expr(node.domain, parent=node)
                mu_parts.append(f": {domain_latex}")
            # Always use | for predicate separator in mu

            # Increment depth for nested quantifiers
            self._quantifier_depth += 1
            # Get indentation at this depth (for line breaks)
            indent = self._get_indentation()
            body_latex = self.generate_expr(node.body, parent=node)
            self._quantifier_depth -= 1

            # Check for line break after pipe (|)
            if node.line_break_after_pipe:
                # Note: Fuzz mu is parenthesized, doesn't use array format
                # LaTeX source: \\ at end of line, then newline, then \t command
                mu_parts.append(f"| \\\\\n{indent} {body_latex}")
            else:
                mu_parts.append("|")
                mu_parts.append(body_latex)

            # If there's an expression part, add @ separator and expression
            if node.expression:
                mu_parts.append("@")
                expr_latex = self.generate_expr(node.expression, parent=node)
                mu_parts.append(expr_latex)

            # Wrap ENTIRE mu expression in parentheses
            return f"({' '.join(mu_parts)})"

        # Check if quantifier has expression part (bullet separator)
        if node.expression:
            # Use | or \mid for predicate separator
            pipe_sep = self._get_mid_separator()

            # Increment depth for nested quantifiers
            self._quantifier_depth += 1
            # Get indentation at this depth (for line breaks)
            indent = self._get_indentation()
            body_latex = self.generate_expr(node.body, parent=node)
            self._quantifier_depth -= 1

            # Check for line break after pipe (|)
            if node.line_break_after_pipe:
                # LaTeX source: \\ at end of line, then newline, then \t command
                parts.append(f"{pipe_sep} \\\\\n{indent} {body_latex}")
            else:
                parts.append(pipe_sep)
                parts.append(body_latex)

            # Add @ or bullet separator and expression
            bullet_sep = self._get_bullet_separator()
            expr_latex = self.generate_expr(node.expression, parent=node)

            # Check for line break after bullet (.)
            if node.line_break_after_bullet:
                # Get indentation for expression after bullet
                expr_indent = self._get_indentation()
                parts.append(f"{bullet_sep} \\\\\n{expr_indent} {expr_latex}")
            else:
                parts.append(bullet_sep)
                parts.append(expr_latex)
        else:
            # Standard quantifier: @ or bullet separator and body
            separator = self._get_bullet_separator()

            # Increment depth for nested quantifiers
            self._quantifier_depth += 1
            # Get indentation at this depth (for line breaks)
            indent = self._get_indentation()
            body_latex = self.generate_expr(node.body, parent=node)
            self._quantifier_depth -= 1

            # Check for line break after pipe (|)
            if node.line_break_after_pipe:
                # Multi-line quantifier: insert \\ and indent body
                # LaTeX source: \\ at end of line, then newline, then \t command
                # No & prefix: the array column separator is only for the
                # justification column, not for expression-internal continuations.
                parts.append(f"{separator} \\\\\n{indent} {body_latex}")
            else:
                # Single-line quantifier
                parts.append(separator)
                parts.append(body_latex)

        result = " ".join(parts)

        # Smart parenthesization for fuzz mode (non-mu quantifiers only)
        # Mu expressions have special handling above (lines 593-610)
        if node.quantifier != "mu" and self._quantifier_needs_parens(node, parent):
            return f"({result})"

        return result

    def _generate_schema_quantifier(
        self, node: Quantifier, parent: Expr | None = None
    ) -> str:
        r"""Emit LaTeX for a schema-text quantifier (Z RM §3.10).

        The binding is emitted literally; fuzz expands the schema invariant.
        jms ruling (2026-05-21): no thin-space between decoration and name.

        Output form:
            \exists \Delta S \spot P
            \exists \Xi S \spot P
            \exists S \spot P
            \exists S^{\prime} \spot P
            \forall \Delta S \spot P
            \exists_1 \Delta S \spot P
        """
        if node.schema_binding is None:
            raise ValueError("_generate_schema_quantifier: schema_binding is None")

        quant_latex = self.QUANTIFIERS.get(node.quantifier)
        if quant_latex is None:
            raise ValueError(f"Unknown quantifier: {node.quantifier}")

        binding_latex = self._generate_schema_binding_latex(node.schema_binding)
        bullet = self._get_bullet_separator()

        self._quantifier_depth += 1
        indent = self._get_indentation()
        body_latex = self.generate_expr(node.body, parent=node)
        self._quantifier_depth -= 1

        if node.line_break_after_pipe:
            result = (
                f"{quant_latex} {binding_latex} {bullet} \\\\\n{indent} {body_latex}"
            )
        else:
            result = f"{quant_latex} {binding_latex} {bullet} {body_latex}"

        if self._quantifier_needs_parens(node, parent):
            return f"({result})"
        return result

    @expr_register.register(Lambda)
    def _generate_lambda(self, node: Lambda, parent: Expr | None = None) -> str:
        """Generate LaTeX for lambda expression.

        Examples:
        - lambda x : N . x^2 -> (\\lambda x : \\nat @ x^{2}) in fuzz mode
        - lambda x, y : N . x + y -> (\\lambda x, y : \\nat @ x + y) in fuzz mode
        - lambda f : X -> Y . f(x) -> (\\lambda f : X \\fun Y @ f(x)) in fuzz mode

        Note: Uses : (colon) for lambda binding, not \\colon.
        Fuzz requires @ separator and parentheses around lambdas in expressions.
        """
        # Generate variables (comma-separated for multi-variable)
        variables_str = ", ".join(node.variables)
        parts = [r"\lambda", variables_str, ":"]

        # Generate domain (required for lambda)
        domain_latex = self.generate_expr(node.domain)
        parts.append(domain_latex)

        # Add bullet/@ separator
        parts.append(self._get_bullet_separator())
        body_latex = self.generate_expr(node.body)
        parts.append(body_latex)

        result = " ".join(parts)

        # Fuzz requires parentheses around every lambda expression
        if self.use_fuzz:
            result = f"({result})"

        return result

    @expr_register.register(SetComprehension)
    def _generate_set_comprehension(
        self, node: SetComprehension, parent: Expr | None = None
    ) -> str:
        """Generate LaTeX for set comprehension.

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
        # Add ~ spacing hints after { and before }
        parts = [r"\{~", variables_str]

        if node.domain:
            domain_latex = self.generate_expr(node.domain)
            parts.append(self._get_colon_separator())
            parts.append(domain_latex)

        # Emit extra semicolon-separated declarations for multi-typed comprehensions.
        # { s : Ship; c : Class | ... } → ...; c \colon \mathrm{Class} ...
        if node.extra_declarations:
            # Primary variables are in scope for all extra_declaration domains.
            primary_bound = frozenset(node.variables)
            accumulated_bound = primary_bound
            for extra_var, extra_domain in node.extra_declarations:
                domain_free = expr_free_vars(extra_domain)
                if domain_free & accumulated_bound:
                    offending = sorted(domain_free & accumulated_bound)
                    prior = offending[0]
                    msg = (
                        f"set comprehension declaration {extra_var!r} is dependent"
                        f" on prior declaration {prior!r} (Z RM §3.10);"
                        f" fuzz parallel-binds schema-text declarations and will"
                        f" reject this; rewrite using a tuple-typed binding"
                        f" (e.g., {{p : T cross U | p.1 elem dom f}}) or move"
                        f" the dependent condition into the predicate"
                    )
                    raise ValueError(msg)
                accumulated_bound = accumulated_bound | {extra_var}
                extra_domain_latex = self.generate_expr(extra_domain)
                parts.append(";")
                parts.append(extra_var)
                parts.append(self._get_colon_separator())
                parts.append(extra_domain_latex)

        # Handle case with no predicate
        if node.predicate is None:
            # No predicate: { x : X . expr } -> use bullet/@ directly
            if node.expression:
                parts.append(self._get_bullet_separator())
                expression_latex = self.generate_expr(node.expression)
                parts.append(expression_latex)
            # else: {x : T} with no predicate or expression - just the binding
        else:
            # Has predicate: add mid/pipe separator
            parts.append(self._get_mid_separator())

            if node.line_break_after_pipe:
                parts.append(r"\\")

            # Generate predicate, passing this node as parent so that nested
            # quantifiers receive the SetComprehension context and the
            # always-paren rule (ADR §4 context #2) fires correctly.
            predicate_latex = self.generate_expr(node.predicate, parent=node)
            parts.append(predicate_latex)

            # If expression is present, add bullet/@ and expression
            if node.expression:
                parts.append(self._get_bullet_separator())
                if node.line_break_after_bullet:
                    parts.append(r"\\")
                expression_latex = self.generate_expr(node.expression)
                parts.append(expression_latex)

        # Close set
        # Add ~ spacing hint before closing brace
        parts.append(r"~\}")

        result = " ".join(parts)

        # When the comprehension has line breaks, wrap in an array
        # environment for proper multi-line rendering.  The opening
        # brace sits on the first row and the closing brace on the
        # last row (textbook convention).
        if node.line_break_after_pipe or node.line_break_after_bullet:
            inner = result[len(r"\{~ ") :].removesuffix(r"~\}")
            return (
                r"\begin{array}{l}"
                r"\{~ " + inner + r" ~\}"
                r"\end{array}"
            )

        return result

    @expr_register.register(FunctionApp)
    def _generate_function_app(
        self, node: FunctionApp, parent: Expr | None = None
    ) -> str:
        """Generate LaTeX for function application.

        Supports applying any expression, not just identifiers.

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
                arg = node.args[0]
                arg_latex = self.generate_expr(arg)
                # Add parentheses for nested applications
                # Critical for fuzz: P (P Z) → \power (\power Z) not \power \power Z
                # FunctionApp: P (P Z), seq (seq X)
                # BinaryOp: seq (X cross Y), P (A union B)
                # GenericInstantiation: seq (P[X])  # noqa: ERA001
                if isinstance(
                    arg, (FunctionApp, BinaryOp, GenericInstantiation, UnaryOp)
                ):
                    arg_latex = f"({arg_latex})"
                # Add ~ spacing hint between function and argument
                return f"{func_latex}~{arg_latex}"

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
                # Pattern: (special_fn1(special_fn2))(args)  # noqa: ERA001
                # Generate: special_fn1~(special_fn2~args) with parens and tildes
                outer_latex = special_functions[inner_func.name]
                inner_latex = special_functions[node.function.args[0].name]
                args_latex = " ".join(self.generate_expr(arg) for arg in node.args)
                # Add ~ spacing hints
                return f"{outer_latex}~({inner_latex}~{args_latex})"

        # General function application: expr(args)
        func_latex = self.generate_expr(node.function)

        # Add parentheses around function if it's a binary operator
        if isinstance(node.function, BinaryOp):
            func_latex = f"({func_latex})"

        args_latex = ", ".join(self.generate_expr(arg) for arg in node.args)
        return f"{func_latex}({args_latex})"

    @expr_register.register(Range)
    def _generate_range(self, node: Range, parent: Expr | None = None) -> str:
        """Generate LaTeX for range expression (m..n).

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

    @expr_register.register(Conditional)
    def _generate_conditional(
        self, node: Conditional, parent: Expr | None = None
    ) -> str:
        """Generate LaTeX for conditional expression (if/then/else).

        Examples:
        - if x > 0 then x else -x
        - if s = <> then 0 else head s

        Supports line breaks with \\\\ continuation:
        - if x > 0 \\\\
            then x \\\\
            else -x

        Fuzz mode: \\IF condition \\THEN expr1 \\ELSE expr2
        Standard LaTeX: (\\mbox{if } ... \\mbox{ then } ... \\mbox{ else } ...)
        """
        condition_latex = self.generate_expr(node.condition)
        then_latex = self.generate_expr(node.then_expr)
        else_latex = self.generate_expr(node.else_expr)

        # Build line break markers
        break_after_cond = " \\\\\n\\t1 " if node.line_break_after_condition else " "
        break_after_then = " \\\\\n\\t1 " if node.line_break_after_then else " "

        # Fuzz uses \IF \THEN \ELSE keywords
        if self.use_fuzz:
            return (
                f"\\IF {condition_latex}{break_after_cond}"
                f"\\THEN {then_latex}{break_after_then}"
                f"\\ELSE {else_latex}"
            )

        # Standard LaTeX uses mbox keywords
        return (
            f"(\\mbox{{if }} {condition_latex}{break_after_cond}"
            f"\\mbox{{ then }} {then_latex}{break_after_then}"
            f"\\mbox{{ else }} {else_latex})"
        )

    @expr_register.register(GuardedCases)
    def _generate_guarded_cases(
        self, node: GuardedCases, parent: Expr | None = None
    ) -> str:
        """Generate LaTeX for guarded cases expression.

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

    @expr_register.register(GuardedBranch)
    def _generate_guarded_branch(
        self, node: GuardedBranch, parent: Expr | None = None
    ) -> str:
        """Generate LaTeX for single guarded branch.

        This is typically not called directly; GuardedCases handles the rendering.
        """
        expr_latex = self.generate_expr(node.expression)
        guard_latex = self.generate_expr(node.guard)
        return f"{expr_latex} \\mbox{{if }} {guard_latex}"

    @expr_register.register(StringLit)
    def _generate_string_lit(self, node: StringLit, parent: Expr | None = None) -> str:
        r"""Generate LaTeX for a string literal using Z-convention quoting.

        The Z convention is backtick-open, apostrophe-close: `value'

        - Standard LaTeX: \text{`value'} (upright text in math mode)
        - Fuzz mode:      `value'         (fuzz handles the backtick natively)

        LaTeX special characters in the value are escaped to prevent malformed
        output. Both paths use _escape_latex since { } \ # % $ & ~ ^ all have
        special meaning inside LaTeX math and text modes.
        """
        escaped = self._escape_latex(node.value)
        if self.use_fuzz:
            return f"`{escaped}'"
        return rf"\text{{`{escaped}'}}"

    @expr_register.register(SetLiteral)
    def _generate_set_literal(
        self, node: SetLiteral, parent: Expr | None = None
    ) -> str:
        """Generate LaTeX for set literal.

        Examples:
        - {1, 2, 3} -> \\{1, 2, 3\\}
        - {a, b} -> \\{a, b\\}
        - {} -> \\{\\} (empty set)
        """
        if not node.elements:
            # Empty set - render as \{\}
            return r"\{\}"

        # Generate comma-separated elements
        elements_latex = ", ".join(
            self.generate_expr(elem, parent=node) for elem in node.elements
        )
        return f"\\{{{elements_latex}\\}}"

    @expr_register.register(Subscript)
    def _generate_subscript(self, node: Subscript, parent: Expr | None = None) -> str:
        """Generate LaTeX for subscript (a_1, x_i)."""
        base = self.generate_expr(node.base)
        index = self.generate_expr(node.index)

        # Wrap index in braces if it's more than one character
        if len(index) > 1:
            return f"{base}_{{{index}}}"
        return f"{base}_{index}"

    @expr_register.register(Superscript)
    def _generate_superscript(
        self, node: Superscript, parent: Expr | None = None
    ) -> str:
        """Generate LaTeX for superscript using \\bsup...\\esup (fuzz-compatible)."""
        base = self.generate_expr(node.base)
        exponent = self.generate_expr(node.exponent)

        # Use \bsup...\esup for fuzz compatibility
        # Standard ^{n} doesn't work in fuzz mode
        # This syntax works in both fuzz and zed modes

        # If base is itself a superscript, wrap in braces to avoid double superscript
        if isinstance(node.base, Superscript):
            base = f"{{{base}}}"

        return f"{base} \\bsup {exponent} \\esup"

    @expr_register.register(Tuple)
    def _generate_tuple(self, node: Tuple, parent: Expr | None = None) -> str:
        """Generate LaTeX for tuple expression.

        Examples:
        - (1, 2) -> (1, 2)
        - (x, y, z) -> (x, y, z)
        - (a, b+1, f(c)) -> (a, b+1, f(c))

        Tuples are rendered as comma-separated expressions in parentheses.
        """
        elements_latex = ", ".join(self.generate_expr(elem) for elem in node.elements)
        return f"({elements_latex})"

    @expr_register.register(RelationalImage)
    def _generate_relational_image(
        self, node: RelationalImage, parent: Expr | None = None
    ) -> str:
        """Generate LaTeX for relational image.

        The relational image R(| S |) gives the image of set S under relation R.

        Examples:
        - R(| {1, 2} |) -> (R \\limg \\{1, 2\\} \\rimg)
        - parentOf(| {john} |) -> (parentOf \\limg \\{john\\} \\rimg)
        - (R o9 S)(| A |) -> ((R \\semi S) \\limg A \\rimg)

        LaTeX rendering uses \\limg and \\rimg delimiters with spaces.
        Note: fuzz requires the entire expression wrapped in parentheses with
        spaces around \\limg/\\rimg, not function application syntax.
        """
        relation_latex = self.generate_expr(node.relation)
        set_latex = self.generate_expr(node.set)
        return f"({relation_latex} \\limg {set_latex} \\rimg)"

    @expr_register.register(SequenceLiteral)
    def _generate_sequence_literal(
        self, node: SequenceLiteral, parent: Expr | None = None
    ) -> str:
        """Generate LaTeX for sequence literal.

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

    @expr_register.register(TupleProjection)
    def _generate_tuple_projection(
        self, node: TupleProjection, parent: Expr | None = None
    ) -> str:
        """Generate LaTeX for tuple projection.

        Supports both numeric projection and named field projection.

        Examples (numeric):
        - x.1 -> x.1
        - (a, b).2 -> (a, b).2
        - f(x).3 -> f(x).3

        Examples (named fields):
        - e.name -> e.name
        - record.status -> record.status
        - person.age -> person.age

        Note: Fuzz only supports named field projection (identifiers).
        Numeric projections (.1, .2) violate fuzz grammar
        (requires Var-Name, not Number).
        """
        base_latex = self.generate_expr(node.base)

        # Add parentheses if base is a binary operator
        if isinstance(node.base, BinaryOp):
            base_latex = f"({base_latex})"

        # Generate projection suffix (works for both int and str)
        return f"{base_latex}.{node.index}"

    @expr_register.register(BagLiteral)
    def _generate_bag_literal(
        self, node: BagLiteral, parent: Expr | None = None
    ) -> str:
        """Generate LaTeX for bag literal.

        Examples:
        - [[x]] -> \\lbag x \\rbag
        - [[1, 2, 2, 3]] -> \\lbag 1, 2, 2, 3 \\rbag

        Bags are multisets where elements can appear multiple times.
        """
        # Generate comma-separated elements
        elements_latex = ", ".join(self.generate_expr(elem) for elem in node.elements)
        return f"\\lbag {elements_latex} \\rbag"
