"""Codegen handlers for Z type constructors.

Covers: FunctionType and GenericInstantiation.  These two handlers
emit Z type expressions that appear inside axdef/schema declaration
slots and as the right-hand sides of abbreviations.

This mixin is composed into :class:`LaTeXGenerator` via multiple
inheritance.  Methods are byte-identical to their counterparts in the
pre-refactor monolithic ``latex_gen.py``; only their file location has
changed.
"""

from __future__ import annotations

from txt2tex.ast_nodes import (
    BinaryOp,
    Expr,
    FunctionApp,
    FunctionType,
    GenericInstantiation,
    Identifier,
    UnaryOp,
)
from txt2tex.codegen._dispatch import CodegenDispatch, expr_register


class _TypesCodegen(CodegenDispatch):  # pyright: ignore[reportUnusedClass]
    """Mixin: handlers for Z type constructors."""

    @expr_register.register(FunctionType)
    def _generate_function_type(
        self, node: FunctionType, parent: Expr | None = None
    ) -> str:
        """Generate LaTeX for function type arrows.

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

        # Add parentheses to domain if it's a function type
        # (N1 +-> X) -> seq X should generate as (\nat_1 \pfun X) \fun \seq X
        if isinstance(node.domain, FunctionType):
            domain_latex = f"({domain_latex})"

        # Add parentheses to range if it's also a function type (for clarity)
        # Function types are right-associative: A -> B -> C means A -> (B -> C)
        if isinstance(node.range, FunctionType):
            range_latex = f"({range_latex})"

        return f"{domain_latex} {arrow_latex} {range_latex}"

    @expr_register.register(GenericInstantiation)
    def _generate_generic_instantiation(
        self, node: GenericInstantiation, parent: Expr | None = None
    ) -> str:
        """Generate LaTeX for generic type instantiation.

        Generic types can be instantiated with specific type parameters using
        bracket notation. Special Z notation types use special LaTeX commands.

        Examples:
        - ∅[N] -> \\emptyset[N] or special empty set notation
        - seq[N] -> \\seq N (special handling for single param)
        - P[X] -> \\power X (special handling for single param)
        - Type[A, B] -> Type[A, B]
        - ∅[N cross N] -> \\emptyset[N \\cross N]

        Strategy: Check if base is a special Z notation identifier with single
        type parameter, use LaTeX command notation. Otherwise use bracket notation.
        """
        # Special Z notation types with LaTeX commands
        special_types = {
            "seq": r"\seq",
            "seq1": r"\seq_1",
            "iseq": r"\iseq",
            "bag": r"\bag",
            "P": r"\power",
            "F": r"\finset",
        }

        # Check if base is a simple identifier with special handling
        if isinstance(node.base, Identifier):
            base_name = node.base.name
            if base_name in special_types and len(node.type_params) == 1:
                # Generic instantiation with single param: \seq N (no brackets)
                # Per fuzz manual: prefix generic symbols are operator symbols
                type_latex = special_types[base_name]
                param = node.type_params[0]
                param_latex = self.generate_expr(param)
                # Add parentheses for complex param expressions
                if isinstance(
                    param,
                    (
                        FunctionApp,
                        BinaryOp,
                        GenericInstantiation,
                        UnaryOp,
                        FunctionType,
                    ),
                ):
                    param_latex = f"({param_latex})"
                return f"{type_latex} {param_latex}"

        # Standard generic instantiation: Type[A, B, ...]
        base_latex = self.generate_expr(node.base)
        type_params_latex = ", ".join(
            self.generate_expr(param) for param in node.type_params
        )
        return f"{base_latex}[{type_params_latex}]"
