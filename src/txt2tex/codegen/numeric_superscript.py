"""Reject numeric `^` heading into a fuzz-checked Z box.

Z's ``_^_`` operator (Z RM §4.11) is relational iteration: ``r^2`` means
``iter 2 r`` and requires ``r`` to be a homogeneous relation.  There is
no numeric-exponentiation operator in the toolkit, so a numeric base --
``x^2`` where ``x : N`` -- makes fuzz misparse the expression and reject
it with a cryptic type error citing ``iter 2 x``.  This module predicts
that failure at codegen time: it walks a box's body, classifies every
``Superscript`` base against the box's own local declarations, and
raises a clear, source-line error for every base that is provably
``\\num``-typed.

A relation-typed base (``r : S <-> S``, so ``r^2`` is genuine iteration)
must never be flagged -- Z is strongly typed and ``\\num`` is disjoint
from ``P(X cross X)``, so the classifier only fires when it can prove
the base numeric from declarations visible in the box; every other case
(a relation, a given-set element, an unprovable free name) is left for
fuzz to accept or reject on its own.
"""

from __future__ import annotations

from typing import cast

from txt2tex.ast_nodes import (
    BinaryOp,
    Declaration,
    Expr,
    FunctionApp,
    Identifier,
    Lambda,
    Number,
    Quantifier,
    Range,
    SchemaInclusion,
    SetComprehension,
    Superscript,
    UnaryOp,
)

# Type names whose declared domain proves \num (Z RM §4.11: N, Z, N1).
_NUMERIC_TYPE_NAMES = frozenset({"N", "Z", "N1"})

# BinaryOp operator strings that are unambiguously arithmetic in this
# grammar's token space -- each always yields a \num result.  "div" is
# deliberately excluded: this DSL's `div` keyword parses to the
# relational (Codd) division node (see ast_nodes.Divide, listed in
# fuzz_routing._DAT_EXPRESSION_TYPES as always RA-tainted), not Z RM's
# arithmetic div -- it never appears as a BinaryOp.operator value, so
# including the string here would be dead code.
_ARITHMETIC_BINARY_OPS = frozenset({"+", "-", "*", "mod"})

# Function names whose application always yields a \num result.
_ARITHMETIC_FUNCTION_NAMES = frozenset({"min", "max"})

Scope = dict[str, Expr | None]


class NumericSuperscriptError(Exception):
    """Raised when `^` denotes numeric exponentiation inside a fuzz-checked box.

    Z has no exponentiation operator; `_^_` is relational iteration
    (Z RM §4.11).  fuzz reads `x^2` as `iter 2 x`, which requires `x` to
    be a homogeneous relation.  Raised only when the base is *provably*
    `\\num`-typed from declarations local to the enclosing box -- a
    relation-typed base (`r^2` where `r : S <-> S`) is genuine iteration
    and never raises.
    """


def declaration_scope(declarations: list[Declaration | SchemaInclusion]) -> Scope:
    """Return the variable-to-domain scope for an axdef/gendef/schema box.

    A `SchemaInclusion` entry contributes no variable of its own -- it
    pulls in another box's declarations, which fuzz (not this checker)
    already knows about -- and is skipped.
    """
    return {
        decl.variable: decl.type_expr
        for decl in declarations
        if isinstance(decl, Declaration)
    }


def comprehension_scope(node: SetComprehension) -> Scope:
    """Return the variable-to-domain scope for a set comprehension's own binder."""
    scope: Scope = dict.fromkeys(node.variables, node.domain)
    if node.extra_declarations:
        scope.update(node.extra_declarations)
    return scope


def check_no_numeric_superscript(node: Expr, scope: Scope) -> None:
    """Raise `NumericSuperscriptError` for the first numeric `^` under `node`.

    `scope` seeds the walk with the enclosing box's own local
    declarations (build it with `declaration_scope` for an axdef/
    gendef/schema box; a `SetComprehension` builds its own scope
    internally, so `{}` is enough there).  Nested binders (`Quantifier`,
    `Lambda`, `SetComprehension`) extend the scope for their own subtree
    only, so a `Superscript` base is always classified against its
    nearest enclosing declaration -- an inner binder's domain shadows an
    outer one of the same name.
    """
    _walk(node, scope)


