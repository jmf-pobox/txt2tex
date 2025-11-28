"""Token types and definitions for txt2tex lexer."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto


class TokenType(Enum):
    """Token types for txt2tex lexer (Phases 0-4)."""

    # Operators (propositional logic)
    AND = auto()
    OR = auto()
    NOT = auto()
    IMPLIES = auto()
    IFF = auto()

    # Quantifiers (Phase 3, enhanced in Phase 6-7)
    FORALL = auto()
    EXISTS = auto()
    EXISTS1 = auto()  # Unique existence quantifier
    MU = auto()  # Definite description (mu-operator)
    LAMBDA = auto()  # Lambda expression (Phase 11d)

    # Set operators (Phase 3, enhanced in Phase 7-8, Phase 11.5, Phase 39)
    IN = auto()
    NOTIN = auto()  # not in (set non-membership)
    SUBSET = auto()
    PSUBSET = auto()  # psubset or ⊂ (strict/proper subset - Phase 39)
    UNION = auto()
    INTERSECT = auto()
    CROSS = auto()  # cross or × (Cartesian product)  # noqa: RUF003
    SETMINUS = auto()  # \ (set difference)
    HASH = auto()  # # (cardinality - prefix operator)

    # Relation operators (Phase 10)
    RELATION = auto()  # <-> (relation type)
    MAPLET = auto()  # |-> (maplet constructor)
    DRES = auto()  # <| (domain restriction)
    RRES = auto()  # |> (range restriction)
    NDRES = auto()  # <<| (domain subtraction)
    NRRES = auto()  # |>> (range subtraction)
    COMP = auto()  # comp or ; (relational composition)
    SEMICOLON = auto()  # ; (relational composition)
    CIRC = auto()  # o9 (forward/backward composition)
    TILDE = auto()  # ~ (relational inverse postfix)
    PLUS = auto()  # + (transitive closure postfix / arithmetic)
    MINUS = auto()  # - (subtraction / negation)
    STAR = auto()  # * (reflexive-transitive closure postfix / arithmetic)
    LIMG = auto()  # (| (relational image left)
    RIMG = auto()  # |) (relational image right)
    SHOWS = auto()  # shows (sequent judgment operator ⊢)

    # Relation functions (Phase 10)
    DOM = auto()  # dom (domain of relation)
    RAN = auto()  # ran (range of relation)
    INV = auto()  # inv (inverse of relation)
    ID = auto()  # id (identity relation)

    # Set functions (Phase 11.5, enhanced Phase 19, Phase 20)
    POWER = auto()  # P (power set)
    POWER1 = auto()  # P1 (non-empty power set)
    FINSET = auto()  # F (finite set)
    FINSET1 = auto()  # F1 (non-empty finite set)
    BIGCUP = auto()  # bigcup (distributed union)
    BIGCAP = auto()  # bigcap (distributed intersection)

    # Sequence operators (Phase 12, enhanced Phase 35)
    LANGLE = auto()  # ⟨ (sequence literal left)
    RANGLE = auto()  # ⟩ (sequence literal right)
    SEQ = auto()  # seq (sequence type)
    SEQ1 = auto()  # seq1 (non-empty sequence type)
    CAT = auto()  # ⌢ (sequence concatenation)
    FILTER = auto()  # ↾ (sequence filter - Phase 35)
    LBAG = auto()  # [[ (bag literal left)
    RBAG = auto()  # ]] (bag literal right)
    BAG_UNION = auto()  # ⊎ (bag union)
    OVERRIDE = auto()  # ++ (function/sequence override) - Phase 13

    # Function type operators (Phase 11, enhanced Phase 18)
    TFUN = auto()  # -> (total function)
    PFUN = auto()  # +-> (partial function)
    TINJ = auto()  # >-> (total injection)
    PINJ = auto()  # >+> (partial injection)
    PINJ_ALT = auto()  # -|> (partial injection, alternative notation)
    TSURJ = auto()  # -->> (total surjection)
    PSURJ = auto()  # +->> (partial surjection)
    BIJECTION = auto()  # >->> (bijection)
    FINFUN = auto()  # 77-> (finite partial function)

    # Comparison operators (Phase 3, enhanced in Phase 7)
    LESS_THAN = auto()  # <
    GREATER_THAN = auto()  # >
    LESS_EQUAL = auto()  # <=
    GREATER_EQUAL = auto()  # >=
    EQUALS = auto()  # =
    NOT_EQUAL = auto()  # != or ≠

    # Range operator (Phase 13)
    RANGE = auto()  # .. (e.g., 1..10, 1993..current)

    # Z notation operators (Phase 4)
    FREE_TYPE = auto()  # ::=
    ABBREV = auto()  # ==

    # Math operators (Phase 3)
    CARET = auto()  # ^ for superscripts
    UNDERSCORE = auto()  # _ for subscripts
    MOD = auto()  # mod (modulo arithmetic)
    CONTINUATION = auto()  # \ at end of line (Phase 27 - line break marker)

    # Grouping
    LPAREN = auto()
    RPAREN = auto()
    LBRACKET = auto()
    RBRACKET = auto()
    LBRACE = auto()  # { for grouping subscripts/superscripts
    RBRACE = auto()  # }

    # Delimiters
    COLON = auto()  # : for quantifiers (forall x : N)
    PIPE = auto()  # | for quantifiers and table columns
    COMMA = auto()  # , for multi-variable quantifiers (forall x, y : N)
    PERIOD = auto()  # . for sentences in paragraphs
    DERIVE = auto()  # --- (horizontal line separator in INFRULE)

    # Identifiers and literals
    IDENTIFIER = auto()
    NUMBER = auto()

    # Document structure (Phase 1)
    SECTION_MARKER = auto()  # ===
    SOLUTION_MARKER = auto()  # **
    PART_LABEL = auto()  # (a), (b), (c), etc.
    TRUTH_TABLE = auto()  # TRUTH TABLE:
    TEXT = auto()  # TEXT: (plain text paragraphs with formula detection)
    PURETEXT = auto()  # PURETEXT: (raw text, no processing)
    LATEX = auto()  # LATEX: (raw LaTeX passthrough, no escaping)
    PAGEBREAK = auto()  # PAGEBREAK: (insert page break)
    CONTENTS = auto()  # CONTENTS: (table of contents)
    PARTS = auto()  # PARTS: (parts formatting style)
    BIBLIOGRAPHY = auto()  # BIBLIOGRAPHY: (bibliography file)
    BIBLIOGRAPHY_STYLE = auto()  # BIBLIOGRAPHY_STYLE: (bibliography style)
    # Title metadata
    TITLE = auto()  # TITLE: (document title)
    SUBTITLE = auto()  # SUBTITLE: (document subtitle)
    AUTHOR = auto()  # AUTHOR: (document author)
    DATE = auto()  # DATE: (document date)
    INSTITUTION = auto()  # INSTITUTION: (institution name)

    # Environments (Phase 2)
    ARGUE = auto()  # ARGUE: or EQUIV: (both map to argue environment)
    INFRULE = auto()  # INFRULE: (inference rule with horizontal line)

    # Z notation keywords (Phase 4)
    GIVEN = auto()  # given
    AXDEF = auto()  # axdef
    SCHEMA = auto()  # schema
    GENDEF = auto()  # gendef (generic definition)
    ZED = auto()  # zed (unboxed paragraph block)
    SYNTAX = auto()  # syntax (aligned free type definitions)
    WHERE = auto()  # where
    END = auto()  # end

    # Conditional expressions (Phase 16)
    IF = auto()  # if
    THEN = auto()  # then
    ELSE = auto()  # else
    OTHERWISE = auto()  # otherwise

    # Proof trees (Phase 5, enhanced Phase 2.2)
    PROOF = auto()  # PROOF:
    DOUBLE_COLON = auto()  # :: (sibling marker in Path C)
    INDENT = auto()  # Indentation level (significant whitespace)
    ELLIPSIS = auto()  # ... (steps omitted in proof)

    # Whitespace and structure
    WHITESPACE = auto()
    NEWLINE = auto()

    # Special
    EOF = auto()


@dataclass(frozen=True)
class Token:
    """A lexical token with type, value, and position."""

    type: TokenType
    value: str
    line: int
    column: int

    def __repr__(self) -> str:
        """Return string representation for debugging."""
        return f"Token({self.type.name}, {self.value!r}, {self.line}:{self.column})"
