"""Dispatch base for LaTeXGenerator — defines the two singledispatch entry points.

The two module-level names ``expr_register`` and ``item_register`` expose the
``singledispatchmethod`` descriptors in a form that both mypy and pyright
understand.  Mixin files import these names and apply them as decorators:

    @expr_register.register(SomeNode)
    def _generate_some_node(self, node: SomeNode, parent: Expr | None = None) -> str:
        ...

The final ``LaTeXGenerator`` class inherits from ``CodegenDispatch`` plus all
the mixin classes so every registered handler is reachable through the MRO.
"""

from __future__ import annotations

from collections.abc import Callable
from functools import singledispatchmethod
from typing import TYPE_CHECKING, TypeVar, cast

from txt2tex.ast_nodes import DocumentItem, Expr

if TYPE_CHECKING:
    from txt2tex.ast_nodes import Identifier, SchemaInclusion

F = TypeVar("F", bound=Callable[..., object])


class RegisterHelper:
    """Typed stand-in for the singledispatchmethod descriptor.

    This class is never instantiated.  It exists only so that mypy and pyright
    understand that ``_expr_register.register(SomeType)`` is a typed decorator
    that preserves the decorated function's type.
    """

    def register(self, typ: type) -> Callable[[F], F]:  # type: ignore[empty-body]
        ...


class CodegenDispatch:
    """Base class carrying the two singledispatch entry points.

    All concrete handlers are registered against these two methods from the
    mixin classes in this package.  ``LaTeXGenerator`` inherits from both the
    mixin classes and ``_CodegenDispatch`` so every registered handler is
    reachable through the normal MRO.

    The ``TYPE_CHECKING`` block below declares cross-cutting state attributes
    and helper methods that live on ``LaTeXGenerator`` (or in mixins not yet
    extracted).  These declarations let mypy/pyright resolve ``self.X``
    references from mixin method bodies without any runtime effect — the
    actual implementations remain on ``LaTeXGenerator`` and are reached
    through the normal MRO.  As subsequent moves consolidate these helpers
    into their own mixin files, the declarations migrate out of here.
    """

    if TYPE_CHECKING:
        _in_z_paragraph: bool
        _in_inline_part: bool
        use_fuzz: bool

        def _has_line_breaks(self, expr: Expr) -> bool: ...
        def _generate_identifier(
            self, node: Identifier, parent: Expr | None = None
        ) -> str: ...
        def _check_overflow(
            self,
            latex: str,
            source_line: int,
            context: str,
            content_preview: str | None = None,
        ) -> None: ...
        def _expression_contains_dat_construct(self, expr: object) -> bool: ...
        def _emit_schema_inclusion(self, incl: SchemaInclusion) -> str: ...

    @singledispatchmethod
    def generate_document_item(self, item: DocumentItem) -> list[str]:
        """Generate LaTeX lines for a document item.

        Uses singledispatch to select the appropriate generator based on
        the item type. This fallback handles bare Expr nodes that appear
        as document items.

        Args:
            item: The document item node to generate. Can be Section,
                Solution, TruthTable, EquivChain, Schema, AxDef, or Expr.

        Returns:
            List of LaTeX lines (without newline characters).
        """
        # Fallback only reached for Expr types (all document types are registered)
        expr = cast("Expr", item)
        latex_expr = self.generate_expr(expr)

        if self._has_line_breaks(expr):
            # Multi-line expression: use display math with array
            # Respect inline part context for proper positioning
            lines: list[str] = []

            if self._in_inline_part:
                # Inside part with leftskip: position naturally with leftskip
                lines.append(r"\savedleftskip=\leftskip")
                lines.append(r"\noindent")
            else:
                # Normal context: just prevent paragraph indentation
                lines.append(r"\noindent")

            lines.append(r"$\displaystyle")
            lines.append(r"\begin{array}{l}")  # Left-aligned single column
            lines.append(latex_expr)
            lines.append(r"\end{array}$")
            lines.append("")
            # Add trailing spacing for separation from following content
            lines.append(r"\bigskip")
            lines.append("")
            return lines
        # Single-line expression: use inline math (original behavior)
        return [r"\noindent", f"${latex_expr}$", "", ""]

    @singledispatchmethod
    def generate_expr(self, expr: Expr, parent: Expr | None = None) -> str:
        """Generate LaTeX for expression (without wrapping in math mode).

        Uses singledispatch to select the appropriate generator based on
        the expression type. Each registered handler generates LaTeX for
        its specific node type, with precedence-aware parenthesization.

        Args:
            expr: The expression AST node to generate LaTeX for.
            parent: The parent expression context for precedence handling
                (None if top-level).

        Returns:
            LaTeX math-mode source code (caller wraps in $...$ or environments).

        Raises:
            TypeError: If expression type has no registered handler.
        """
        raise TypeError(f"Unknown expression type: {type(expr).__name__}")


# Expose the singledispatchmethod descriptors with a typed interface so that
# mypy and pyright understand @_expr_register.register(SomeNode) as a typed
# decorator.  The __dict__ access bypasses __get__ and returns the raw
# singledispatchmethod object, which mypy sees as Any; assigning it to a
# _RegisterHelper annotation makes the .register call fully typed.
expr_register: RegisterHelper = CodegenDispatch.__dict__["generate_expr"]
item_register: RegisterHelper = CodegenDispatch.__dict__["generate_document_item"]
