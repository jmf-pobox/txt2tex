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

    # Set operators (Phase 3, enhanced in Phase 7)
    IN = auto()
    NOTIN = auto()  # not in (set non-membership)
    SUBSET = auto()
    UNION = auto()
    INTERSECT = auto()

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
    STAR = auto()  # * (reflexive-transitive closure postfix / arithmetic)
    LIMG = auto()  # (| (relational image left)
    RIMG = auto()  # |) (relational image right)

    # Relation functions (Phase 10)
    DOM = auto()  # dom (domain of relation)
    RAN = auto()  # ran (range of relation)
    INV = auto()  # inv (inverse of relation)
    ID = auto()  # id (identity relation)

    # Comparison operators (Phase 3, enhanced in Phase 7)
    LESS_THAN = auto()  # <
    GREATER_THAN = auto()  # >
    LESS_EQUAL = auto()  # <=
    GREATER_EQUAL = auto()  # >=
    EQUALS = auto()  # =
    NOT_EQUAL = auto()  # != or ≠

    # Z notation operators (Phase 4)
    FREE_TYPE = auto()  # ::=
    ABBREV = auto()  # ==

    # Math operators (Phase 3)
    CARET = auto()  # ^ for superscripts
    UNDERSCORE = auto()  # _ for subscripts

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

    # Identifiers and literals
    IDENTIFIER = auto()
    NUMBER = auto()

    # Document structure (Phase 1)
    SECTION_MARKER = auto()  # ===
    SOLUTION_MARKER = auto()  # **
    PART_LABEL = auto()  # (a), (b), (c), etc.
    TRUTH_TABLE = auto()  # TRUTH TABLE:
    TEXT = auto()  # TEXT: (plain text paragraphs)

    # Environments (Phase 2)
    EQUIV = auto()  # EQUIV:

    # Z notation keywords (Phase 4)
    GIVEN = auto()  # given
    AXDEF = auto()  # axdef
    SCHEMA = auto()  # schema
    WHERE = auto()  # where
    END = auto()  # end

    # Proof trees (Phase 5)
    PROOF = auto()  # PROOF:
    DOUBLE_COLON = auto()  # :: (sibling marker in Path C)
    INDENT = auto()  # Indentation level (significant whitespace)

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
