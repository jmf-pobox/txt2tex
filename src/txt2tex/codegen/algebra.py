"""Codegen handlers for relational-algebra constructs.

Covers: Restrict, Project, RelationRename, NaturalJoin, Divide,
Group, GroupAggregate, Ungroup.  Includes the two private helpers
``_emit_attr_name`` and ``_generate_aggregator_clause`` that are
only called from this family.

This mixin is composed into :class:`LaTeXGenerator` via multiple
inheritance.  Methods are byte-identical to their counterparts in the
pre-refactor monolithic ``latex_gen.py``; only their file location has
changed.
"""

from __future__ import annotations

from txt2tex.ast_nodes import (
    AggregatorClause,
    Divide,
    Expr,
    ExtendAggregate,
    Group,
    GroupAggregate,
    Identifier,
    NaturalJoin,
    Project,
    RelationRename,
    Restrict,
    Ungroup,
)
from txt2tex.codegen._dispatch import CodegenDispatch, expr_register


class _AlgebraCodegen(CodegenDispatch):  # pyright: ignore[reportUnusedClass]
    """Mixin: handlers for relational-algebra constructs."""

    # -------------------------------------------------------------------------
    # Relational algebra expression generators (Phase 2.2)
    # -------------------------------------------------------------------------

    def _emit_attr_name(self, name: str) -> str:
        r"""Emit an attribute name for use inside pi[...] or R[new/old] brackets.

        Attribute names are field names — they render italic by default.
        Operator-keyword mappings (dom → \dom, id → \id) do NOT apply here:
        in the pi or rename bracket context every name is unambiguously a field name.
        """
        return name

    @expr_register.register(Restrict)
    def _generate_restrict(self, node: Restrict, parent: Expr | None = None) -> str:
        r"""Generate LaTeX for sigma[predicate](relation).

        sigma[bore >= 16](Class) → \mathrm{Restrict}_{bore \geq 16}(Class)
        """
        pred_latex = self.generate_expr(node.predicate, parent=node)
        rel_latex = self.generate_expr(node.relation, parent=node)
        return rf"\mathrm{{Restrict}}_{{{pred_latex}}}({rel_latex})"

    @expr_register.register(Project)
    def _generate_project(self, node: Project, parent: Expr | None = None) -> str:
        r"""Generate LaTeX for pi[A, B](relation).

        pi[class, country](Class) → \mathrm{Project}_{class, country}(Class)
        Attribute names are emitted via _emit_attr_name (identity pass-through);
        keyword-to-LaTeX conversions do not apply inside the attribute list.
        Subscript form matches the instructor's canonical notation (slides/topic02.pdf).
        """
        attrs_str = ", ".join(self._emit_attr_name(a) for a in node.attrs)
        rel_latex = self.generate_expr(node.relation, parent=node)
        return rf"\mathrm{{Project}}_{{{attrs_str}}}({rel_latex})"

    @expr_register.register(RelationRename)
    def _generate_relation_rename(
        self, node: RelationRename, parent: Expr | None = None
    ) -> str:
        """Generate LaTeX for relation renaming (Z RM §3.11).

        Emits ``R[new/old, ...]`` as a literal pass-through — no ``\\mathrm``.
        Per Z RM §3.11 the new name appears first, the old name second.
        Pair direction in the AST: ``(new_name, old_name)``.

        When the relation operand is a compound expression (not a bare
        identifier), it is wrapped in parentheses for readability.

        Examples:
        - R[b/a]                      → R[b/a]
        - R[b/a, d/c]                 → R[b/a, d/c]
        - (pi[x](R))[b/a]             → (pi[x](R))[b/a]  (compound base)
        """
        rel_latex = self.generate_expr(node.relation, parent=node)
        # Wrap compound (non-identifier) bases in parens for clarity
        if not isinstance(node.relation, Identifier):
            rel_latex = f"({rel_latex})"
        pairs_str = ", ".join(
            f"{new_name}/{old_name}" for new_name, old_name in node.pairs
        )
        return f"{rel_latex}[{pairs_str}]"

    @expr_register.register(NaturalJoin)
    def _generate_natural_join(
        self, node: NaturalJoin, parent: Expr | None = None
    ) -> str:
        r"""Generate LaTeX for R join S or R join [p] S.

        R join S      → \mathrm{Join}(R, S)               (natural join)
        R join [p] S  → \mathrm{Join}_{p}(R, S)           (theta-join)

        When line_break_after is set, inserts \\ before the RHS so the
        right operand starts on the next indented line.
        """
        left_latex = self.generate_expr(node.left, parent=node)
        right_latex = self.generate_expr(node.right, parent=node)
        if node.subscript is None:
            if node.line_break_after:
                indent = self._get_indentation()
                return f"\\mathrm{{Join}}({left_latex}, \\\\\n{indent} {right_latex})"
            return f"\\mathrm{{Join}}({left_latex}, {right_latex})"
        sub_latex = self.generate_expr(node.subscript)
        if node.line_break_after:
            indent = self._get_indentation()
            # Break inside the function-call parens before the right argument
            join_op = f"\\mathrm{{Join}}_{{{sub_latex}}}"
            return f"{join_op}({left_latex}, \\\\\n{indent} {right_latex})"
        return f"\\mathrm{{Join}}_{{{sub_latex}}}({left_latex}, {right_latex})"

    @expr_register.register(Divide)
    def _generate_divide(self, node: Divide, parent: Expr | None = None) -> str:
        r"""Generate LaTeX for R div S.

        R div S → R~\div~S

        Surround the `\div` (which fuzz.sty renders as a sans-serif "div"
        word, not the ÷ symbol) with explicit ~ non-breaking spaces so
        the operator does not visually crowd identifiers in dense
        contexts such as binding bodies and inline math.

        When line_break_after is set, inserts \\ before the RHS.
        """
        left_latex = self.generate_expr(node.left, parent=node)
        right_latex = self.generate_expr(node.right, parent=node)
        if node.line_break_after:
            indent = self._get_indentation()
            return f"{left_latex}~\\div~\\\\\n{indent} {right_latex}"
        return f"{left_latex}~\\div~{right_latex}"

    @expr_register.register(Group)
    def _generate_group(self, node: Group, parent: Expr | None = None) -> str:
        r"""Generate LaTeX for R group ({A, B, ...} as alias).

        R group ({A} as m) →
            R \mathop{\mathrm{GROUP}} (\{A\} \mathop{\mathrm{AS}} m)

        When line_break_after is set, inserts \\ after the GROUP expression
        so the next operator in a chain starts on the following line.
        """
        relation_latex = self.generate_expr(node.relation)
        attrs_str = ", ".join(self._emit_attr_name(a) for a in node.attrs)
        alias_str = self._emit_attr_name(node.alias)
        result = (
            rf"{relation_latex} \mathop{{\mathrm{{GROUP}}}}"
            rf" (\{{{attrs_str}\}} \mathop{{\mathrm{{AS}}}} {alias_str})"
        )
        if node.line_break_after:
            indent = self._get_indentation()
            return f"{result} \\\\\n{indent} "
        return result

    @expr_register.register(GroupAggregate)
    def _generate_group_aggregate(
        self, node: GroupAggregate, parent: Expr | None = None
    ) -> str:
        r"""Generate LaTeX for R Group (Count(x) as t, Sum(y) as g).

        Each AggregatorClause renders as:
            \mathrm{Count}(x)~\mathrm{as}~t

        The full expression renders as:
            R \mathop{\mathrm{Group}}(\mathrm{Count}(x)~\mathrm{as}~t,
                                      \mathrm{Sum}(y)~\mathrm{as}~g)

        The `\mathop` wrapper gives `Group` proper binary-operator spacing
        in math mode so the left operand (`R`) does not collide with the
        operator symbol.  Consistent with `_generate_group` (regroup) and
        `_generate_ungroup` which use `\mathop` for the same reason.

        When line_break_after is set, inserts \\ after the GROUP expression.
        """
        relation_latex = self.generate_expr(node.relation)
        clause_parts = ", ".join(
            self._generate_aggregator_clause(c) for c in node.clauses
        )
        result = rf"{relation_latex} \mathop{{\mathrm{{Group}}}}({clause_parts})"
        if node.line_break_after:
            indent = self._get_indentation()
            return f"{result} \\\\\n{indent} "
        return result

    def _generate_aggregator_clause(self, clause: AggregatorClause) -> str:
        r"""Render a single AggregatorClause as LaTeX.

        Single-arg: Count(attr) as alias  →  \mathrm{Count}(attr)~\mathrm{as}~alias
        Two-arg:    Sum(rel, attr) as alias → \mathrm{Sum}(rel, attr)~\mathrm{as}~alias
        """
        label = clause.agg.label()
        attr = self._emit_attr_name(clause.attr)
        alias = self._emit_attr_name(clause.alias)
        if clause.source_rel is not None:
            rel = self._emit_attr_name(clause.source_rel)
            args = f"{rel}, {attr}"
        else:
            args = attr
        return rf"\mathrm{{{label}}}({args})~\mathrm{{as}}~{alias}"

    @expr_register.register(ExtendAggregate)
    def _generate_extend_aggregate(
        self, node: ExtendAggregate, parent: Expr | None = None
    ) -> str:
        r"""Generate LaTeX for R extend (Sum(payments, amountPaid) as total).

        Each AggregatorClause renders as:
            \mathrm{Sum}(payments, amountPaid)~\mathrm{as}~total

        The full expression renders as:
            R \mathop{\mathrm{Extend}}(
                \mathrm{Sum}(payments, amountPaid)~\mathrm{as}~total)

        The ``\mathop`` wrapper gives ``Extend`` proper binary-operator spacing
        in math mode so the left operand does not collide with the operator symbol.
        Consistent with ``_generate_group_aggregate`` which uses ``\mathop`` for
        the same reason.

        When line_break_after is set, inserts \\ after the EXTEND expression.
        """
        relation_latex = self.generate_expr(node.relation)
        clause_parts = ", ".join(
            self._generate_aggregator_clause(c) for c in node.clauses
        )
        result = rf"{relation_latex} \mathop{{\mathrm{{Extend}}}}({clause_parts})"
        if node.line_break_after:
            indent = self._get_indentation()
            return f"{result} \\\\\n{indent} "
        return result

    @expr_register.register(Ungroup)
    def _generate_ungroup(self, node: Ungroup, parent: Expr | None = None) -> str:
        r"""Generate LaTeX for R ungroup alias.

        R ungroup members → R \mathop{\mathrm{UNGROUP}} members

        When line_break_after is set, inserts \\ after the UNGROUP expression
        so the next operator in a chain starts on the following line.
        """
        relation_latex = self.generate_expr(node.relation)
        alias_str = self._emit_attr_name(node.alias)
        result = f"{relation_latex} \\mathop{{\\mathrm{{UNGROUP}}}} {alias_str}"
        if node.line_break_after:
            indent = self._get_indentation()
            return f"{result} \\\\\n{indent} "
        return result
