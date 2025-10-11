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
    """
    Tokenizes input text for Phase 0 + Phase 1 + Phase 2.

    Supports propositional logic with document structure and equivalence chains.
    """

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
            return None  # Skip whitespace

        # Newline (significant in Phase 1 for multi-line documents)
        if char == "\n":
            self._advance()
            return Token(TokenType.NEWLINE, "\n", start_line, start_column)

        # Section marker: ===
        if char == "=" and self._peek_char() == "=" and self._peek_char(2) == "=":
            self._advance()
            self._advance()
            self._advance()
            return Token(TokenType.SECTION_MARKER, "===", start_line, start_column)

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

        # Solution marker: **
        if char == "*" and self._peek_char() == "*":
            self._advance()
            self._advance()
            return Token(TokenType.SOLUTION_MARKER, "**", start_line, start_column)

        # Part label: (a), (b), (c), etc. - restrict to a-j for homework parts
        next_char = self._peek_char()
        if char == "(" and "a" <= next_char <= "j" and self._peek_char(2) == ")":
            self._advance()  # consume '('
            label = self._advance()  # consume letter
            self._advance()  # consume ')'
            return Token(TokenType.PART_LABEL, f"({label})", start_line, start_column)

        # Parentheses
        if char == "(":
            self._advance()
            return Token(TokenType.LPAREN, "(", start_line, start_column)

        if char == ")":
            self._advance()
            return Token(TokenType.RPAREN, ")", start_line, start_column)

        # Brackets (for justifications in Phase 2)
        if char == "[":
            self._advance()
            return Token(TokenType.LBRACKET, "[", start_line, start_column)

        if char == "]":
            self._advance()
            return Token(TokenType.RBRACKET, "]", start_line, start_column)

        # Pipe (for truth tables)
        if char == "|":
            self._advance()
            return Token(TokenType.PIPE, "|", start_line, start_column)

        # Identifiers and keywords
        if char.isalpha():
            return self._scan_identifier(start_line, start_column)

        # Numbers
        if char.isdigit():
            return self._scan_number(start_line, start_column)

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

        # Check for multi-word keyword: TRUTH TABLE:
        if value == "TRUTH" and self._current_char() == " ":
            saved_pos = self.pos
            saved_line = self.line
            saved_column = self.column

            self._advance()  # skip space
            # Skip additional spaces
            while self._current_char() == " ":
                self._advance()

            # Check for "TABLE:"
            if (
                self._current_char() == "T"
                and self._peek_char() == "A"
                and self._peek_char(2) == "B"
                and self._peek_char(3) == "L"
                and self._peek_char(4) == "E"
                and self._peek_char(5) == ":"
            ):
                # Consume "TABLE:"
                for _ in range(6):
                    self._advance()
                return Token(
                    TokenType.TRUTH_TABLE, "TRUTH TABLE:", start_line, start_column
                )
            # Not "TABLE:", restore position
            self.pos = saved_pos
            self.line = saved_line
            self.column = saved_column

        # Check for EQUIV: keyword
        if value == "EQUIV" and self._current_char() == ":":
            self._advance()  # Consume ':'
            return Token(TokenType.EQUIV, "EQUIV:", start_line, start_column)

        # Check for keywords
        if value == "and":
            return Token(TokenType.AND, value, start_line, start_column)
        if value == "or":
            return Token(TokenType.OR, value, start_line, start_column)
        if value == "not":
            return Token(TokenType.NOT, value, start_line, start_column)

        # Regular identifier
        return Token(TokenType.IDENTIFIER, value, start_line, start_column)

    def _scan_number(self, start_line: int, start_column: int) -> Token:
        """Scan number."""
        start_pos = self.pos
        while not self._at_end() and self._current_char().isdigit():
            self._advance()

        value = self.text[start_pos : self.pos]
        return Token(TokenType.NUMBER, value, start_line, start_column)
