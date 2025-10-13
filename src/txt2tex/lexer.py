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
    Tokenizes input text for Phase 0-4 + Phase 10a-b.

    Supports propositional logic, document structure, equivalence chains,
    predicate logic with quantifiers and mathematical notation, Z notation,
    and relational operators (Phase 10a: <->, |->, <|, |>, comp, ;, dom, ran)
    and extended operators (Phase 10b: <<|, |>>, o9, ~, +, *, inv, id).
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

        # Relation type operator: <-> (Phase 10)
        if char == "<" and self._peek_char() == "-" and self._peek_char(2) == ">":
            self._advance()
            self._advance()
            self._advance()
            return Token(TokenType.RELATION, "<->", start_line, start_column)

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

        # Braces (for grouping subscripts/superscripts in Phase 3)
        if char == "{":
            self._advance()
            return Token(TokenType.LBRACE, "{", start_line, start_column)

        if char == "}":
            self._advance()
            return Token(TokenType.RBRACE, "}", start_line, start_column)

        # Maplet operator: |-> (Phase 10a) - check before | alone
        if char == "|" and self._peek_char() == "-" and self._peek_char(2) == ">":
            self._advance()
            self._advance()
            self._advance()
            return Token(TokenType.MAPLET, "|->", start_line, start_column)

        # Range subtraction operator: |>> (Phase 10b) - check before |> and | alone
        if char == "|" and self._peek_char() == ">" and self._peek_char(2) == ">":
            self._advance()
            self._advance()
            self._advance()
            return Token(TokenType.NRRES, "|>>", start_line, start_column)

        # Range restriction operator: |> (Phase 10a) - check before | alone
        if char == "|" and self._peek_char() == ">":
            self._advance()
            self._advance()
            return Token(TokenType.RRES, "|>", start_line, start_column)

        # Pipe (for truth tables and quantifiers)
        if char == "|":
            self._advance()
            return Token(TokenType.PIPE, "|", start_line, start_column)

        # Comma (for multi-variable quantifiers in Phase 6)
        if char == ",":
            self._advance()
            return Token(TokenType.COMMA, ",", start_line, start_column)

        # Period (for sentences in paragraphs)
        if char == ".":
            self._advance()
            return Token(TokenType.PERIOD, ".", start_line, start_column)

        # Free type operator ::= (Phase 4) - check before :: and :
        if char == ":" and self._peek_char() == ":" and self._peek_char(2) == "=":
            self._advance()
            self._advance()
            self._advance()
            return Token(TokenType.FREE_TYPE, "::=", start_line, start_column)

        # Double colon :: (Phase 5 - sibling marker) - check before : alone
        if char == ":" and self._peek_char() == ":":
            self._advance()
            self._advance()
            return Token(TokenType.DOUBLE_COLON, "::", start_line, start_column)

        # Colon (for quantifiers in Phase 3)
        if char == ":":
            self._advance()
            return Token(TokenType.COLON, ":", start_line, start_column)

        # Semicolon (for relational composition in Phase 10a)
        if char == ";":
            self._advance()
            return Token(TokenType.SEMICOLON, ";", start_line, start_column)

        # Comparison operators (Phase 3)
        # Check <= and >= before < and >
        # But watch out for <=> and <-> which are handled earlier
        # Domain subtraction operator: <<| (Phase 10b) - check before <| and < alone
        if char == "<" and self._peek_char() == "<" and self._peek_char(2) == "|":
            self._advance()
            self._advance()
            self._advance()
            return Token(TokenType.NDRES, "<<|", start_line, start_column)

        # Domain restriction operator: <| (Phase 10a) - check before < alone
        if char == "<" and self._peek_char() == "|":
            self._advance()
            self._advance()
            return Token(TokenType.DRES, "<|", start_line, start_column)

        if char == "<" and self._peek_char() == "=" and self._peek_char(2) != ">":
            self._advance()
            self._advance()
            return Token(TokenType.LESS_EQUAL, "<=", start_line, start_column)

        if char == "<":
            self._advance()
            return Token(TokenType.LESS_THAN, "<", start_line, start_column)

        if char == ">" and self._peek_char() == "=":
            self._advance()
            self._advance()
            return Token(TokenType.GREATER_EQUAL, ">=", start_line, start_column)

        if char == ">":
            self._advance()
            return Token(TokenType.GREATER_THAN, ">", start_line, start_column)

        # Not equal != (Phase 7) - check before other operators
        if char == "!" and self._peek_char() == "=":
            self._advance()
            self._advance()
            return Token(TokenType.NOT_EQUAL, "!=", start_line, start_column)

        # Abbreviation operator == (Phase 4) - check before = alone
        # Already checked for === and => earlier
        if char == "=" and self._peek_char() == "=":
            self._advance()
            self._advance()
            return Token(TokenType.ABBREV, "==", start_line, start_column)

        # Equals (Phase 3) - but not =>, ==, or === which are handled earlier
        if char == "=":
            self._advance()
            return Token(TokenType.EQUALS, "=", start_line, start_column)

        # Math operators (Phase 3)
        if char == "^":
            self._advance()
            return Token(TokenType.CARET, "^", start_line, start_column)

        if char == "_":
            self._advance()
            return Token(TokenType.UNDERSCORE, "_", start_line, start_column)

        # Postfix relation operators (Phase 10b)
        if char == "~":
            self._advance()
            return Token(TokenType.TILDE, "~", start_line, start_column)

        if char == "+":
            self._advance()
            return Token(TokenType.PLUS, "+", start_line, start_column)

        # Note: * is used for both SOLUTION_MARKER (**) and STAR (*)
        # ** is checked earlier, so single * is safe here
        if char == "*":
            self._advance()
            return Token(TokenType.STAR, "*", start_line, start_column)

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

        # Check for special o9 operator (Phase 10b) - composition
        if self._current_char() == "o" and self._peek_char() == "9":
            self._advance()  # consume 'o'
            self._advance()  # consume '9'
            return Token(TokenType.CIRC, "o9", start_line, start_column)

        # Note: Do NOT include underscore in identifiers
        # Underscore is used as subscript operator in Phase 3
        while not self._at_end() and self._current_char().isalnum():
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

        # Check for PROOF: keyword
        if value == "PROOF" and self._current_char() == ":":
            self._advance()  # Consume ':'
            return Token(TokenType.PROOF, "PROOF:", start_line, start_column)

        # Check for TEXT: keyword - capture rest of line as raw text
        if value == "TEXT" and self._current_char() == ":":
            self._advance()  # Consume ':'

            # Skip any whitespace after the colon
            while self._current_char() in " \t":
                self._advance()

            # Capture the rest of the line as raw text (don't tokenize)
            text_start = self.pos
            while not self._at_end() and self._current_char() != "\n":
                self._advance()

            # Extract the raw text content
            text_content = self.text[text_start : self.pos]

            return Token(TokenType.TEXT, text_content, start_line, start_column)

        # Check for keywords (propositional logic)
        if value == "and":
            return Token(TokenType.AND, value, start_line, start_column)
        if value == "or":
            return Token(TokenType.OR, value, start_line, start_column)
        if value == "not":
            return Token(TokenType.NOT, value, start_line, start_column)

        # Check for quantifiers (Phase 3, enhanced in Phase 6-7)
        if value == "forall":
            return Token(TokenType.FORALL, value, start_line, start_column)
        if value == "exists1":
            return Token(TokenType.EXISTS1, value, start_line, start_column)
        if value == "exists":
            return Token(TokenType.EXISTS, value, start_line, start_column)
        if value == "mu":
            return Token(TokenType.MU, value, start_line, start_column)

        # Check for set operators (Phase 3, enhanced in Phase 7)
        if value == "notin":
            return Token(TokenType.NOTIN, value, start_line, start_column)
        if value == "in":
            return Token(TokenType.IN, value, start_line, start_column)
        if value == "subset":
            return Token(TokenType.SUBSET, value, start_line, start_column)
        if value == "union":
            return Token(TokenType.UNION, value, start_line, start_column)
        if value == "intersect":
            return Token(TokenType.INTERSECT, value, start_line, start_column)

        # Check for Z notation keywords (Phase 4)
        if value == "given":
            return Token(TokenType.GIVEN, value, start_line, start_column)
        if value == "axdef":
            return Token(TokenType.AXDEF, value, start_line, start_column)
        if value == "schema":
            return Token(TokenType.SCHEMA, value, start_line, start_column)
        if value == "where":
            return Token(TokenType.WHERE, value, start_line, start_column)
        if value == "end":
            return Token(TokenType.END, value, start_line, start_column)

        # Check for relation functions (Phase 10a)
        if value == "comp":
            return Token(TokenType.COMP, value, start_line, start_column)
        if value == "dom":
            return Token(TokenType.DOM, value, start_line, start_column)
        if value == "ran":
            return Token(TokenType.RAN, value, start_line, start_column)

        # Check for relation functions (Phase 10b)
        if value == "inv":
            return Token(TokenType.INV, value, start_line, start_column)
        if value == "id":
            return Token(TokenType.ID, value, start_line, start_column)

        # Regular identifier
        return Token(TokenType.IDENTIFIER, value, start_line, start_column)

    def _scan_number(self, start_line: int, start_column: int) -> Token:
        """Scan number."""
        start_pos = self.pos
        while not self._at_end() and self._current_char().isdigit():
            self._advance()

        value = self.text[start_pos : self.pos]
        return Token(TokenType.NUMBER, value, start_line, start_column)
