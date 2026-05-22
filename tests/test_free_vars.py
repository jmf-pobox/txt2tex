"""Regression tests for free_vars.expr_free_vars (#141)."""

from __future__ import annotations

import pytest

from txt2tex.ast_nodes import Binding
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
