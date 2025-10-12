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

    # Quantifiers (Phase 3, enhanced in Phase 6)
    FORALL = auto()
    EXISTS = auto()
    EXISTS1 = auto()  # Unique existence quantifier

    # Set operators (Phase 3)
    IN = auto()
    SUBSET = auto()
    UNION = auto()
    INTERSECT = auto()

    # Comparison operators (Phase 3)
    LESS_THAN = auto()  # <
    GREATER_THAN = auto()  # >
    LESS_EQUAL = auto()  # <=
    GREATER_EQUAL = auto()  # >=
    EQUALS = auto()  # =

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

    # Identifiers and literals
    IDENTIFIER = auto()
    NUMBER = auto()

    # Document structure (Phase 1)
    SECTION_MARKER = auto()  # ===
    SOLUTION_MARKER = auto()  # **
    PART_LABEL = auto()  # (a), (b), (c), etc.
    TRUTH_TABLE = auto()  # TRUTH TABLE:

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
