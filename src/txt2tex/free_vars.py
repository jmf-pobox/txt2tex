"""Compute free variables of a txt2tex AST expression."""

from __future__ import annotations

from collections.abc import Iterable

from txt2tex.ast_nodes import (
    BagLiteral,
    BinaryOp,
    Conditional,
    Divide,
    Expr,
    FunctionApp,
    FunctionType,
    GenericInstantiation,
    Group,
    GroupAggregate,
    GuardedBranch,
    GuardedCases,
    Identifier,
    Lambda,
    NaturalJoin,
    Number,
    Project,
    Quantifier,
    Range,
    RelationalImage,
    RelationRename,
    Restrict,
    SchemaCompose,
    SchemaHide,
    SchemaPipe,
    SchemaProject,
    SchemaRename,
    SchemaText,
    SequenceLiteral,
    SetComprehension,
    SetLiteral,
    StringLit,
    Subscript,
    Superscript,
    Theta,
    Tuple,
    TupleProjection,
    UnaryOp,
    Ungroup,
)

_EMPTY: frozenset[str] = frozenset()


def _union(exprs: Iterable[Expr]) -> frozenset[str]:
    """Return the union of free variables across a sequence of expressions.

    Accepts any ``Iterable[Expr]`` (covariant read) so callers can pass a
    ``list[GuardedBranch]`` or ``list[Identifier]`` without an ``arg-type``
    cast — both are ``Expr`` subtypes, but ``list[T]`` is invariant in T.
    """
    result: frozenset[str] = _EMPTY
    for e in exprs:
        result = result | expr_free_vars(e)
    return result


def _free_vars_binder(expr: Quantifier | Lambda | SetComprehension) -> frozenset[str]:
    """Return free variables for binder nodes (Quantifier, Lambda, SetComprehension).

    Domain expressions are NOT scoped by the binder's own variables per Z RM
    §3.9 (Quantifier), §3.12 (Lambda), §3.10 (SetComprehension).
    """
    if isinstance(expr, Quantifier):
        bound = frozenset(expr.variables)
        domain_free = expr_free_vars(expr.domain) if expr.domain is not None else _EMPTY
        body_free = expr_free_vars(expr.body) - bound
        expr_part_free = (
            expr_free_vars(expr.expression) - bound
            if expr.expression is not None
            else _EMPTY
        )
        return domain_free | body_free | expr_part_free

    if isinstance(expr, Lambda):
        bound = frozenset(expr.variables)
        return expr_free_vars(expr.domain) | (expr_free_vars(expr.body) - bound)

    # SetComprehension — sequential scoping within extra_declarations (Z RM §3.10).
    primary_bound = frozenset(expr.variables)
    domain_free = expr_free_vars(expr.domain) if expr.domain is not None else _EMPTY
    accumulated_bound = primary_bound
    extra_free: frozenset[str] = _EMPTY
    if expr.extra_declarations:
        for extra_var, extra_domain in expr.extra_declarations:
            extra_free = extra_free | (expr_free_vars(extra_domain) - accumulated_bound)
            accumulated_bound = accumulated_bound | {extra_var}
    all_bound = accumulated_bound
    pred_free = (
        expr_free_vars(expr.predicate) - all_bound
        if expr.predicate is not None
        else _EMPTY
    )
    expr_part_free = (
        expr_free_vars(expr.expression) - all_bound
        if expr.expression is not None
        else _EMPTY
    )
    return domain_free | extra_free | pred_free | expr_part_free


def _free_vars_schema_calculus(
    expr: SchemaCompose
    | SchemaPipe
    | SchemaProject
    | SchemaHide
    | SchemaRename
    | SchemaText,
) -> frozenset[str]:
    """Return free variables for schema-calculus nodes (conservative over-report).

    Shadow analysis requires a type-driven symbol table not present here.
    Over-reporting may produce unnecessary nesting but never fuzz-invalid Z.
    """
    if isinstance(expr, (SchemaCompose, SchemaPipe, SchemaProject)):
        return expr_free_vars(expr.left) | expr_free_vars(expr.right)
    if isinstance(expr, (SchemaHide, SchemaRename)):
        # Hidden/renamed names stay in the free-var set (conservative).
        return expr_free_vars(expr.schema)
    # SchemaText: collect predicates only; declaration-side names omitted.
    result: frozenset[str] = _EMPTY
    for pred in expr.predicates:
        result = result | expr_free_vars(pred)
    return result


