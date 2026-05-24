"""Operator precedence and parenthesisation policy.

Holds the operator tables (``BINARY_OPS``, ``PRECEDENCE``,
``UNARY_PRECEDENCE``, ``RIGHT_ASSOCIATIVE``), the binary-operator
text mapper (``_map_binary_operator``), and the two parens-needed
predicates (``_needs_parens``, ``_quantifier_needs_parens``) plus
the small helper ``_body_has_connective``.

This mixin is foundational for Phase 2's paren-policy work: every
emit-site that decides whether to wrap an expression in parens
consults methods that live here.  Method bodies and class-var values
are byte-identical to their counterparts in the pre-refactor
monolithic ``latex_gen.py``.
"""

from __future__ import annotations

from typing import ClassVar

from txt2tex.ast_nodes import (
    BinaryOp,
    Expr,
    FunctionType,
    Lambda,
    Quantifier,
    SetComprehension,
)
from txt2tex.codegen._dispatch import CodegenDispatch


class _ParenPolicyCodegen(CodegenDispatch):  # pyright: ignore[reportUnusedClass]
    """Mixin: paren policy + operator tables."""

    # Operator mappings
    BINARY_OPS: ClassVar[dict[str, str]] = {
        # Propositional logic - Only LaTeX-style keywords
        "land": r"\land",
        "lor": r"\lor",
        "=>": r"\Rightarrow",
        "implies": r"\Rightarrow",  # Internal operator for filter semantics
        "<=>": r"\Leftrightarrow",
        # Comparison operators
        "<": r"<",
        ">": r">",
        "<=": r"\leq",
        ">=": r"\geq",
        "=": r"=",
        "!=": r"\neq",
        "/=": r"\neq",  # Z notation slash negation
        # Sequent judgment
        "shows": r"\shows",  # Turnstile (⊢)
        # Set operators
        "elem": r"\in",  # Set membership
        "notin": r"\notin",
        "/in": r"\notin",  # Z notation slash negation
        "subset": r"\subseteq",
        "subseteq": r"\subseteq",  # Alternative notation for subset
        "psubset": r"\subset",  # Strict/proper subset
        "union": r"\cup",
        "intersect": r"\cap",
        "cross": r"\cross",  # Cartesian product
        "×": r"\cross",  # Cartesian product (Unicode)  # noqa: RUF001
        "\\": r"\setminus",  # Set difference
        "++": r"\oplus",  # Override
        # Relation operators
        "<->": r"\rel",  # Relation type
        "|->": r"\mapsto",  # Maplet constructor
        "<|": r"\dres",  # Domain restriction
        "|>": r"\rres",  # Range restriction
        "comp": r"\comp",  # Relational composition
        ";": r"\semi",  # Relational composition (semicolon)
        # Extended relation operators
        "<<|": r"\ndres",  # Domain subtraction (anti-restriction)
        "|>>": r"\nrres",  # Range subtraction (anti-restriction)
        "o9": r"\semi",  # Forward composition (fuzz \semi)
        # Function type operators
        "->": r"\fun",  # Total function
        "+->": r"\pfun",  # Partial function
        ">->": r"\inj",  # Total injection
        ">+>": r"\pinj",  # Partial injection
        "-|>": r"\pinj",  # Partial injection (alternative notation)
        "-->>": r"\surj",  # Total surjection
        "+->>": r"\psurj",  # Partial surjection
        ">->>": r"\bij",  # Bijection
        "77->": r"\ffun",  # Finite partial function
        # Arithmetic operators
        "+": r"+",  # Addition (also postfix in relational context)
        "-": r"-",  # Subtraction
        "*": r"*",  # Multiplication (also postfix in relational context)
        "mod": r"\mod",  # Modulo (use \mod not \bmod for fuzz compatibility)
        # Sequence operators
        "⌢": r"\cat",  # Sequence concatenation (Unicode)
        "^": r"\cat",  # Sequence concatenation (ASCII alternative)
        "↾": r"\filter",  # Sequence filter (Unicode)
        "filter": r"\filter",  # Sequence filter (ASCII alternative)
        # Bag operators
        "⊎": r"\uplus",  # Bag union (Unicode)
        "bag_union": r"\uplus",  # Bag union (ASCII alternative)
        "bag_diff": r"\uminus",  # Bag difference (Z RM §4.6.2)
    }

    # Operator precedence (lower number = lower precedence)
    # Only LaTeX-style keywords supported: land, lor
    # Z RM §8.3 defines precedence for logical/set operators; arithmetic
    # operators are treated as generic infix in Z RM, so standard mathematical
    # convention applies: multiply/divide bind tighter than add/subtract.
    PRECEDENCE: ClassVar[dict[str, int]] = {
        "<=>": 1,  # Lowest precedence
        "=>": 2,
        "implies": 2,  # Internal operator for filter semantics
        "lor": 3,
        "land": 4,
        # Comparison operators
        "<": 5,
        ">": 5,
        "<=": 5,
        ">=": 5,
        "=": 5,
        "!=": 5,
        "/=": 5,  # Z slash-negation alias of !=
        # Relation operators - between comparison and set ops
        "<->": 6,
        "|->": 6,
        "<|": 6,
        "|>": 6,
        "<<|": 6,  # Domain subtraction
        "|>>": 6,  # Range subtraction
        "o9": 6,  # Composition
        "comp": 6,
        ";": 6,
        # Function type operators - same precedence as relations
        "->": 6,
        "+->": 6,
        ">->": 6,
        ">+>": 6,
        "-->>": 6,
        "+->>": 6,
        ">->>": 6,
        "77->": 6,  # Finite partial function
        # Set operators
        "elem": 7,  # Set membership (replaces "in" after migration)
        "notin": 7,
        "/in": 7,  # Z slash-negation alias of notin
        "subset": 7,
        "subseteq": 7,  # Alternative notation for subset
        "psubset": 7,  # Strict/proper subset
        "union": 8,
        "++": 8,  # Function/relation override — same level as union per parser
        # cross/join/div are strictly tighter than union; loosen union to
        # 8 and bump the cross family so _needs_parens emits the right
        # parens around mixed-level children.
        "cross": 9,  # Cartesian product (parser: _parse_cross, tighter than union)
        "×": 9,  # Cartesian product (Unicode)  # noqa: RUF001
        "intersect": 10,
        "\\": 10,  # Set difference - same level as intersect (parser: _parse_intersect)
        # Arithmetic operators (Gap #1 — Z RM §8.3 treats these as generic
        # infix; standard mathematical convention: * binds tighter than + and
        # -.  Levels 11 and 12 sit above all set operators (max 10) so that
        # mixed expressions like `a + b` inside a set-membership test do not
        # spuriously parenthesise `b`.)
        "+": 11,  # Binary addition
        "-": 11,  # Binary subtraction
        "*": 12,  # Multiplication
        "mod": 12,  # Modulo — same binding strength as *
    }
    # Documentary only.  Z RM treats `=>` as right-associative and `<=>` as
    # logically commutative.  The parser builds left-folded trees for both
    # (parser.py:_parse_iff / _parse_implies are `while` loops), and the
    # paren behaviour for these operators is hard-coded in _needs_parens
    # rather than driven by this set.  Kept for documentation; not consulted
    # at runtime.
    RIGHT_ASSOCIATIVE: ClassVar[set[str]] = {"=>", "<=>"}
    # Unary operator precedence (Gap #2).  All unary operators bind more
    # tightly than any binary operator (highest level in our table is 11 for
    # * and /; unary level is 20 so any PRECEDENCE.get(op, 999) comparison
    # will correctly find unary > binary).  The dict makes the policy
    # machine-readable and queryable from tests.
    UNARY_PRECEDENCE: ClassVar[dict[str, int]] = {
        "lnot": 20,
        "-": 20,  # Unary negation
        "#": 20,  # Cardinality (Z RM §4.2)
        "dom": 20,
        "ran": 20,
        "inv": 20,
        "id": 20,
        "P": 20,
        "P1": 20,
        "F": 20,
        "F1": 20,
        "bigcup": 20,
        "bigcap": 20,
        # Postfix operators — precedence not relevant for paren decisions
        # (postfix is rendered as superscript and never needs extra parens)
        "~": 20,
        "+": 20,  # Transitive closure (postfix context only)
        "*": 20,  # Reflexive-transitive closure (postfix context only)
    }

    def _map_binary_operator(self, operator: str, base_latex: str) -> str:
        """Map binary operator to appropriate LaTeX for fuzz/standard mode.

        Fuzz-specific mappings:
        - => / implies → \\implies (instead of \\Rightarrow)
        - <=> → \\iff (outside EQUIV blocks) or \\Leftrightarrow (in EQUIV)
        """
        if not self.use_fuzz:
            return base_latex
        if operator in ("=>", "implies"):
            return r"\implies"
        # In ARGUE/EQUIV/EQUAL blocks, use \Leftrightarrow; otherwise use \iff
        if operator == "<=>" and not self._in_argue_block:
            return r"\iff"
        return base_latex

    def _needs_parens(
        self, child: Expr, parent: BinaryOp, *, is_left_child: bool
    ) -> bool:
        """Check if child expression needs parentheses in parent context.

        Args:
            child: The child expression to check
            parent: The parent BinaryOp node
            is_left_child: True if this is the left child, False if right

        Returns:
            True if parentheses are needed
        """
        parent_op = parent.operator
        # Quantifiers and lambdas have lowest precedence (bind most loosely)
        # Per Woodcock: "quantifiers bind very loosely, scope extends to next bracket"
        # Need parens when used as operands of binary operators
        # In fuzz mode, _quantifier_needs_parens handles this separately
        # In non-fuzz mode, we handle it here
        if isinstance(child, (Quantifier, Lambda)) and not self.use_fuzz:
            return True

        # FunctionType needs parentheses when used as operand in cross/other ops
        # E.g., (X -> Y) cross Z, not X -> Y cross Z which would be X -> (Y cross Z)
        if isinstance(child, FunctionType):
            return True

        # Only binary ops need precedence checking
        if not isinstance(child, BinaryOp):
            return False

        # If child has explicit parentheses from source, don't add
        # precedence-based parentheses. The child will add its own parens
        # when generated. Prevents double parenthesization ((A \land B))
        if child.explicit_parens:
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

            # Note: Cross product does NOT automatically get nested parens.
            # Fuzz distinguishes between:
            # - A x B x C (flat 3-tuple, no parens)
            # - (A x B) x C (nested pairs, with parens)
            # Only add parens where user explicitly wrote them in source.
            # Removed automatic parenthesization that was breaking fuzz 3-tuples.

            # For left-associative operators, right child needs parens
            # E.g., R o9 (S o9 T) requires parens on right
            # but (R o9 S) o9 T doesn't need parens on left
            # All operators except => and <=> are left-associative
            if not is_left_child:
                return True

        return False

    # Propositional connectives whose presence in a quantifier body triggers
    # the "always-paren" rule (ADR §4 context #1).  Z RM §2.1-2.3.
    _CONNECTIVE_OPS: ClassVar[frozenset[str]] = frozenset(
        {
            "land",
            "lor",
            "=>",
            "<=>",
        }
    )

    def _body_has_connective(self, expr: Expr) -> bool:
        """Return True if expr is a BinaryOp whose operator is a connective."""
        return isinstance(expr, BinaryOp) and expr.operator in self._CONNECTIVE_OPS

    def _quantifier_needs_parens(self, node: Quantifier, parent: Expr | None) -> bool:
        """Check if quantifier needs parentheses given its parent context.

        Two always-paren rules apply regardless of mode (ADR §4):

        1. *Body-has-connectives* (Z RM §2.1, §2.3, §3.9): when the
           effective body of the quantifier (the expression after the
           bullet if present, otherwise the predicate) is a propositional
           connective expression, wrap the whole quantifier for visual
           chunking.

        2. *Set-comprehension predicate* (Z RM §3.8.1): a quantifier
           appearing as the constraint of a set comprehension
           ``{ x : T | exists … }`` must be wrapped.  The parent is a
           SetComprehension node, which reaches here once the set
           comprehension generator passes ``parent=node`` (Gap #3).

        In fuzz mode, the grammar is stricter: any parent that is not a
        Quantifier or Lambda also triggers parens (fuzz requires explicit
        grouping for nested quantified predicates).

        Args:
            node: The quantifier node.
            parent: The parent expression (None if top-level).

        Returns:
            True if parentheses should be emitted around *node*.
        """
        # Top-level: never needs parens
        if parent is None:
            return False

        # Quantifier or Lambda parent: the inner quantifier is the body or
        # expression part, always delimited by a structural bullet/@ separator.
        # No parens needed from this function (the bullet is the separator).
        # This exemption also prevents context #1 below from spuriously
        # wrapping e.g. "forall x | forall y | P land Q".
        if isinstance(parent, (Quantifier, Lambda)):
            return False

        # Always-paren context #2: quantifier inside a set-comprehension
        # predicate.  Applies in both modes.  The parent=node argument now
        # passed by _generate_set_comprehension makes this context visible.
        if isinstance(parent, SetComprehension):
            return True

        # Always-paren context #1: effective body contains a connective.
        # Only checked when parent is NOT a Quantifier/Lambda (handled above)
        # and NOT a SetComprehension (handled above).  This fires when the
        # quantifier appears in another compound context (BinaryOp, Tuple,
        # FunctionApp arg, etc.) and its body has a propositional connective.
        # Z RM §2.1, §2.3, §3.9.
        body_expr = node.expression if node.expression is not None else node.body
        if self._body_has_connective(body_expr):
            return True

        # In non-fuzz mode the remaining cases (quantifier inside BinaryOp)
        # are handled by _needs_parens.  In fuzz mode, any remaining parent
        # (BinaryOp, Tuple, FunctionApp, …) requires parens because fuzz's
        # grammar is stricter than standard LaTeX.
        return self.use_fuzz
