"""Token-cursor helpers for the recursive-descent parser.

Covers: ``_at_end``, ``_current``, ``_advance``, ``_match``,
``_peek_ahead``, ``_skip_newlines``, ``_has_blank_line``,
``_bracket_contains_slash``.  Every rule method in the parser_pkg
reaches the token stream through these helpers.

This mixin is composed into :class:`Parser` via multiple inheritance.
Method bodies are byte-identical to their counterparts in the
pre-refactor monolithic ``parser.py``; only their file location has
changed.
"""

from __future__ import annotations

from txt2tex.parser_pkg._base import ParserBase
from txt2tex.tokens import Token, TokenType


class _LexerStateParser(ParserBase):  # pyright: ignore[reportUnusedClass]
    """Mixin: token-cursor helpers."""

    def _at_end(self) -> bool:
        """Check if we've consumed all tokens."""
        return self._current().type == TokenType.EOF

    def _current(self) -> Token:
        """Return current token without consuming it."""
        return self.tokens[self.pos]

    def _advance(self) -> Token:
        """Consume and return current token."""
        token = self.tokens[self.pos]
        if not self._at_end():
            self.pos += 1
        # Track the end position of this token for whitespace detection
        self.last_token_end_column = token.column + len(token.value)
        self.last_token_line = token.line
        return token

    def _match(self, *types: TokenType) -> bool:
        """Check if current token matches any of the given types."""
        return self._current().type in types

    def _peek_ahead(self, offset: int = 1) -> Token:
        """Look ahead at token without consuming it."""
        pos = self.pos + offset
        if pos < len(self.tokens):
            return self.tokens[pos]
        return self.tokens[-1]  # Return EOF if past end

    def _skip_newlines(self) -> None:
        """Skip all consecutive newline tokens."""
        while self._match(TokenType.NEWLINE) and not self._at_end():
            self._advance()

    def _has_blank_line(self) -> bool:
        """Check if there are multiple consecutive newlines (blank line).

        Returns:
            True if there are 2+ consecutive NEWLINE tokens (indicating blank line)
        """
        if not self._match(TokenType.NEWLINE):
            return False

        # Count consecutive newlines
        newline_count = 0
        offset = 0
        while (
            self.pos + offset < len(self.tokens)
            and self.tokens[self.pos + offset].type == TokenType.NEWLINE
        ):
            newline_count += 1
            offset += 1

        return newline_count >= 2

    def _bracket_contains_slash(self) -> bool:
        """Return True if the next bracket group (starting at '[') contains '/'.

        Scans ahead from the current position (which must point at '[') for a
        SLASH token at bracket depth 0.  Does not consume any tokens.
        """
        depth = 0
        offset = 1  # start scanning past the '['
        while True:
            tok = self._peek_ahead(offset)
            if tok.type == TokenType.LBRACKET:
                depth += 1
            elif tok.type == TokenType.RBRACKET:
                if depth == 0:
                    return False
                depth -= 1
            elif tok.type == TokenType.SLASH and depth == 0:
                return True
            elif tok.type in (TokenType.EOF, TokenType.NEWLINE):
                return False
            offset += 1