def expr_free_vars(expr: Expr) -> frozenset[str]:
    """Return the set of free variable names in expr.

    Conservative: may over-report for schema-calculus nodes where shadow
    analysis requires type information.  Over-report produces unnecessary
    nesting (always Z-valid).  Under-report produces fuzz-rejected output
    — so err toward over-report.

    Z RM references:
    - Quantifier scoping: Z RM §3.9
    - Lambda scoping: Z RM §3.12
    - Set comprehension scoping: Z RM §3.10
    """
    # Leaf nodes
    if isinstance(expr, Identifier):
        return frozenset({expr.name})
    if isinstance(expr, (Number, StringLit)):
        return _EMPTY

    # Binder nodes
    if isinstance(expr, (Quantifier, Lambda, SetComprehension)):
        return _free_vars_binder(expr)

    # Schema-calculus nodes
    _schema_calc = (
        SchemaCompose,
        SchemaPipe,
        SchemaProject,
        SchemaHide,
        SchemaRename,
        SchemaText,
    )
    if isinstance(expr, _schema_calc):
        return _free_vars_schema_calculus(expr)

    # Pass-through nodes — union of children's free vars.
    if isinstance(expr, BinaryOp):
        return expr_free_vars(expr.left) | expr_free_vars(expr.right)
    if isinstance(expr, UnaryOp):
        return expr_free_vars(expr.operand)
    if isinstance(expr, Subscript):
        return expr_free_vars(expr.base) | expr_free_vars(expr.index)
    if isinstance(expr, Superscript):
        return expr_free_vars(expr.base) | expr_free_vars(expr.exponent)
    if isinstance(expr, FunctionApp):
        return expr_free_vars(expr.function) | _union(expr.args)
    if isinstance(expr, FunctionType):
        return expr_free_vars(expr.domain) | expr_free_vars(expr.range)
    if isinstance(expr, (Tuple, SetLiteral, BagLiteral, SequenceLiteral)):
        return _union(expr.elements)
    if isinstance(expr, RelationalImage):
        return expr_free_vars(expr.relation) | expr_free_vars(expr.set)
    if isinstance(expr, GenericInstantiation):
        return expr_free_vars(expr.base) | _union(expr.type_params)
    if isinstance(expr, Range):
        return expr_free_vars(expr.start) | expr_free_vars(expr.end)
    if isinstance(expr, TupleProjection):
        return expr_free_vars(expr.base)
    if isinstance(expr, Conditional):
        return (
            expr_free_vars(expr.condition)
            | expr_free_vars(expr.then_expr)
            | expr_free_vars(expr.else_expr)
        )
    if isinstance(expr, GuardedBranch):
        return expr_free_vars(expr.expression) | expr_free_vars(expr.guard)
    if isinstance(expr, GuardedCases):
        return _union(expr.branches)
    if isinstance(expr, Theta):
        return expr_free_vars(expr.expr)
    if isinstance(expr, Restrict):
        return expr_free_vars(expr.predicate) | expr_free_vars(expr.relation)
    if isinstance(expr, (Project, RelationRename, Group, Ungroup, GroupAggregate)):
        return expr_free_vars(expr.relation)
    if isinstance(expr, NaturalJoin):
        sub_free = (
            expr_free_vars(expr.subscript) if expr.subscript is not None else _EMPTY
        )
        return expr_free_vars(expr.left) | expr_free_vars(expr.right) | sub_free
    if isinstance(expr, Divide):
        return expr_free_vars(expr.left) | expr_free_vars(expr.right)
    # Binding is the only remaining Expr member at this point.
    msg = (
        f"expr_free_vars: Binding node not yet supported "
        f"(line={expr.line}, column={expr.column})"
    )
    raise NotImplementedError(msg)
