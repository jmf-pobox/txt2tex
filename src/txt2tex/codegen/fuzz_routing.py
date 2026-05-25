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
    Group,
    GroupAggregate,
    NaturalJoin,
    Project,
    RelationRename,
    Restrict,
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
