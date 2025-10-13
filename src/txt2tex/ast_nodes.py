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
    """Quantifier node (forall, exists, exists1, mu).

    Phase 6 enhancement: Supports multiple variables with shared domain.
    Phase 7 enhancement: Supports mu-operator (definite description).
    Phase 11.5 enhancement: Supports mu with expression part (mu x : X | P . E).
    Examples:
    - forall x : N | pred  -> variables=["x"], domain=N, body=pred
    - forall x, y : N | pred -> variables=["x", "y"], domain=N, body=pred
    - exists1 x : N | pred -> quantifier="exists1", variables=["x"], body=pred
    - mu x : N | pred -> quantifier="mu", variables=["x"], body=pred, expression=None
    - mu x : N | pred . expr -> quantifier="mu", body=pred, expression=expr
    """

    quantifier: str  # "forall", "exists", "exists1", or "mu"
    variables: list[str]  # One or more variables (e.g., ["x", "y"])
    domain: Expr | None  # Optional domain shared by all variables (e.g., N, Z)
    body: Expr  # Predicate/body expression
    expression: Expr | None = None  # Optional expression part (mu only)


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


@dataclass(frozen=True)
class SetComprehension(ASTNode):
    """Set comprehension node (Phase 8).

    Supports two forms:
    - Set by predicate: { x : X | predicate } (expression=None)
    - Set by expression: { x : X | predicate . expression }

    Examples:
    - { x : N | x > 0 } -> variables=["x"], domain=N, predicate=(x > 0),
                           expression=None
    - { x : N | x > 0 . x^2 } -> variables=["x"], domain=N,
                                  predicate=(x > 0), expression=(x^2)
    - { x, y : N | x + y = 4 } -> variables=["x", "y"], domain=N,
                                   predicate=(x+y=4)
    """

    variables: list[str]  # One or more variables (e.g., ["x"], ["x", "y"])
    domain: Expr | None  # Optional domain (e.g., N, Z, P X)
    predicate: Expr  # The condition/predicate
    expression: Expr | None  # Optional expression (if present, set by expression)


@dataclass(frozen=True)
class SetLiteral(ASTNode):
    """Set literal node (Phase 11.5).

    Represents explicit set literals: {1, 2, 3}, {a, b, c}, {}

    Examples:
    - {1, 2, 3} -> elements=[Number("1"), Number("2"), Number("3")]
    - {a, b} -> elements=[Identifier("a"), Identifier("b")]
    - {} -> elements=[]  (empty set)
    """

    elements: list[Expr]  # List of elements in the set (can be empty)


@dataclass(frozen=True)
class FunctionApp(ASTNode):
    """Function application node (Phase 11b).

    Represents function application: f(x), g(x, y, z)
    Also used for generic instantiation: seq(N), P(X)

    Examples:
    - f(x) -> name="f", args=[Identifier("x")]
    - g(x, y, z) -> name="g", args=[Identifier("x"), Identifier("y"), Identifier("z")]
    - seq(N) -> name="seq", args=[Identifier("N")]
    - f(g(h(x))) -> name="f", args=[FunctionApp("g", [FunctionApp("h", [...])])]
    """

    name: str  # Function name
    args: list[Expr]  # Argument list (can be empty for f())


@dataclass(frozen=True)
class FunctionType(ASTNode):
    """Function type node (Phase 11c).

    Represents function type arrows: X -> Y, X +-> Y, X >-> Y, etc.

    Arrow types:
    - "->" : total function (\\fun)
    - "+->" : partial function (\\pfun)
    - "->>" : total injection (\\inj)
    - ">+>" : partial injection (\\pinj)
    - "-->>" : total surjection (\\surj)
    - "+->>" : partial surjection (\\psurj)
    - ">->>" : bijection (\\bij)

    Examples:
    - X -> Y : total function from X to Y
    - N +-> N : partial function from N to N
    - A -> B -> C : curried function (right-associative: A -> (B -> C))
    """

    arrow: str  # Arrow type ("->", "+->", ">>", etc.)
    domain: Expr  # Domain type
    range: Expr  # Range type


@dataclass(frozen=True)
class Lambda(ASTNode):
    """Lambda expression node (Phase 11d).

    Represents lambda expressions: lambda x : X . body

    Supports multiple variables with shared domain:
    - lambda x : X . x
    - lambda x, y : N . x + y
    - lambda f : X -> Y . lambda x : X . f(x)

    Examples:
    - lambda x : N . x^2 -> variables=["x"], domain=N, body=(x^2)
    - lambda x, y : N . x + y -> variables=["x", "y"], domain=N, body=(x+y)
    """

    variables: list[str]  # One or more variables (e.g., ["x"], ["x", "y"])
    domain: Expr  # Domain type expression
    body: Expr  # Lambda body expression


@dataclass(frozen=True)
class Tuple(ASTNode):
    """Tuple expression node (Phase 11.6).

    Represents tuple expressions: (a, b), (x, y, z)

    Tuples are multi-element ordered collections, commonly used in:
    - Cartesian products: (1, 2), (a, b, c)
    - Set comprehensions: { x : N | x > 0 . (x, x^2) }
    - Relations: (person, age)

    Examples:
    - (1, 2) -> elements=[Number("1"), Number("2")]
    - (x, y, z) -> elements=[Identifier("x"), Identifier("y"), Identifier("z")]
    - (a, b+1, f(c)) -> elements=[Identifier("a"), BinaryOp("+", ...), FunctionApp(...)]

    Note: Single-element tuples like (x) are parsed as parenthesized expressions,
    not tuples. Tuples require at least 2 elements.
    """

    elements: list[Expr]  # List of tuple elements (minimum 2)


