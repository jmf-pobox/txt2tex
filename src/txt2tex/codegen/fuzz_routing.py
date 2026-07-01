"""Fuzz-vs-inline-math routing helpers.

Some AST nodes — algebra, bindings, GROUP/UNGROUP — cannot sit inside
a Z environment because fuzz rejects their syntax.  Abbreviation
emission inspects the right-hand side and switches between an in-Z
form (``\begin{zed}...\\end{zed}``) and a noindent inline-math form
(``\noindent$...$``) accordingly.  This mixin carries the inspector
and the type tuple it uses.

State is module-state by convention; method bodies are byte-identical
to their counterparts in the pre-refactor monolithic ``latex_gen.py``.
"""

from __future__ import annotations

from typing import ClassVar, cast

from txt2tex.ast_nodes import (
    Binding,
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
    SetComprehension,
    Tuple,
    Ungroup,
)
from txt2tex.codegen._dispatch import CodegenDispatch


class _FuzzRoutingCodegen(CodegenDispatch):  # pyright: ignore[reportUnusedClass]
    """Mixin: helpers for routing emission between Z and inline math."""

    _DAT_EXPRESSION_TYPES: ClassVar[tuple[type, ...]] = (
        Restrict,
        Project,
        RelationRename,
        NaturalJoin,
        Divide,
        Binding,
        Group,
        GroupAggregate,
        ExtendAggregate,
        Ungroup,
    )

    def _expression_contains_dat_construct(self, expr: object) -> bool:
        """True if expr's AST tree contains any relational construct.

        Relational constructs (algebra, bindings, GROUP/UNGROUP) cannot sit
        inside a Z environment without fuzz rejecting their syntax.
        This recursive walk lets abbreviation emission switch between an
        in-zed form (pure Z RHS) and a noindent-math form (relational RHS).
        """
        if isinstance(expr, self._DAT_EXPRESSION_TYPES):
            return True
        fields = getattr(expr, "__dataclass_fields__", None)
        if fields is None:
            return False
        for field_name in fields:
            value: object = getattr(expr, field_name)
            if isinstance(value, list):
                items = cast("list[object]", value)
                if any(self._expression_contains_dat_construct(v) for v in items):
                    return True
            elif self._expression_contains_dat_construct(value):
                return True
        return False

    def _binding_to_tuple_expr(self, binding: Binding) -> Expr:
        """Convert a binding to the equivalent tuple expression for fuzz.

        Single-field: bare expression. Multi-field: tuple.
        """
        if len(binding.pairs) <= 1:
            if not binding.pairs:
                # Empty binding — return an empty-set placeholder
                return Identifier(
                    name="\\emptyset", line=binding.line, column=binding.column
                )
            return binding.pairs[0][1]
        return Tuple(
            elements=[v for _, v in binding.pairs],
            line=binding.line,
            column=binding.column,
        )

    def _replace_binding_with_tuple(self, node: SetComprehension) -> SetComprehension:
        """Return a fuzz-safe copy of the set comprehension.

        If the characteristic expression is a Binding, replace with
        the equivalent tuple so fuzz can validate the types.
        """
        if not isinstance(node.expression, Binding):
            return node
        return SetComprehension(
            variables=node.variables,
            domain=node.domain,
            predicate=node.predicate,
            expression=self._binding_to_tuple_expr(node.expression),
            extra_declarations=node.extra_declarations,
            line_break_after_pipe=node.line_break_after_pipe,
            line_break_after_bullet=node.line_break_after_bullet,
            line=node.line,
            column=node.column,
        )

    def _emit_hidden_abbreviation(self, name_latex: str, expr: Expr) -> list[str]:
        r"""Emit a hidden fuzz-validation abbreviation inside \\setbox0=\\vbox{%...}.

        The box is discarded at typeset time but fuzz reads and validates it.
        Sets ``_in_hidden_fuzz_block`` so nested generators suppress
        \begin{array} wrapping that fuzz would reject.
        """
        prev_z = self._in_z_paragraph
        prev_hidden = self._in_hidden_fuzz_block
        self._in_z_paragraph = True
        self._in_hidden_fuzz_block = True
        try:
            expr_latex = self.generate_expr(expr)
        finally:
            self._in_z_paragraph = prev_z
            self._in_hidden_fuzz_block = prev_hidden
        return [
            r"\setbox0=\vbox{%",
            r"\begin{zed}",
            f"{name_latex} == {expr_latex}",
            r"\end{zed}%",
            "}",
        ]
