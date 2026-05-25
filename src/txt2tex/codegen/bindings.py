"""Codegen handlers for Z binding constructs.

Covers: Theta (``\theta S``) and Binding (the ``{|...|}`` literal).
The multi-typed comprehension that uses bindings ships with the
expressions mixin as part of ``_generate_set_comprehension``.

This mixin is composed into :class:`LaTeXGenerator` via multiple
inheritance.  Methods are byte-identical to their counterparts in the
pre-refactor monolithic ``latex_gen.py``; only their file location has
changed.
"""

from __future__ import annotations

from txt2tex.ast_nodes import Binding, Expr, Theta
from txt2tex.codegen._dispatch import CodegenDispatch, expr_register


class _BindingsCodegen(CodegenDispatch):  # pyright: ignore[reportUnusedClass]
    """Mixin: handlers for Z binding constructs."""

    @expr_register.register(Theta)
    def _generate_theta(self, node: Theta, parent: Expr | None = None) -> str:
        r"""Generate LaTeX for θ-expression (Z RM §3.10).

        Emits ``\theta SchemaRef``.  The \theta macro is a standard LaTeX
        Greek letter — no preamble change needed for either fuzz or zed mode.
        """
        return rf"\theta {self.generate_expr(node.expr, parent=node)}"

    @expr_register.register(Binding)
    def _generate_binding(self, node: Binding, parent: Expr | None = None) -> str:
        r"""Generate LaTeX for a Z binding literal (Z RM §3.7).

        {| name == expr, ... |} → \lblot name == expr, \ldots \rblot

        Component values are emitted with the full expression generator.
        Empty binding ``{| |}`` → ``\lblot \rblot``.
        """
        if not node.pairs:
            return r"\lblot~\rblot"
        components: list[str] = []
        for label, value_expr in node.pairs:
            label_latex = self._emit_attr_name(label)
            value_latex = self.generate_expr(value_expr)
            components.append(f"{label_latex} == {value_latex}")
        inner = ", ".join(components)
        return rf"\lblot~{inner}~\rblot"
