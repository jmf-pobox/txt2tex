"""AST node definitions for txt2tex parser."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ASTNode:
    """Base class for all AST nodes."""

    line: int
    column: int


@dataclass(frozen=True)
class BinaryOp(ASTNode):
    """Binary operation node (and, or, =>, <=>)."""

    operator: str
    left: Expr
    right: Expr


@dataclass(frozen=True)
class UnaryOp(ASTNode):
    """Unary operation node (not)."""

    operator: str
    operand: Expr


@dataclass(frozen=True)
class Identifier(ASTNode):
    """Identifier node (variable name)."""

    name: str


# Type alias for all expression types
Expr = BinaryOp | UnaryOp | Identifier
