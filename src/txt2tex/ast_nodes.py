"""AST node definitions for txt2tex parser."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ASTNode:
    """Base class for all AST nodes."""

    line: int
    column: int


# Expression nodes (Phase 0)


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


@dataclass(frozen=True)
class Number(ASTNode):
    """Numeric literal node."""

    value: str


# Phase 3 expression nodes


@dataclass(frozen=True)
class Quantifier(ASTNode):
    """Quantifier node (forall, exists)."""

    quantifier: str  # "forall" or "exists"
    variable: str
    domain: Expr | None  # Optional domain (e.g., N, Z)
    body: Expr


@dataclass(frozen=True)
class Subscript(ASTNode):
    """Subscript node (a_1, x_i)."""

    base: Expr
    index: Expr


@dataclass(frozen=True)
class Superscript(ASTNode):
    """Superscript node (x^2, 2^n)."""

    base: Expr
    exponent: Expr


# Type alias for all expression types
Expr = BinaryOp | UnaryOp | Identifier | Number | Quantifier | Subscript | Superscript


# Document structure nodes (Phase 1)


@dataclass(frozen=True)
class Section(ASTNode):
    """Section with title and content."""

    title: str
    items: list[DocumentItem]


@dataclass(frozen=True)
class Solution(ASTNode):
    """Solution block with number and content."""

    number: str
    items: list[DocumentItem]


@dataclass(frozen=True)
class Part(ASTNode):
    """Part label with content."""

    label: str
    items: list[DocumentItem]


@dataclass(frozen=True)
class TruthTable(ASTNode):
    """Truth table with headers and rows."""

    headers: list[str]
    rows: list[list[str]]


# Equivalence chain nodes (Phase 2)


@dataclass(frozen=True)
class EquivStep(ASTNode):
    """Single step in an equivalence chain."""

    expression: Expr
    justification: str | None


@dataclass(frozen=True)
class EquivChain(ASTNode):
    """Equivalence chain with multiple steps."""

    steps: list[EquivStep]


# Z notation nodes (Phase 4)


@dataclass(frozen=True)
class GivenType(ASTNode):
    """Given type declaration (given A, B, C)."""

    names: list[str]


@dataclass(frozen=True)
class FreeType(ASTNode):
    """Free type definition (Type ::= branch1 | branch2)."""

    name: str
    branches: list[str]


@dataclass(frozen=True)
class Abbreviation(ASTNode):
    """Abbreviation definition (name == expression)."""

    name: str
    expression: Expr


@dataclass(frozen=True)
class Declaration(ASTNode):
    """Declaration in axdef or schema (var : Type)."""

    variable: str
    type_expr: Expr


@dataclass(frozen=True)
class AxDef(ASTNode):
    """Axiomatic definition block."""

    declarations: list[Declaration]
    predicates: list[Expr]


@dataclass(frozen=True)
class Schema(ASTNode):
    """Schema definition block."""

    name: str
    declarations: list[Declaration]
    predicates: list[Expr]


# Proof tree nodes (Phase 5)


@dataclass(frozen=True)
class ProofNode(ASTNode):
    """Node in a proof tree."""

    expression: Expr
    justification: str | None  # Optional rule name
    children: list[ProofNode]  # Child proof nodes
    indent_level: int  # Indentation level


@dataclass(frozen=True)
class ProofTree(ASTNode):
    """Proof tree with indentation-based structure."""

    nodes: list[ProofNode]  # Top-level nodes


# Type alias for document items (expressions or structural elements)
DocumentItem = (
    Expr
    | Section
    | Solution
    | Part
    | TruthTable
    | EquivChain
    | GivenType
    | FreeType
    | Abbreviation
    | AxDef
    | Schema
    | ProofTree
)


@dataclass(frozen=True)
class Document(ASTNode):
    """Document containing multiple expressions or blocks."""

    items: list[DocumentItem]