def _walk(node: object, scope: Scope) -> None:
    if isinstance(node, Superscript):
        _check_tower(node, scope)
        return
    if isinstance(node, SetComprehension):
        _walk_comprehension(node, scope)
        return
    if isinstance(node, Quantifier):
        _walk_quantifier(node, scope)
        return
    if isinstance(node, Lambda):
        _walk_lambda(node, scope)
        return
    if isinstance(node, (list, tuple)):
        items = cast("tuple[object, ...] | list[object]", node)
        for item in items:
            _walk(item, scope)
        return
    if isinstance(node, dict):
        mapping = cast("dict[object, object]", node)
        for value in mapping.values():
            _walk(value, scope)
        return
    fields = getattr(node, "__dataclass_fields__", None)
    if fields is None:
        return
    for field_name in fields:
        _walk(getattr(node, field_name), scope)


def _walk_comprehension(node: SetComprehension, scope: Scope) -> None:
    if node.domain is not None:
        _walk(node.domain, scope)
    if node.extra_declarations:
        for _name, domain_expr in node.extra_declarations:
            _walk(domain_expr, scope)
    inner_scope = {**scope, **comprehension_scope(node)}
    if node.predicate is not None:
        _walk(node.predicate, inner_scope)
    if node.expression is not None:
        _walk(node.expression, inner_scope)


def _walk_quantifier(node: Quantifier, scope: Scope) -> None:
    if node.domain is not None:
        _walk(node.domain, scope)
    inner_scope = scope
    if node.variables:
        inner_scope = {**scope, **dict.fromkeys(node.variables, node.domain)}
    _walk(node.body, inner_scope)
    if node.expression is not None:
        _walk(node.expression, inner_scope)
    if node.tuple_pattern is not None:
        _walk(node.tuple_pattern, inner_scope)


def _walk_lambda(node: Lambda, scope: Scope) -> None:
    _walk(node.domain, scope)
    inner_scope = {**scope, **dict.fromkeys(node.variables, node.domain)}
    _walk(node.body, inner_scope)


def _check_tower(node: Superscript, scope: Scope) -> None:
    """Unwind a `(base^a)^b^...` tower and classify by the innermost base.

    Every exponent in the chain is still walked for its own nested
    `Superscript` nodes (e.g. `x^(y^2)`); the innermost non-`Superscript`
    base is what the classification rule (jms) says decides the whole
    tower.
    """
    exponents: list[Expr] = []
    current: Expr = node
    while isinstance(current, Superscript):
        exponents.append(current.exponent)
        _walk(current.exponent, scope)
        current = current.base
    _walk(current, scope)

    if not _is_numeric(current, scope):
        return

    base_text = _base_text(node.base)
    exponent_text = _source_text(node.exponent)
    inner_text = _source_text(current)
    raise NumericSuperscriptError(
        _message(node.line, base_text, exponent_text, exponents, inner_text)
    )


def _is_numeric(expr: Expr, scope: Scope) -> bool:
    """True when `expr` is provably `\\num`-typed from `scope` alone."""
    if isinstance(expr, Number):
        return True
    if isinstance(expr, Identifier):
        domain = scope.get(expr.name)
        return domain is not None and _is_numeric_domain(domain)
    if isinstance(expr, BinaryOp):
        return expr.operator in _ARITHMETIC_BINARY_OPS
    if isinstance(expr, UnaryOp):
        return expr.operator == "#"
    if isinstance(expr, FunctionApp) and isinstance(expr.function, Identifier):
        return expr.function.name in _ARITHMETIC_FUNCTION_NAMES
    return False


