"""AST node definitions for txt2tex parser.

Nodes use ``@dataclass(frozen=True)``.  This protects against accidental
attribute rebinding; it does *not* deep-freeze ``list``-valued fields.
Calling ``hash()`` on a node that carries a mutable list raises
``TypeError`` — the correct behaviour, since these nodes are never used
as dict keys or set elements.  A future call site that needs hashability
should switch the relevant field to a ``tuple``.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Literal


@dataclass(frozen=True)
class ASTNode:
    """Base class for all AST nodes."""

    line: int
    column: int


# Expression nodes


@dataclass(frozen=True)
class BinaryOp(ASTNode):
    """Binary operation node (and, or, =>, <=>).

    When line_break_after is True, LaTeX generator inserts \\\\ after the operator.

    When explicit_parens is True, parentheses are always generated in LaTeX output,
    even if not required by precedence rules. This preserves semantic grouping and
    clarity from the source text.
    """

    operator: str
    left: Expr
    right: Expr
    line_break_after: bool = False  # True if \\ continuation follows operator
    explicit_parens: bool = False  # True if expression was explicitly wrapped in ()


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


@dataclass(frozen=True)
class StringLit(ASTNode):
    """String literal node ('quoted value').

    Carries the content between the single quotes, with escape sequences
    already resolved (\\' → ').  The generator emits the Z-convention
    LaTeX-quote form: \\text{`value'}.
    """

    value: str


# Quantifier expression nodes


@dataclass(frozen=True)
class SchemaBinding(ASTNode):
    """Schema-text binding in a quantifier (Z RM §3.10).

    Used when a quantifier binds a schema name rather than individual
    variables with a domain.  The four forms are:

    - decoration="Delta"  →  exists Delta S | P    (state-change)
    - decoration="Xi"     →  exists Xi S | P       (read-only)
    - decoration="None"   →  exists S | P          (schema-as-declaration)
    - decoration="Prime"  →  exists S' | P         (primed schema)

    The schema_name field carries the raw identifier value, including any
    prime suffix already baked in by the lexer (e.g., ``"S'"`` for the
    primed form).  The decoration field records the explicit keyword prefix,
    if any.

    fuzz expands the invariant; the engine emits the schema reference
    literally (jms ruling 2026-05-21).
    """

    decoration: Literal["Delta", "Xi", "None", "Prime"]
    schema_name: str  # Raw identifier (e.g., "S", "S'", "BoxOffice")


@dataclass(frozen=True)
class Quantifier(ASTNode):
    """Quantifier node (forall, exists, exists1, mu).

    Supports:
        - Multiple variables with shared domain (value_binding path)
        - Schema-text quantification (schema_binding path, Z RM §3.10)
        - Mu-operator (definite description)
        - Mu with expression part (mu x : X | P . E)
        - Tuple patterns for destructuring
        - Bullet separator for all quantifiers

    Exactly one of ``value_binding`` and ``schema_binding`` is populated.
    When ``schema_binding`` is not None the ``variables``, ``domain``, and
    ``tuple_pattern`` fields are unused (empty/None) and the ``body`` carries
    the predicate after ``|``.

    Examples (value-binding path):
    - forall x : N | pred  -> variables=["x"], domain=N, body=pred
    - forall x : N | constraint . body -> body=constraint, expression=body
    - forall x, y : N | pred -> variables=["x", "y"], domain=N, body=pred
    - forall (x, y) : T | pred -> variables=["x", "y"], tuple_pattern
    - exists x : N | constraint . body -> body=constraint, expression=body
    - exists1 x : N | pred -> quantifier="exists1", variables=["x"]
    - mu x : N | pred -> quantifier="mu", body=pred, expression=None
    - mu x : N | pred . expr -> quantifier="mu", body=pred, expression=expr

    Examples (schema-binding path):
    - exists Delta S | P -> schema_binding=SchemaBinding("Delta", "S"), body=P
    - exists Xi S | P    -> schema_binding=SchemaBinding("Xi", "S"), body=P
    - exists S | P       -> schema_binding=SchemaBinding("None", "S"), body=P
    - exists S' | P      -> schema_binding=SchemaBinding("Prime", "S'"), body=P
    - forall Delta S | P -> schema_binding=SchemaBinding("Delta", "S"), body=P

    Note on expression field semantics:
    - For mu: expression is the term/value to select
      (e.g., f(x) in mu x : N | P . f(x))
    - For forall/exists/exists1: expression is body predicate after constraint
      (e.g., forall x : N | x > 0 . x < 10 has body="x > 0", expr="x < 10")
    """

    quantifier: str  # "forall", "exists", "exists1", or "mu"
    variables: list[str]  # One or more variables (e.g., ["x", "y"])
    domain: Expr | None  # Optional domain shared by all variables (e.g., N, Z)
    body: Expr  # Constraint (before bullet) or full body (without bullet)
    expression: Expr | None = None  # Body after bullet (all quantifiers)
    line_break_after_pipe: bool = False  # True if \ continuation after |
    line_break_after_bullet: bool = False  # True if line break after . separator
    tuple_pattern: Expr | None = None  # Tuple pattern for destructuring
    schema_binding: SchemaBinding | None = None  # Schema-text binding (Z RM §3.10)


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
    """Set comprehension node.

    Supports three forms:
        - Set by predicate: { x : X | predicate } (expression=None)
        - Set by expression with predicate: { x : X | predicate . expression }
        - Set by expression only: { x : X . expression } (predicate=None)

    Examples:
    - { x : N | x > 0 } -> variables=["x"], domain=N, predicate=(x > 0),
                           expression=None
    - { x : N | x > 0 . x^2 } -> variables=["x"], domain=N,
                                  predicate=(x > 0), expression=(x^2)
    - { x : N . x^2 } -> variables=["x"], domain=N, predicate=None,
                          expression=(x^2)
    """

    variables: list[str]  # One or more variables (e.g., ["x"], ["x", "y"])
    domain: Expr | None  # Optional domain (e.g., N, Z, P X)
    predicate: Expr | None  # The condition/predicate (can be None)
    expression: Expr | None  # Optional expression (if present, set by expression)
    # Additional semicolon-separated declaration groups for multi-typed bindings:
    # { s : Ship; c : Class | ... } → extra_declarations=[("c", Class)]
    extra_declarations: list[tuple[str, Expr]] | None = None
    line_break_after_pipe: bool = False
    line_break_after_bullet: bool = False


@dataclass(frozen=True)
class SetLiteral(ASTNode):
    """Set literal node.

    Represents explicit set literals: {1, 2, 3}, {a, b, c}, {}

    Examples:
    - {1, 2, 3} -> elements=[Number("1"), Number("2"), Number("3")]
    - {a, b} -> elements=[Identifier("a"), Identifier("b")]
    - {} -> elements=[]  (empty set)
    """

    elements: list[Expr]  # List of elements in the set (can be empty)


@dataclass(frozen=True)
class FunctionApp(ASTNode):
    """Function application node.

    Represents function application: f(x), g(x, y, z), ⟨a, b, c⟩(2)
    Also used for sequence indexing and generic instantiation: seq(N), P(X)

    Supports applying any expression, not just identifiers.

    Examples:
    - f(x) -> function=Identifier("f"), args=[Identifier("x")]
    - g(x, y, z) -> function=Identifier("g"), args=[Identifier("x"),...]
    - seq(N) -> function=Identifier("seq"), args=[Identifier("N")]
    - f(g(h(x))) -> function=Identifier("f"), args=[FunctionApp(...)]
    - ⟨a, b, c⟩(2) -> function=SequenceLiteral([...]), args=[Number("2")]
    - (f ++ g)(x) -> function=BinaryOp("++", ...), args=[Identifier("x")]
    """

    function: Expr  # Function expression (can be any expression)
    args: list[Expr]  # Argument list (can be empty for f())


@dataclass(frozen=True)
class FunctionType(ASTNode):
    """Function type node.

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
    """Lambda expression node.

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
    """Tuple expression node.

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
    r"""Relational image node.

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
    """Generic type instantiation node.

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


@dataclass(frozen=True)
class SchemaCompose(ASTNode):
    """Schema composition node (Z RM §3.11).

    Represents ``S ; T`` — combine two operations sequentially.

    The composed schema ``S ; T`` connects the output state of S to the
    input state of T by identifying primed components of S with unprimed
    components of T, then hiding the intermediate state.

    Examples:
    - OpA ; OpB      -> left=Identifier("OpA"), right=Identifier("OpB")
    - (S ; T) ; U   -> nested composition (left-associative)

    LaTeX rendering: S \\semi T
    """

    left: Expr
    right: Expr


@dataclass(frozen=True)
class SchemaPipe(ASTNode):
    """Schema piping node (Z RM §3.11).

    Represents ``S >> T`` — pipeline two operations output-to-input.

    Piping connects the output of S to the input of T by identifying the
    output channel of S (decorated with ``!``) with the input channel of T
    (decorated with ``?``), then hiding the communication channels.

    Examples:
    - Send >> Receive  -> left=Identifier("Send"), right=Identifier("Receive")

    LaTeX rendering: S \\pipe T
    """

    left: Expr
    right: Expr


@dataclass(frozen=True)
class SchemaHide(ASTNode):
    """Schema hiding node (Z RM §3.11).

    Represents ``S hide (x, y)`` — existentially quantify components.

    Hiding removes the named components from the signature of S, replacing
    them with existential quantification in the predicate part.

    Examples:
    - S hide (x)         -> schema=Identifier("S"), names=["x"]
    - S hide (x, y, z)   -> schema=Identifier("S"), names=["x", "y", "z"]

    LaTeX rendering: S \\hide (x, y)
    """

    schema: Expr
    names: list[str]


@dataclass(frozen=True)
class SchemaProject(ASTNode):
    """Schema projection node (Z RM §3.11).

    Represents ``S project T`` — project schema S onto the signature of T.

    The result is the schema with the same predicate as S but restricted to
    the components declared in T.

    Examples:
    - S project T   -> left=Identifier("S"), right=Identifier("T")

    LaTeX rendering: S \\project T
    """

    left: Expr
    right: Expr


@dataclass(frozen=True)
class SchemaRename(ASTNode):
    """Schema renaming node (Z RM §3.11).

    Represents ``S[new/old, ...]`` — produce a schema identical to S except
    that each component named ``old`` is renamed to ``new``.

    Per Z RM §3.11 the NEW name appears first, the OLD name second.

    The schema expression is typically a plain (possibly decorated) Identifier.
    The ``pairs`` list holds ``(new_name, old_name)`` tuples in source order;
    at least one pair is required.

    Examples:
    - S[a/b]         -> schema=Identifier("S"),  pairs=[("a", "b")]  # new=a, old=b
    - S[a/b, c/d]    -> schema=Identifier("S"),  pairs=[("a", "b"), ("c", "d")]
    - S'[a/b]        -> schema=Identifier("S'"), pairs=[("a", "b")]
    - S[a'/b]        -> schema=Identifier("S"),  pairs=[("a'", "b")]

    Disambiguation from GenericInstantiation: the parser scans the bracket
    contents at depth 0 before committing.  If any ``/`` token appears, this
    node is constructed; otherwise GenericInstantiation is constructed.

    LaTeX rendering: schema_repr[new/old, ...]
    """

    schema: Expr  # Schema reference (typically a decorated Identifier)
    pairs: list[tuple[str, str]]  # (new_name, old_name) per Z RM §3.11, at least one


# Range node


@dataclass(frozen=True)
class Range(ASTNode):
    """Range expression node.

    Represents integer range expressions: m..n

    Creates the set {m, m+1, m+2, ..., n} in Z notation.

    Examples:
    - 1..10 -> range(Number("1"), Number("10"))
    - 1993..current -> range(Number("1993"), Identifier("current"))
    - x.2..x.3 -> range(TupleProjection(...), TupleProjection(...))

    LaTeX rendering: start \\upto end
    """

    start: Expr  # Start of range (inclusive)
    end: Expr  # End of range (inclusive)


# Sequence nodes


@dataclass(frozen=True)
class SequenceLiteral(ASTNode):
    """Sequence literal node.

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
    """Tuple projection node.

    Represents tuple component access: x.1, x.2, x.3, or schema field access: e.name

    Used to access specific components of tuples or named fields of schemas.

    Examples:
    - x.1 -> base=Identifier("x"), index=1 (numeric projection)
    - (a, b, c).2 -> base=Tuple([...]), index=2 (numeric projection)
    - f(x).3 -> base=FunctionApp(...), index=3 (numeric projection)
    - e.name -> base=Identifier("e"), index="name" (named field projection)
    - record.status -> base=Identifier("record"), index="status"
                        (named field projection)

    LaTeX rendering: base.index (stays the same)

    Note: Fuzz only supports named field projection (identifiers),
    not numeric projection.
    """

    base: Expr  # The tuple or schema expression
    index: int | str  # Component index (1-based: 1, 2, 3, ...) or field name


@dataclass(frozen=True)
class BagLiteral(ASTNode):
    """Bag literal node.

    Represents bag (multiset) literals: [[x]], [[a, b, c]]

    Bags are unordered collections where elements can appear multiple times.
    The notation [[x]] creates a bag containing a single element x.

    Examples:
    - [[x]] -> elements=[Identifier("x")]
    - [[1, 2, 2, 3]] -> elements=[Number("1"), Number("2"), Number("2"), Number("3")]

    LaTeX rendering: \\lbag elements \\rbag
    """

    elements: list[Expr]  # List of bag elements (can have duplicates)


@dataclass(frozen=True)
class Conditional(ASTNode):
    """Conditional expression node.

    Represents conditional expressions: if condition then expr1 else expr2

    Used in function definitions and mathematical expressions to express
    conditional logic.

    Examples:
    - if x > 0 then x else -x -> condition=(x > 0), then_expr=x, else_expr=(-x)
    - if s = <> then 0 else 1 -> condition=(s = <>), then_expr=0, else_expr=1

    Line breaks can be inserted using \\ at the end of a line:
    - if x > 0 \\
        then x \\
        else -x

    LaTeX rendering: Uses cases environment or inline conditional notation
    """

    condition: Expr  # The conditional predicate
    then_expr: Expr  # Expression when condition is true
    else_expr: Expr  # Expression when condition is false
    line_break_after_condition: bool = False  # Line break before 'then'
    line_break_after_then: bool = False  # Line break before 'else'


@dataclass(frozen=True)
class GuardedBranch(ASTNode):
    """A single branch in a guarded cases expression.

    Represents: expression if guard

    Used in function definitions with multiple conditional branches.

    Example:
    - <x> ^ (premium_plays s) if user_status(x.2) = premium
      -> expression=<x> ^ (premium_plays s), guard=(user_status(x.2) = premium)
    """

    expression: Expr  # The expression for this branch
    guard: Expr  # The condition/guard for this branch


@dataclass(frozen=True)
class GuardedCases(ASTNode):
    """Guarded cases expression.

    Represents multiple conditional branches:
      expr1 if cond1
      expr2 if cond2
      ...

    Used in axiomatic definitions with case-based function definitions.

    Example:
    f(x) =
      expr1 if cond1
      expr2 if cond2

    LaTeX rendering: Multiple lines with \text{if} guards
    """

    branches: list[GuardedBranch]  # List of conditional branches


@dataclass(frozen=True)
class Theta(ASTNode):
    r"""θ-expression (Z RM §3.10).

    ``theta S`` constructs the binding whose components are the in-scope
    variables matching schema S's signature.  The schema reference is
    typically an Identifier, optionally Phase-0 decorated (e.g.,
    Identifier("Booking'") for ``theta Booking'``).

    Examples:
    - theta S       -> expr=Identifier("S")
    - theta S'      -> expr=Identifier("S'")
    - theta Booking -> expr=Identifier("Booking")

    LaTeX rendering: \theta S  (Greek letter, no macro change needed)
    """

    expr: Expr  # Schema reference (typically a decorated Identifier)


@dataclass(frozen=True)
class SchemaText(ASTNode):
    r"""Inline schema text in a horizontal definition (Z RM §3.8).

    Written as ``[ decl-list | pred-list ]`` on the RHS of a ``defs``
    paragraph.  Combines a declaration section with an optional predicate
    section in a single bracket form.

    Examples:
    - [ x, y : N | x < y ]
      -> declarations=[Declaration("x", N), Declaration("y", N)]
         predicates=[BinaryOp("<", x, y)]
    - [ x : N | x > 0; x < 100 ]
      -> declarations=[Declaration("x", N)]
         predicates=[BinaryOp(">", x, 0), BinaryOp("<", x, 100)]

    LaTeX rendering: [ decl1; decl2 | pred1 \land pred2 ]

    Note: ``predicates`` is a flat list.  Z RM §3.6 separates predicates
    within a schema text with ``;``; those are collected here in order.
    Blank-line grouping (for ``\also`` generation) is not applicable to
    the inline form, so no nested list structure is needed.
    """

    declarations: list[Declaration | SchemaInclusion]
    predicates: list[Expr]  # Flat list; ';' separated in source


# Aggregator support (Phase 4.2 — GROUP aggregate form)


class Aggregator(Enum):
    """Aggregation function names for the GROUP aggregate form."""

    COUNT = auto()
    SUM = auto()
    AVG = auto()
    MIN = auto()
    MAX = auto()
    MEDIAN = auto()

    def label(self) -> str:
        """Return the display label used in \\mathrm{...} output."""
        return self.name.capitalize()


@dataclass(frozen=True)
class AggregatorClause(ASTNode):
    """Single aggregator application inside a GROUP aggregate expression.

    Represents ``Count(attr) as alias``.  The rendered form is
    ``\\mathrm{Count}(attr)~\\mathrm{as}~alias``.
    """

    agg: Aggregator
    attr: str  # Single attribute identifier (no nested expressions)
    alias: str  # Name the aggregated column receives in the output relation


# Relational algebra nodes (Phase 2.2)


@dataclass(frozen=True)
class Restrict(ASTNode):
    """Relational restriction (sigma) node.

    Represents sigma[predicate](relation) — select tuples satisfying predicate.

    Example:
    - sigma[bore >= 16](Class) -> predicate=(bore >= 16), relation=Class
    """

    predicate: Expr
    relation: Expr


@dataclass(frozen=True)
class Project(ASTNode):
    """Relational projection (pi) node.

    Represents pi[A, B](relation) — keep only named attributes.

    Example:
    - pi[class, country](Class) -> attrs=["class", "country"], relation=Class
    """

    attrs: list[str]
    relation: Expr


@dataclass(frozen=True)
class RelationRename(ASTNode):
    """Relation renaming node (Z RM §3.11).

    Represents ``R[new/old, ...]`` — rename attributes of a relation.

    Per Z RM §3.11 the NEW name appears first, the OLD name second.
    The ``pairs`` list holds ``(new_name, old_name)`` tuples in source order.

    The ``relation`` field accepts any expression (compound operands supported,
    per jra decision A, 2026-05-23).  Examples:

    - R[b/a]                            -> relation=Identifier("R"), pairs=[("b", "a")]
    - R[b/a, d/c]   -> relation=Identifier("R"), pairs=[("b", "a"), ("d", "c")]
    - (pi[x](R))[b/a]                   -> relation=Project(...), pairs=[("b", "a")]
    - (pi[t](sigma[w='Ali'](M)))[id/t]  -> relation=Project(...), pairs=[("id", "t")]

    This node is produced only when the parser is in a relational context
    (inside pi, sigma, join, div, group, ungroup operand positions).  In a
    Z paragraph context the identical surface form ``S[a/b]`` produces
    ``SchemaRename`` instead.

    LaTeX rendering routes through inline math (not a Z environment) because
    fuzz rejects ``R[new/old]`` on a relation value inside Z paragraphs
    (jms ruling Q1, 2026-05-23; fuzz syntax error at ``/``).

    LaTeX output: ``relation[new/old, ...]`` — literal pass-through, no \\mathrm.
    """

    relation: Expr  # Any expression (compound operands allowed)
    pairs: list[tuple[str, str]]  # (new_name, old_name) per Z RM §3.11, at least one


@dataclass(frozen=True)
class NaturalJoin(ASTNode):
    """Natural join or theta-join (join) node.

    Represents R join S (natural join) or R join [p] S (theta-join).

    Examples:
    - R join S -> left=R, right=S, subscript=None
    - R join [R.x = S.y] S -> left=R, right=S, subscript=(R.x = S.y)
    """

    left: Expr
    right: Expr
    subscript: Expr | None  # None for natural join, predicate for theta-join
    line_break_after: bool = False


@dataclass(frozen=True)
class Divide(ASTNode):
    """Relational division (div) node.

    Represents R div S.

    Example:
    - R div S -> left=R, right=S
    """

    left: Expr
    right: Expr
    line_break_after: bool = False


@dataclass(frozen=True)
class Group(ASTNode):
    """Date's GROUP operator — bundle attributes into a nested relation (Phase 4.1).

    Represents ``R group ({A, B, ...} as alias)``.

    Bundles the named attributes of R into a single nested relation-valued
    attribute called alias.

    Examples:
    - R group ({A} as members)
      -> relation=Identifier("R"), attrs=["A"], alias="members"
    - R group ({A, B, C} as nested)
      -> relation=Identifier("R"), attrs=["A", "B", "C"], alias="nested"

    LaTeX rendering:
      R \\mathop{\\mathrm{GROUP}} (\\{A, B\\} \\mathop{\\mathrm{AS}} alias)
    """

    relation: Expr
    attrs: list[str]
    alias: str
    line_break_after: bool = False


@dataclass(frozen=True)
class Ungroup(ASTNode):
    """Date's UNGROUP operator — flatten a nested relation (Phase 4.1).

    Represents ``R ungroup alias``.

    Inverse of GROUP: removes the nested relation-valued attribute alias,
    restoring the original flat structure.

    Examples:
    - R ungroup members
      -> relation=Identifier("R"), alias="members"

    LaTeX rendering:
      R \\mathop{\\mathrm{UNGROUP}} alias
    """

    relation: Expr
    alias: str
    line_break_after: bool = False


@dataclass(frozen=True)
class GroupAggregate(ASTNode):
    """Date's GROUP operator in aggregate form (Phase 4.2).

    Represents ``R Group (Count(x) as total, Sum(y) as grand)``.

    Computes one or more scalar aggregates per partition of R.  Each
    aggregator clause names the aggregation function, the input attribute,
    and the output alias.  Multiple clauses are comma-separated.

    Examples:
    - R Group (Count(x) as total)
      -> relation=Identifier("R"), clauses=[AggregatorClause(COUNT, "x", "total")]
    - R Group (Count(x) as t, Sum(y) as g)
      -> relation=Identifier("R"), clauses=[AggregatorClause(COUNT, "x", "t"),
                                            AggregatorClause(SUM, "y", "g")]

    LaTeX rendering:
      R \\mathrm{Group}(\\mathrm{Count}(x)~\\mathrm{as}~total)
    """

    relation: Expr
    clauses: list[AggregatorClause]
    line_break_after: bool = False


@dataclass(frozen=True)
class Binding(ASTNode):
    r"""Z binding expression (Z RM §3.7).

    Constructs a labelled tuple whose components are name-expression pairs.
    Written ``{| name == expr, ... |}`` in source; rendered as
    ``\lblot name == expr, \ldots \rblot`` in LaTeX.

    Components are comma-separated (Z RM §3.7 uses commas, not semicolons).
    The ``==`` operator is the ABBREV token reused in binding context;
    the parser disambiguates by position (inside ``{| ... |}``, not at
    top-level abbreviation position).

    Examples:
    - {| name == s.name |}
      -> pairs=[("name", TupleProjection(s, "name"))]
    - {| name == s.name, displacement == c.displacement |}
      -> pairs=[("name", ...), ("displacement", ...)]
    - {| |} (empty binding, Z RM permits it)
      -> pairs=[]
    """

    pairs: list[tuple[str, Expr]]


# Type alias for all expression types
Expr = (
    BinaryOp
    | UnaryOp
    | Identifier
    | Number
    | StringLit
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
    | SchemaCompose
    | SchemaPipe
    | SchemaHide
    | SchemaProject
    | SchemaRename
    | Range
    | SequenceLiteral
    | TupleProjection
    | BagLiteral
    | Conditional
    | GuardedBranch
    | GuardedCases
    | Theta
    | SchemaText
    | Restrict
    | Project
    | RelationRename
    | NaturalJoin
    | Divide
    | Group
    | Ungroup
    | GroupAggregate
    | Binding
)


# Document structure nodes


@dataclass(frozen=True)
class TitleMetadata(ASTNode):
    """Document title metadata (title, author, date, etc.)."""

    title: str | None = None
    subtitle: str | None = None
    author: str | None = None
    date: str | None = None
    institution: str | None = None


@dataclass(frozen=True)
class BibliographyMetadata(ASTNode):
    """Bibliography file and style metadata for document."""

    file: str | None = None
    style: str | None = None


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


# Equivalence chain nodes


@dataclass(frozen=True)
class ArgueStep(ASTNode):
    """Single step in an argue chain (equational reasoning).

    Used for both EQUIV: and ARGUE: block syntax (they are aliases).
    """

    expression: Expr
    justification: str | None


@dataclass(frozen=True)
class ArgueChain(ASTNode):
    """Argue chain with multiple reasoning steps (equational reasoning).

    Generated by EQUIV:, ARGUE:, and EQUAL: block syntax.
    connector="iff" (default) joins steps with \\Leftrightarrow (logical equivalence).
    connector="eq" joins steps with = (equality of expressions of the same Z type).
    """

    steps: list[ArgueStep]
    connector: Literal["iff", "eq"] = "iff"


@dataclass(frozen=True)
class InfruleBlock(ASTNode):
    """Inference rule with premises, horizontal line, and conclusion.

    Generated by INFRULE: block syntax. Uses fuzz's infrule environment.
    Format:
      premise1 [label1]
      premise2 [label2]
      ---
      conclusion [label]
    """

    premises: list[tuple[Expr, str | None]]  # (premise, label)
    conclusion: tuple[Expr, str | None]  # (conclusion, label)


# Z notation nodes


@dataclass(frozen=True)
class GivenType(ASTNode):
    """Given type declaration (given A, B, C)."""

    names: list[str]


@dataclass(frozen=True)
class FreeBranch(ASTNode):
    """A single branch in a free type definition.

    Represents constructor branches that may have parameters.

    Examples:
    - stalk (no parameters) -> name="stalk", parameters=None
    - leaf⟨N⟩ (single parameter) -> name="leaf", parameters=Identifier("N")
    - branch⟨Tree x Tree⟩ (multiple parameters) -> name="branch",
      parameters=BinaryOp("cross", Tree, Tree)
    """

    name: str  # Constructor name (e.g., "leaf", "branch", "stalk")
    parameters: (
        Expr | None
    )  # None for simple branches, Expr for parameterized constructors


@dataclass(frozen=True)
class FreeType(ASTNode):
    """Free type definition (Type ::= branch1 | branch2).

    Supports recursive constructors with parameters.

    Examples:
    - Status ::= active | inactive (simple)
      -> branches=[FreeBranch("active", None), ...]
    - Tree ::= stalk | leaf⟨N⟩ | branch⟨Tree x Tree⟩ (recursive)
      -> branches=[FreeBranch("stalk", None), FreeBranch("leaf", N), ...]
    """

    name: str
    branches: list[FreeBranch]  # List of constructor branches


@dataclass(frozen=True)
class SyntaxDefinition(ASTNode):
    """Single free type definition within syntax environment.

    Represents: TypeName ::= branch1 | branch2 | ...
    Can span multiple lines with continuation branches.

    Example:
    - EXP ::= const<N> | binop<OP cross EXP cross EXP>
      -> name="EXP", branches=[FreeBranch("const", N), ...]
    """

    name: str  # Type name (e.g., "EXP", "OP")
    branches: list[FreeBranch]  # List of constructor branches


@dataclass(frozen=True)
class SyntaxBlock(ASTNode):
    """Syntax environment for aligned free type definitions.

    Generates \\begin{syntax}...\\end{syntax} with column alignment.
    Groups of definitions separated by blank lines generate \\also.

    Example:
      syntax
        OP ::= plus | minus

        EXP ::= const<N>
             |  binop<OP cross EXP>
      end

    Generated LaTeX:
      \\begin{syntax}
      OP & ::= & plus | minus
      \\also
      EXP & ::= & const \\ldata \\nat \\rdata \\\\
      & | & binop \\ldata OP \\cross EXP \\rdata
      \\end{syntax}
    """

    groups: list[list[SyntaxDefinition]]  # Groups separated by blank lines


@dataclass(frozen=True)
class Abbreviation(ASTNode):
    """Abbreviation definition (name == expression).

    Supports generic parameters [X, Y, ...].
    Example: [X] Pairs == X x X
    """

    name: str
    expression: Expr
    generic_params: list[str] | None = None  # Optional generic parameters


@dataclass(frozen=True)
class Declaration(ASTNode):
    """Declaration in axdef or schema (var : Type).

    When ``is_primary_key`` is True the generator emits a PK annotation
    line below the schema box, marking the attribute as a primary key.
    """

    variable: str
    type_expr: Expr
    is_primary_key: bool = False


@dataclass(frozen=True)
class SchemaInclusion(ASTNode):
    """Schema inclusion in axdef, schema, or gendef declaration list.

    Represents three forms per Z RM §3.7 and §5.2:
    - bare:  ``Counter``           → decoration=None
    - delta: ``Delta Airline``     → decoration="delta"
    - xi:    ``Xi Card``           → decoration="xi"

    The ``name`` field carries any Phase-0 decoration suffix already baked
    in by the lexer (e.g., ``"Counter'"`` for a primed schema reference).
    Generic instantiation parameters (e.g., ``Delta Stack[Int]``) are held
    in ``generics`` as a list of type expressions; None for the common
    unparameterised case.
    """

    name: str
    decoration: str | None  # None | "delta" | "xi"
    generics: list[Expr] | None = None


@dataclass(frozen=True)
class AxDef(ASTNode):
    """Axiomatic definition block.

    Supports generic parameters [X, Y, ...].
    ZED2E alignment: predicates grouped by blank lines for \also generation.

    Example:
    axdef [X]
      f : X -> X
    where
      forall x : X | f(x) = x
    end
    """

    declarations: list[Declaration | SchemaInclusion]
    predicates: list[list[Expr]]  # Groups of predicates (separated by blank lines)
    generic_params: list[str] | None = None  # Optional generic parameters


@dataclass(frozen=True)
class GenDef(ASTNode):
    """Generic definition block.

    Generic definitions define polymorphic functions and constants.
    Generic parameters are required (not optional like in AxDef).
    ZED2E alignment: predicates grouped by blank lines for \also generation.

    Example:
    gendef [X, Y]
      fst : X cross Y -> X
    where
      forall x : X; y : Y @ fst(x, y) = x
    end
    """

    generic_params: list[str]  # Required generic parameters
    declarations: list[Declaration | SchemaInclusion]
    predicates: list[list[Expr]]  # Groups of predicates (separated by blank lines)


@dataclass(frozen=True)
class Schema(ASTNode):
    """Schema definition block.

    Supports generic parameters [X, Y, ...] and anonymous schemas (name=None).
    ZED2E alignment: predicates grouped by blank lines for \also generation.

    Examples:
    - schema GenericStack[X] ... end (named with generics)
    - schema State ... end (named)
    - schema ... end (anonymous)
    """

    name: str | None  # Optional name (None for anonymous schemas)
    declarations: list[Declaration | SchemaInclusion]
    predicates: list[list[Expr]]  # Groups of predicates (separated by blank lines)
    generic_params: list[str] | None = None  # Optional generic parameters


@dataclass(frozen=True)
class HorizDef(ASTNode):
    r"""Horizontal schema definition (Z RM §3.8).

    ``Name [generics]? defs RHS`` renders as
    ``\begin{zed} Name \defs RHS \end{zed}``.

    The RHS is either:
    - A schema reference: an Identifier (possibly decorated, possibly with
      generic instantiation).  Example: ``OpAlias defs Delta Counter``.
    - An inline schema text: ``SchemaText`` node produced by ``[ decls | preds ]``.
      Example: ``NatPair defs [ x, y : N | x < y ]``.

    Examples:
    - OpAlias defs Delta Counter
      -> name="OpAlias", generics=None, body=SchemaInclusion("Counter", "delta")
    - Stack[X] defs [s : seq X | true]
      -> name="Stack", generics=["X"], body=SchemaText(...)
    """

    name: str  # LHS schema name
    generics: list[str] | None  # Optional generic parameter names
    # RHS: Identifier, GenericInstantiation, SchemaInclusion, or SchemaText.
    # SchemaInclusion covers Delta/Xi decorated references (Z RM §3.8 examples).
    body: Expr | SchemaInclusion


# Proof tree nodes


@dataclass(frozen=True)
class CaseAnalysis(ASTNode):
    """Case analysis branch (case q: ... case r: ...)."""

    case_name: str  # "q", etc.
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


# Text paragraph node


@dataclass(frozen=True)
class Paragraph(ASTNode):
    """Plain text paragraph with formula detection.

    Text content that gets processed for inline math, operators, etc.
    """

    text: str  # The paragraph content


@dataclass(frozen=True)
class PureParagraph(ASTNode):
    """Pure text paragraph with NO processing.

    Raw text content with no formula detection, no operator conversion.
    Only basic LaTeX character escaping is applied.
    """

    text: str  # The raw paragraph content


@dataclass(frozen=True)
class LatexBlock(ASTNode):
    """Raw LaTeX passthrough block.

    LaTeX code passed directly to output with NO escaping.
    Use for custom LaTeX commands, environments, or formatting.
    """

    latex: str  # The raw LaTeX content


@dataclass(frozen=True)
class BMachine(ASTNode):
    """B-machine verbatim block (B: ... END).

    Body text is passed verbatim inside a LaTeX verbatim environment.
    The body includes the terminating END line; indentation is preserved.
    """

    body: str  # Raw multi-line body including the final END line


@dataclass(frozen=True)
class RawLatexBlock(ASTNode):
    """Multi-line raw LaTeX passthrough block (LATEX:\\n...END).

    Body lines are slurped verbatim until a column-0 END terminator.
    Indentation and internal blank lines are preserved exactly.
    The body is emitted directly to .tex output with NO escaping and
    NO wrapping — the user owns the raw LaTeX.
    """

    body: str  # Raw multi-line body (excluding the final END line)


@dataclass(frozen=True)
class PageBreak(ASTNode):
    """Page break in document.

    Inserts a page break in the PDF output.
    """


@dataclass(frozen=True)
class LineBreak(ASTNode):
    """Vertical line break (\\medskip) in document.

    Inserts a medium vertical skip between paragraphs in the PDF output.
    Useful for separating logical groups of related content (e.g., a schema
    and its auto-emitted PK/FK predicates from the next schema).
    """


@dataclass(frozen=True)
class Contents(ASTNode):
    """Table of contents directive.

    Generates \tableofcontents with optional depth control.
    depth: "full" or "2" for sections + subsections, empty for sections only.
    """

    depth: str = ""  # Empty = sections only, "full" or "2" = sections + subsections


@dataclass(frozen=True)
class PartsFormat(ASTNode):
    """Parts formatting style directive.

    Controls how parts are rendered: "inline" or "subsection".
    """

    style: str = "subsection"  # "inline" or "subsection"


@dataclass(frozen=True)
class Zed(ASTNode):
    """Zed block for standalone predicates and declarations.

    Unboxed Z notation paragraphs for:
    - Standalone predicates (e.g., global constraints)
    - Basic type declarations
    - Abbreviations
    - Free type definitions

    Generates: \\begin{zed}...\\end{zed}

    Note: content can be an Expr (single expression) or Document (multiple items).
    The parser creates Document when the zed block contains multiple declarations.
    """

    content: Expr | Document  # Single expression or multiple items


# Type alias for document items (expressions or structural elements)
DocumentItem = (
    Expr
    | Section
    | Solution
    | Part
    | Paragraph
    | PureParagraph
    | LatexBlock
    | BMachine
    | RawLatexBlock
    | PageBreak
    | LineBreak
    | Contents
    | PartsFormat
    | TruthTable
    | ArgueChain  # Renamed from EquivChain (EQUIV: and ARGUE: both use this)
    | InfruleBlock
    | GivenType
    | FreeType
    | SyntaxBlock
    | Abbreviation
    | AxDef
    | GenDef
    | Schema
    | HorizDef
    | Zed
    | ProofTree
)


@dataclass(frozen=True)
class Document(ASTNode):
    """Document containing multiple expressions or blocks."""

    items: list[DocumentItem]
    title_metadata: TitleMetadata | None = None
    parts_format: str = "subsection"  # "inline" or "subsection"
    bibliography_metadata: BibliographyMetadata | None = None


# Backwards-compatible aliases (EQUIV was renamed to ARGUE for clarity)
# EQUIV: and ARGUE: both map to ArgueChain internally
EquivStep = ArgueStep
EquivChain = ArgueChain
