"""Lexer for txt2tex - converts text into tokens."""

from __future__ import annotations

from txt2tex.tokens import Token, TokenType


class LexerError(Exception):
    """Raised when lexer encounters invalid input."""

    def __init__(self, message: str, line: int, column: int) -> None:
        """Initialize lexer error with position."""
        super().__init__(f"Line {line}, column {column}: {message}")
        self.line = line
        self.column = column


class Lexer:
    """Tokenizes input text for Phase 0: simple propositional logic."""

    def __init__(self, text: str) -> None:
        """Initialize lexer with input text."""
        self.text = text
        self.pos = 0
        self.line = 1
        self.column = 1

    def tokenize(self) -> list[Token]:
        """Tokenize entire input and return list of tokens."""
        tokens: list[Token] = []
        while not self._at_end():
            token = self._scan_token()
            if token is not None:
                tokens.append(token)
        tokens.append(self._make_token(TokenType.EOF, ""))
        return tokens

    def _at_end(self) -> bool:
        """Check if we've reached end of input."""
        return self.pos >= len(self.text)

    def _current_char(self) -> str:
        """Return current character or empty string if at end."""
        if self._at_end():
            return ""
        return self.text[self.pos]

    def _peek_char(self, offset: int = 1) -> str:
        """Look ahead at character without consuming it."""
        pos = self.pos + offset
        if pos >= len(self.text):
            return ""
        return self.text[pos]

    def _advance(self) -> str:
        """Consume and return current character, updating position."""
        if self._at_end():
            return ""
        char = self.text[self.pos]
        self.pos += 1
        if char == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return char

    def _make_token(self, token_type: TokenType, value: str) -> Token:
        """Create token at current position."""
        return Token(token_type, value, self.line, self.column - len(value))

    def _scan_token(self) -> Token | None:
        """Scan next token from input."""
        start_line = self.line
        start_column = self.column

        char = self._current_char()

        # Whitespace (skip but track)
        if char in " \t":
            self._advance()
            return None  # Skip whitespace in Phase 0

        # Newline
        if char == "\n":
            self._advance()
            return None  # Skip newlines in Phase 0

        # Multi-character operators
        if char == "=" and self._peek_char() == ">":
            self._advance()
            self._advance()
            return Token(TokenType.IMPLIES, "=>", start_line, start_column)

        if char == "<" and self._peek_char() == "=" and self._peek_char(2) == ">":
            self._advance()
            self._advance()
            self._advance()
            return Token(TokenType.IFF, "<=>", start_line, start_column)

        # Parentheses
        if char == "(":
            self._advance()
            return Token(TokenType.LPAREN, "(", start_line, start_column)

        if char == ")":
            self._advance()
            return Token(TokenType.RPAREN, ")", start_line, start_column)

        # Identifiers and keywords
        if char.isalpha():
            return self._scan_identifier(start_line, start_column)

        # Unknown character
        raise LexerError(f"Unexpected character: {char!r}", self.line, self.column)

    def _scan_identifier(self, start_line: int, start_column: int) -> Token:
        """Scan identifier or keyword."""
        start_pos = self.pos
        while not self._at_end() and (
            self._current_char().isalnum() or self._current_char() == "_"
        ):
            self._advance()

        value = self.text[start_pos : self.pos]

        # Check for keywords
        if value == "and":
            return Token(TokenType.AND, value, start_line, start_column)
        if value == "or":
            return Token(TokenType.OR, value, start_line, start_column)
        if value == "not":
            return Token(TokenType.NOT, value, start_line, start_column)

        # Regular identifier
        return Token(TokenType.IDENTIFIER, value, start_line, start_column)