def _is_numeric_domain(domain: Expr) -> bool:
    """True when `domain` is one of Z's numeric carriers: N, Z, N1, or a..b."""
    if isinstance(domain, Identifier):
        return domain.name in _NUMERIC_TYPE_NAMES
    return isinstance(domain, Range)


def _concrete_nonneg_int(expr: Expr) -> int | None:
    """Return the literal value of a non-negative integer `Number`, else None."""
    if isinstance(expr, Number) and expr.value.isdigit():
        return int(expr.value)
    return None


def _expansion(exponents: list[Expr], base_text: str) -> str | None:
    """Return the structured k-fold-product rewrite, or None when none exists.

    `exponents` holds every level of a `(base^a)^b^...` tower, outermost
    first (as `_check_tower` collects them).  A rewrite exists only when
    every exponent is a concrete non-negative integer literal; a symbolic
    or negative exponent at any level means there is no finite rewrite to
    suggest.

    Expansion proceeds innermost level first, and each level's result
    becomes the repeated unit for the next level out -- parenthesized
    whenever it is itself a product (k >= 2), so the nesting stays
    visible: `(x^2)^3` becomes `(x * x) * (x * x) * (x * x)`, never the
    flattened `x*x*x*x*x*x`.  A single-level tower degenerates to the
    plain product: `x^3` -> `x * x * x`.
    """
    ks: list[int] = []
    for exp in exponents:
        k = _concrete_nonneg_int(exp)
        if k is None:
            return None
        ks.append(k)

    text = base_text
    is_product = False
    for k in reversed(ks):  # innermost level first
        if k == 0:
            text = "1"
            is_product = False
        elif k == 1:
            pass  # (E)^1 == E -- level contributes nothing
        else:
            unit = f"({text})" if is_product else text
            text = " * ".join([unit] * k)
            is_product = True
    return text


def _base_text(base: Expr) -> str:
    """Render `base` for use as a Superscript's base, parenthesizing a tower."""
    text = _source_text(base)
    return f"({text})" if isinstance(base, Superscript) else text


def _source_text(expr: Expr) -> str:
    """Return a short, source-like rendering of `expr` for diagnostics.

    Not a LaTeX renderer -- just enough to echo the constructs this
    module classifies (identifiers, numbers, arithmetic, cardinality,
    towers) back at the user in their own notation.
    """
    if isinstance(expr, Identifier):
        return expr.name
    if isinstance(expr, Number):
        return expr.value
    if isinstance(expr, BinaryOp):
        return f"{_source_text(expr.left)} {expr.operator} {_source_text(expr.right)}"
    if isinstance(expr, UnaryOp):
        return f"{expr.operator}{_source_text(expr.operand)}"
    if isinstance(expr, FunctionApp) and isinstance(expr.function, Identifier):
        args = ", ".join(_source_text(arg) for arg in expr.args)
        return f"{expr.function.name}({args})"
    if isinstance(expr, Range):
        return f"{_source_text(expr.start)}..{_source_text(expr.end)}"
    if isinstance(expr, Superscript):
        return f"{_base_text(expr.base)}^{_source_text(expr.exponent)}"
    return "..."


def _message(
    line: int,
    base_text: str,
    exponent_text: str,
    exponents: list[Expr],
    inner_text: str,
) -> str:
    header = (
        f"line {line}: '^' denotes relational iteration in Z, not numeric power "
        "(there is no exponentiation operator in the toolkit). fuzz reads "
        f"'{base_text}^{exponent_text}' as 'iter {exponent_text} {base_text}' "
        f"and requires {base_text} to be a homogeneous relation, but {base_text} "
        "is a number here."
    )
    expansion = _expansion(exponents, inner_text)
    if expansion is None:
        workaround = "Mark the box NOFUZZ, or use --zed."
    else:
        workaround = f"Rewrite as '{expansion}', or mark the box NOFUZZ, or use --zed."
    return f"{header} {workaround}"