@dataclass(frozen=True)
class RelationalImage(ASTNode):
    r"""Relational image node (Phase 11.8).

    Represents relational image: R(| S |)

    The relational image R(| S |) gives the image of set S under relation R.
    For a relation R : X <-> Y and set S : P X, R(| S |) is the set
    {y : Y | exists x : S | x |-> y in R}

    Examples:
    - R(| {1, 2} |) -> relation=R, set={1, 2}
    - parentOf(| {john} |) -> relation=parentOf, set={john}
    - (R o9 S)(| A |) -> relation=(R o9 S), set=A

    LaTeX rendering: R(\limg S \rimg)
    """

    relation: Expr  # The relation R
    set: Expr  # The set S


@dataclass(frozen=True)
class GenericInstantiation(ASTNode):
    """Generic type instantiation node (Phase 11.9).

    Represents generic type instantiation: Type[A, B]

    In Z notation, generic types can be instantiated with specific type parameters.
    This is written as the base type followed by type arguments in square brackets.

    Examples:
    - ∅[N] -> base=∅, type_params=[N]  (empty set of type N)
    - seq[N] -> base=seq, type_params=[N]  (sequence of N)
    - P[X] -> base=P, type_params=[X]  (power set of X)
    - ∅[N cross N] -> base=∅, type_params=[N cross N]  (empty relation)
    - Type[A, B] -> base=Type, type_params=[A, B]  (multi-parameter)

    LaTeX rendering: base[type_params] or special notation depending on base
    """

    base: Expr  # The generic type being instantiated
    type_params: list[Expr]  # Type parameters (at least one)


# Sequence nodes (Phase 12)


@dataclass(frozen=True)
class SequenceLiteral(ASTNode):
    """Sequence literal node (Phase 12).

    Represents sequence literals: ⟨⟩, ⟨a⟩, ⟨a, b, c⟩

    Sequences are ordered lists of elements. The empty sequence is written ⟨⟩.

    Examples:
    - ⟨⟩ -> elements=[]  (empty sequence)
    - ⟨a⟩ -> elements=[Identifier("a")]
    - ⟨1, 2, 3⟩ -> elements=[Number("1"), Number("2"), Number("3")]
    - ⟨x, y+1, f(z)⟩ -> elements=[Identifier("x"), BinaryOp("+", ...), FunctionApp(...)]

    LaTeX rendering: \\langle elements \\rangle
    """

    elements: list[Expr]  # List of sequence elements (can be empty)


@dataclass(frozen=True)
class TupleProjection(ASTNode):
    """Tuple projection node (Phase 12).

    Represents tuple component access: x.1, x.2, x.3

    Used to access specific components of tuples in sequences and relations.

    Examples:
    - x.1 -> base=Identifier("x"), index=1
    - (a, b, c).2 -> base=Tuple([...]), index=2
    - f(x).3 -> base=FunctionApp(...), index=3

    LaTeX rendering: base.index (stays the same)
    """

    base: Expr  # The tuple expression
    index: int  # Component index (1-based: 1, 2, 3, ...)


@dataclass(frozen=True)
class BagLiteral(ASTNode):
    """Bag literal node (Phase 12).

    Represents bag (multiset) literals: [[x]], [[a, b, c]]

    Bags are unordered collections where elements can appear multiple times.
    The notation [[x]] creates a bag containing a single element x.

    Examples:
    - [[x]] -> elements=[Identifier("x")]
    - [[1, 2, 2, 3]] -> elements=[Number("1"), Number("2"), Number("2"), Number("3")]

    LaTeX rendering: \\lbag elements \\rbag
    """

    elements: list[Expr]  # List of bag elements (can have duplicates)


# Type alias for all expression types
Expr = (
    BinaryOp
    | UnaryOp
    | Identifier
    | Number
    | Quantifier
    | Subscript
    | Superscript
    | SetComprehension
    | SetLiteral
    | FunctionApp
    | FunctionType
    | Lambda
    | Tuple
    | RelationalImage
    | GenericInstantiation
    | SequenceLiteral
    | TupleProjection
    | BagLiteral
)


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
    """Abbreviation definition (name == expression).

    Phase 9 enhancement: Supports generic parameters [X, Y, ...].
    Example: [X] Pairs == X x X
    """

    name: str
    expression: Expr
    generic_params: list[str] | None = None  # Optional generic parameters


@dataclass(frozen=True)
class Declaration(ASTNode):
    """Declaration in axdef or schema (var : Type)."""

    variable: str
    type_expr: Expr


@dataclass(frozen=True)
class AxDef(ASTNode):
    """Axiomatic definition block.

    Phase 9 enhancement: Supports generic parameters [X, Y, ...].
    Example:
    axdef [X]
      f : X -> X
    where
      forall x : X | f(x) = x
    end
    """

    declarations: list[Declaration]
    predicates: list[Expr]
    generic_params: list[str] | None = None  # Optional generic parameters


@dataclass(frozen=True)
class Schema(ASTNode):
    """Schema definition block.

    Phase 9 enhancement: Supports generic parameters [X, Y, ...].
    Example:
    schema GenericStack[X]
      items : seq X
    where
      # items <= 100
    end
    """

    name: str
    declarations: list[Declaration]
    predicates: list[Expr]
    generic_params: list[str] | None = None  # Optional generic parameters


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


# Text paragraph node (Phase 0 - originally planned, now implementing)


@dataclass(frozen=True)
class Paragraph(ASTNode):
    """Plain text paragraph.

    Simple text content that gets rendered as-is in LaTeX.
    No inline math parsing yet - that's a future enhancement.
    """

    text: str  # The paragraph content


# Type alias for document items (expressions or structural elements)
DocumentItem = (
    Expr
    | Section
    | Solution
    | Part
    | Paragraph
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
