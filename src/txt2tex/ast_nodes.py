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
    """Quantifier node (forall, exists, exists1).

    Phase 6 enhancement: Supports multiple variables with shared domain.
    Examples:
    - forall x : N | pred  -> variables=["x"], domain=N
    - forall x, y : N | pred -> variables=["x", "y"], domain=N
    - exists1 x : N | pred -> quantifier="exists1", variables=["x"]
    """

    quantifier: str  # "forall", "exists", or "exists1"
    variables: list[str]  # One or more variables (e.g., ["x", "y"])
    domain: Expr | None  # Optional domain shared by all variables (e.g., N, Z)
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


# Proof tree nodes (Phase 5 - Path C)


@dataclass(frozen=True)
class CaseAnalysis(ASTNode):
    """Case analysis branch (case q: ... case r: ...)."""

    case_name: str  # "q", "r", etc.
    steps: list[ProofNode]  # Proof steps for this case


@dataclass(frozen=True)
class ProofNode(ASTNode):
    """Node in a proof tree (Path C format)."""

    expression: Expr
    justification: (
        str | None
    )  # Optional rule name (e.g., "and elim", "=> intro from 1")
    label: int | None  # For assumptions: [1], [2], etc.
    is_assumption: bool  # True if this is marked [assumption]
    is_sibling: bool  # True if marked with :: (sibling premise)
    children: list[ProofNode | CaseAnalysis]  # Child proof nodes or case branches
    indent_level: int  # Indentation level (for parsing)


@dataclass(frozen=True)
class ProofTree(ASTNode):
    """Proof tree (Path C format) - conclusion with supporting proof."""

    conclusion: ProofNode  # The final conclusion at the top


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
