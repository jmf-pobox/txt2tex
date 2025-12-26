"""AST node definitions for txt2tex parser."""

from __future__ import annotations

from dataclasses import dataclass


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


# Quantifier expression nodes


@dataclass(frozen=True)
class Quantifier(ASTNode):
    """Quantifier node (forall, exists, exists1, mu).

    Supports:
        - Multiple variables with shared domain
        - Mu-operator (definite description)
        - Mu with expression part (mu x : X | P . E)
        - Tuple patterns for destructuring
        - Bullet separator for all quantifiers

    Examples:
    - forall x : N | pred  -> variables=["x"], domain=N, body=pred
    - forall x : N | constraint . body -> body=constraint, expression=body
    - forall x, y : N | pred -> variables=["x", "y"], domain=N, body=pred
    - forall (x, y) : T | pred -> variables=["x", "y"], tuple_pattern
    - exists x : N | constraint . body -> body=constraint, expression=body
    - exists1 x : N | pred -> quantifier="exists1", variables=["x"]
    - mu x : N | pred -> quantifier="mu", body=pred, expression=None
    - mu x : N | pred . expr -> quantifier="mu", body=pred, expression=expr

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
    | Range
    | SequenceLiteral
    | TupleProjection
    | BagLiteral
    | Conditional
    | GuardedBranch
    | GuardedCases
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

    Generated by both EQUIV: and ARGUE: block syntax (backwards compatible).
    Uses fuzz's argue environment for better page breaking and line width handling.
    """

    steps: list[ArgueStep]


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
    """Declaration in axdef or schema (var : Type)."""

    variable: str
    type_expr: Expr


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

    declarations: list[Declaration]
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
    declarations: list[Declaration]
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
    declarations: list[Declaration]
    predicates: list[list[Expr]]  # Groups of predicates (separated by blank lines)
    generic_params: list[str] | None = None  # Optional generic parameters


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
class PageBreak(ASTNode):
    """Page break in document.

    Inserts a page break in the PDF output.
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
    | PageBreak
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
