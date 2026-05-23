"""Regression tests for free_vars.expr_free_vars (#141)."""

from __future__ import annotations

import pytest

from txt2tex.ast_nodes import Binding, GuardedBranch, GuardedCases, Identifier
from txt2tex.free_vars import expr_free_vars


def test_binding_raises_not_implemented() -> None:
    """expr_free_vars raises NotImplementedError for Binding nodes (#141).

    A Binding that silently fell through to the catch-all returned an
    incomplete free-variable set without any diagnostic.  The fix
    replaces the silent return with an explicit raise so callers know
    the node is unsupported rather than receiving wrong information.
    """
    node = Binding(line=1, column=1, pairs=[])
    with pytest.raises(NotImplementedError, match="Binding node not yet supported"):
        expr_free_vars(node)


def test_binding_error_includes_location() -> None:
    """NotImplementedError message includes line and column from the Binding node."""
    node = Binding(line=7, column=12, pairs=[])
    with pytest.raises(NotImplementedError, match="line=7, column=12"):
        expr_free_vars(node)


def _ident(name: str) -> Identifier:
    """Build a positionless Identifier for test construction."""
    return Identifier(name=name, line=1, column=1)


def test_guarded_cases_unions_branch_free_vars() -> None:
    """expr_free_vars on GuardedCases unions free vars across all branches.

    Regression for the _union(branches) call site at free_vars.py:201.
    Prior to Round 4 this was suppressed via `# type: ignore[arg-type]`
    because list[GuardedBranch] couldn't be passed as list[Expr] under
    mypy's invariant list subtyping; _union now accepts Iterable[Expr].
    Pin the runtime behaviour so the type change does not regress.
    """
    branch_one = GuardedBranch(
        guard=_ident("p"),
        expression=_ident("x"),
        line=1,
        column=1,
    )
    branch_two = GuardedBranch(
        guard=_ident("q"),
        expression=_ident("y"),
        line=2,
        column=1,
    )
    node = GuardedCases(branches=[branch_one, branch_two], line=1, column=1)
    assert expr_free_vars(node) == frozenset({"p", "q", "x", "y"})


def test_guarded_cases_empty_branches() -> None:
    """GuardedCases with no branches has no free variables."""
    node = GuardedCases(branches=[], line=1, column=1)
    assert expr_free_vars(node) == frozenset()
