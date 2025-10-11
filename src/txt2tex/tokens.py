"""Token types and definitions for txt2tex lexer."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto


class TokenType(Enum):
    """Token types for Phase 0: Simple propositional logic."""

    # Operators (propositional logic)
    AND = auto()
    OR = auto()
    NOT = auto()
    IMPLIES = auto()
    IFF = auto()

    # Grouping
    LPAREN = auto()
    RPAREN = auto()

    # Identifiers and literals
    IDENTIFIER = auto()

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
