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
    Tokenizes input text for Phase 0-4 + Phase 10a-b + Phase 11a.

    Supports propositional logic, document structure, equivalence chains,
    predicate logic with quantifiers and mathematical notation, Z notation,
    relational operators (Phase 10a: <->, |->, <|, |>, comp, ;, dom, ran),
    extended operators (Phase 10b: <<|, |>>, o9, ~, +, *, inv, id),
    and function types (Phase 11a: ->, +->, >->, >+>, -->>, +->>, >->>).
    """

    def __init__(self, text: str) -> None:
        """Initialize lexer with input text."""
        self.text = text
        self.pos = 0
        self.line = 1
        self.column = 1
        self._in_solution_marker = False  # Track if inside ** ... **

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
            # Toggle solution marker context (opening or closing **)
            self._in_solution_marker = not self._in_solution_marker
            return Token(TokenType.SOLUTION_MARKER, "**", start_line, start_column)

        # Part label: (a), (b), (c), etc. - restrict to a-j for homework parts
        # Phase 11b: Only match at start of line to avoid function app conflict
        next_char = self._peek_char()
        if (
            char == "("
            and "a" <= next_char <= "j"
            and self._peek_char(2) == ")"
            and start_column == 1
        ):
            self._advance()  # consume '('
            label = self._advance()  # consume letter
            self._advance()  # consume ')'
            return Token(TokenType.PART_LABEL, f"({label})", start_line, start_column)

        # Relational image operators (Phase 11.5): (| and |)
        # Check before simple parentheses
        if char == "(" and self._peek_char() == "|":
            self._advance()
            self._advance()
            return Token(TokenType.LIMG, "(|", start_line, start_column)

        # Parentheses
        if char == "(":
            self._advance()
            return Token(TokenType.LPAREN, "(", start_line, start_column)

        if char == ")":
            self._advance()
            return Token(TokenType.RPAREN, ")", start_line, start_column)

        # Brackets (for justifications in Phase 2)
        # Note: Bag literals [[...]] are handled at parser level, not lexer level
        # to avoid conflicts with nested brackets like Type[List[N]]
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

        # Relational image right bracket: |) (Phase 11.5) - check before | alone
        if char == "|" and self._peek_char() == ")":
            self._advance()
            self._advance()
            return Token(TokenType.RIMG, "|)", start_line, start_column)

        # Pipe (for truth tables and quantifiers)
        if char == "|":
            self._advance()
            return Token(TokenType.PIPE, "|", start_line, start_column)

        # Comma (for multi-variable quantifiers in Phase 6)
        if char == ",":
            self._advance()
            return Token(TokenType.COMMA, ",", start_line, start_column)

        # Range operator .. (Phase 13) - check before period alone
        if char == "." and self._peek_char() == ".":
            self._advance()
            self._advance()
            return Token(TokenType.RANGE, "..", start_line, start_column)

        # Period (for sentences in paragraphs and tuple projection)
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

        # Phase 14: ASCII sequence brackets <> as alternative to Unicode ⟨⟩
        # Recognize < as LANGLE when followed by: >, identifier, digit, (, or <
        # This handles: <>, <x>, <1>, <(expr)>, <<nested>>
        if char == "<":
            next_char = self._peek_char()
            # < followed by > is always empty sequence: <>
            # < followed by letter/digit is sequence literal: <x>, <1>
            # < followed by ( could be sequence with tuple: <(a, b)>
            # < followed by < is nested sequence: <<a>>
            # Otherwise it's comparison: x < y
            if next_char in (">", "(", "<") or next_char.isalnum():
                self._advance()
                return Token(TokenType.LANGLE, "<", start_line, start_column)
            # It's a comparison operator
            self._advance()
            return Token(TokenType.LESS_THAN, "<", start_line, start_column)

        if char == ">" and self._peek_char() == "=":
            self._advance()
            self._advance()
            return Token(TokenType.GREATER_EQUAL, ">=", start_line, start_column)

        # Function type operators starting with > (Phase 11a)
        # Check 4-character first: >->>
        if (
            char == ">"
            and self._peek_char() == "-"
            and self._peek_char(2) == ">"
            and self._peek_char(3) == ">"
        ):
            self._advance()
            self._advance()
            self._advance()
            self._advance()
            return Token(TokenType.BIJECTION, ">->>", start_line, start_column)

        # Check 4-character: >7-> (partial bijection, Phase 33)
        if (
            char == ">"
            and self._peek_char() == "7"
            and self._peek_char(2) == "-"
            and self._peek_char(3) == ">"
        ):
            self._advance()
            self._advance()
            self._advance()
            self._advance()
            return Token(TokenType.PBIJECTION, ">7->", start_line, start_column)

        # Check 3-character: >+>, >->
        if char == ">" and self._peek_char() == "+" and self._peek_char(2) == ">":
            self._advance()
            self._advance()
            self._advance()
            return Token(TokenType.PINJ, ">+>", start_line, start_column)

        if char == ">" and self._peek_char() == "-" and self._peek_char(2) == ">":
            self._advance()
            self._advance()
            self._advance()
            return Token(TokenType.TINJ, ">->", start_line, start_column)

        # Phase 14: ASCII sequence brackets - recognize > as RANGLE
        # Key distinction: <x> has NO space before >, but x > 0 HAS space
        # > is RANGLE if: no space before AND previous char is alphanumeric/</)/ ,
        # > is GREATER_THAN if: space before OR previous char is operator/etc
        if char == ">":
            # Check if there's whitespace immediately before >
            prev_pos = self.pos - 1
            if prev_pos >= 0 and self.text[prev_pos] in " \t":
                # There's whitespace before >, so it's a comparison: x > y
                self._advance()
                return Token(TokenType.GREATER_THAN, ">", start_line, start_column)

            # No whitespace, check what character comes before
            if prev_pos >= 0:
                prev_char = self.text[prev_pos]
                # If previous char suggests we're closing a sequence, this is RANGLE
                # < for <>, alphanumeric for <x>, ) for <(a)>, , for <a, b>
                if prev_char.isalnum() or prev_char in ("<", ">", ")", ","):
                    self._advance()
                    return Token(TokenType.RANGLE, ">", start_line, start_column)

            # Otherwise it's a comparison operator
            self._advance()
            return Token(TokenType.GREATER_THAN, ">", start_line, start_column)

        # Not equal != (Phase 7) - check before other operators
        if char == "!" and self._peek_char() == "=":
            self._advance()
            self._advance()
            return Token(TokenType.NOT_EQUAL, "!=", start_line, start_column)

        # Not equal /= (Z notation slash negation - Phase 16+)
        if char == "/" and self._peek_char() == "=":
            self._advance()
            self._advance()
            return Token(TokenType.NOT_EQUAL, "/=", start_line, start_column)

        # Not in /in (Z notation slash negation - Phase 16+)
        # Check for /in followed by non-alphanumeric (not part of identifier)
        if (
            char == "/"
            and self._peek_char() == "i"
            and self._peek_char(2) == "n"
            and not self._peek_char(3).isalnum()
            and self._peek_char(3) != "_"
        ):
            self._advance()
            self._advance()
            self._advance()
            return Token(TokenType.NOTIN, "/in", start_line, start_column)

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

        # Math operators (Phase 3, enhanced Phase 14, Phase 24)
        # Caret: ^ can mean superscript OR sequence concatenation
        # Phase 24: Whitespace-sensitive disambiguation
        # - Space/tab/newline before ^ → concatenation (CAT)
        # - No space before ^ → exponentiation (CARET)
        # - Special case: >^< → error (missing required space)
        if char == "^":
            # Check if there's whitespace immediately before ^
            has_space_before = self.pos > 0 and self.text[self.pos - 1] in " \t\n"

            # Special case: >^< pattern (sequence concat without space)
            # This is a common mistake - provide helpful error message
            if (
                self.pos > 0
                and self.text[self.pos - 1] == ">"
                and self.pos + 1 < len(self.text)
                and self.text[self.pos + 1] == "<"
            ):
                raise LexerError(
                    "Sequence concatenation requires space: use '> ^ <' not '>^<'",
                    line=start_line,
                    column=start_column,
                )

            # Space before ^ → concatenation
            if has_space_before:
                self._advance()
                return Token(TokenType.CAT, "^", start_line, start_column)

            # No space → exponentiation
            self._advance()
            return Token(TokenType.CARET, "^", start_line, start_column)

        # Cardinality operator (Phase 8)
        if char == "#":
            self._advance()
            return Token(TokenType.HASH, "#", start_line, start_column)

        # Postfix relation operators (Phase 10b)
        if char == "~":
            self._advance()
            return Token(TokenType.TILDE, "~", start_line, start_column)

        # Function type operators starting with + (Phase 11a)
        # Check 4-character first: +->>
        if (
            char == "+"
            and self._peek_char() == "-"
            and self._peek_char(2) == ">"
            and self._peek_char(3) == ">"
        ):
            self._advance()
            self._advance()
            self._advance()
            self._advance()
            return Token(TokenType.PSURJ, "+->>", start_line, start_column)

        # Check 3-character: +->
        if char == "+" and self._peek_char() == "-" and self._peek_char(2) == ">":
            self._advance()
            self._advance()
            self._advance()
            return Token(TokenType.PFUN, "+->", start_line, start_column)

        # Override operator: ++ (Phase 13)
        if char == "+" and self._peek_char() == "+":
            self._advance()
            self._advance()
            return Token(TokenType.OVERRIDE, "++", start_line, start_column)

        if char == "+":
            self._advance()
            return Token(TokenType.PLUS, "+", start_line, start_column)

        # Note: * is used for both SOLUTION_MARKER (**) and STAR (*)
        # ** is checked earlier, so single * is safe here
        if char == "*":
            self._advance()
            return Token(TokenType.STAR, "*", start_line, start_column)

        # Function type operators starting with - (Phase 11a)
        # Check 4-character first: -->>
        if (
            char == "-"
            and self._peek_char() == "-"
            and self._peek_char(2) == ">"
            and self._peek_char(3) == ">"
        ):
            self._advance()
            self._advance()
            self._advance()
            self._advance()
            return Token(TokenType.TSURJ, "-->>", start_line, start_column)

        # Check 3-character: -|> (Phase 18 - partial injection alternative)
        if char == "-" and self._peek_char() == "|" and self._peek_char(2) == ">":
            self._advance()
            self._advance()
            self._advance()
            return Token(TokenType.PINJ_ALT, "-|>", start_line, start_column)

        # Check 2-character: ->
        if char == "-" and self._peek_char() == ">":
            self._advance()
            self._advance()
            return Token(TokenType.TFUN, "->", start_line, start_column)

        # Phase 20: Visual separator lines (-----, ===== etc.)
        # If at start of line and followed by many more of the same character,
        # treat as TEXT
        if start_column == 1 and char == "-":
            # Check if this is a separator line (many dashes)
            consecutive_dashes = 1
            temp_pos = self.pos + 1
            while temp_pos < len(self.text) and self.text[temp_pos] == "-":
                consecutive_dashes += 1
                temp_pos += 1
            # If 10+ consecutive dashes at start of line, treat as TEXT separator
            if consecutive_dashes >= 10:
                text_start = self.pos
                while not self._at_end() and self._current_char() != "\n":
                    self._advance()
                text_content = self.text[text_start : self.pos]
                return Token(TokenType.TEXT, text_content, start_line, start_column)

        # Standalone minus (subtraction/negation)
        if char == "-":
            self._advance()
            return Token(TokenType.MINUS, "-", start_line, start_column)

        # Identifiers and keywords (Phase 15: allow underscore in identifiers)
        if char.isalpha() or char == "_":
            return self._scan_identifier(start_line, start_column)

        # Numbers and digit-starting identifiers (Phase 18)
        # Digit-starting identifiers: 479_courses (digit followed by underscore+letter)
        # Pure numbers: 479 (digits only)
        # Finite function operator: 7 7-> (Phase 34)
        if (
            char == "7"
            and self._peek_char() == " "
            and self._peek_char(2) == "7"
            and self._peek_char(3) == "-"
            and self._peek_char(4) == ">"
        ):
            self._advance()  # 7
            self._advance()  # space
            self._advance()  # 7
            self._advance()  # -
            self._advance()  # >
            return Token(TokenType.FINFUN, "7 7->", start_line, start_column)

        if char.isdigit():
            # Peek ahead to determine if this is identifier or number
            # Scan all digits first
            temp_pos = self.pos
            while temp_pos < len(self.text) and self.text[temp_pos].isdigit():
                temp_pos += 1

            # Check if followed by underscore and then letter/digit
            # Pattern: 479_courses (digit+underscore+alphanumeric)
            if (
                temp_pos < len(self.text)
                and self.text[temp_pos] == "_"
                and temp_pos + 1 < len(self.text)
                and (self.text[temp_pos + 1].isalnum())
            ):
                # It's an identifier starting with digits
                return self._scan_identifier(start_line, start_column)

            # It's a plain number
            return self._scan_number(start_line, start_column)

        # Unicode symbols (Phase 11.5)
        if char == "×":  # noqa: RUF001
            self._advance()
            return Token(TokenType.CROSS, "×", start_line, start_column)  # noqa: RUF001

        # Set difference operator OR line continuation (Phase 11.5, enhanced Phase 27)
        if char == "\\":
            # Look ahead for newline (continuation marker)
            peek_pos = 1
            # Skip optional whitespace after backslash
            while self._peek_char(peek_pos) in " \t":
                peek_pos += 1

            # If followed by newline, it's a continuation marker
            if self._peek_char(peek_pos) == "\n":
                self._advance()  # consume \
                # Consume optional trailing whitespace
                while self._current_char() in " \t":
                    self._advance()
                # Don't consume newline - let it be a separate token
                return Token(TokenType.CONTINUATION, "\\", start_line, start_column)

            # Not followed by newline → set difference operator
            self._advance()
            return Token(TokenType.SETMINUS, "\\", start_line, start_column)

        # Sequence literals (Phase 12) - Unicode angle brackets
        if char == "⟨":
            self._advance()
            return Token(TokenType.LANGLE, "⟨", start_line, start_column)

        if char == "⟩":
            self._advance()
            return Token(TokenType.RANGLE, "⟩", start_line, start_column)

        # Sequence concatenation (Phase 12)
        if char == "⌢":
            self._advance()
            return Token(TokenType.CAT, "⌢", start_line, start_column)

        # Sequence filter (Phase 35)
        if char == "↾":
            self._advance()
            return Token(TokenType.FILTER, "↾", start_line, start_column)

        # Bag union (Phase 12)
        if char == "⊎":
            self._advance()
            return Token(TokenType.BAG_UNION, "⊎", start_line, start_column)

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

        # Phase 15: Include underscore in identifiers
        # Phase 24: Allow apostrophes in contractions (Let's, can't)
        # This allows multi-word identifiers like cumulative_total
        # Subscripts like a_i are now handled in LaTeX generation
        while not self._at_end():
            current = self._current_char()
            if current.isalnum() or current == "_":
                self._advance()
            elif current == "'" and self._peek_char().isalpha():
                # Allow apostrophe if followed by a letter (contraction)
                self._advance()
            else:
                break

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
            while not self._at_end() and self._current_char() in " \t":
                self._advance()

            # Capture the rest of the line as raw text (don't tokenize)
            text_start = self.pos
            while not self._at_end() and self._current_char() != "\n":
                self._advance()

            # Extract the raw text content
            text_content = self.text[text_start : self.pos]

            return Token(TokenType.TEXT, text_content, start_line, start_column)

        # Check for PURETEXT: keyword - capture rest of line as completely raw text
        if value == "PURETEXT" and self._current_char() == ":":
            self._advance()  # Consume ':'

            # Skip any whitespace after the colon
            while not self._at_end() and self._current_char() in " \t":
                self._advance()

            # Capture the rest of the line as raw text (don't tokenize)
            text_start = self.pos
            while not self._at_end() and self._current_char() != "\n":
                self._advance()

            # Extract the raw text content
            text_content = self.text[text_start : self.pos]

            return Token(TokenType.PURETEXT, text_content, start_line, start_column)

        # Check for LATEX: keyword - capture rest of line as raw LaTeX (no escaping)
        if value == "LATEX" and self._current_char() == ":":
            self._advance()  # Consume ':'

            # Skip any whitespace after the colon
            while not self._at_end() and self._current_char() in " \t":
                self._advance()

            # Capture the rest of the line as raw LaTeX (don't tokenize)
            text_start = self.pos
            while not self._at_end() and self._current_char() != "\n":
                self._advance()

            # Extract the raw LaTeX content
            text_content = self.text[text_start : self.pos]

            return Token(TokenType.LATEX, text_content, start_line, start_column)

        # Check for PAGEBREAK: keyword
        if value == "PAGEBREAK" and self._current_char() == ":":
            self._advance()  # Consume ':'
            return Token(TokenType.PAGEBREAK, "PAGEBREAK:", start_line, start_column)

        # Phase 20: Auto-detect prose paragraphs BEFORE keyword checks
        # Phase 24: Also detect prose after part labels (any column)
        # Check for capitalized prose starters
        # Exclude articles (A, An) that might be type names
        prose_starters = {
            "The",
            "This",
            "These",
            "Those",
            "That",
            "We",
            "It",
            "They",
            "There",
            "Here",
            "In",
            "On",
            "At",
            "For",
            "When",
            "Where",
            "Why",
            "How",
            "What",
            "If",
            "Since",
            "Because",
            "Although",
            "While",
            "Each",
            "Every",
            "Some",
            "All",
            "Any",
            "By",
            "From",
            "To",
            "With",
            "Without",
            "First",
            "Second",
            "Third",
            "Finally",
            "Next",
            "Then",
            "Note",
            "Consider",
            "Suppose",
            "Recall",
            "Let",
            "Given",
            "Assuming",
            "Hence",
            "Thus",
            "Therefore",
            # Phase 24: Common contractions
            "Let's",
            "It's",
            "That's",
            "There's",
            "Here's",
            "What's",
            "Who's",
            "Where's",
            "When's",
            "How's",
            "We're",
            "They're",
            "You're",
            "Don't",
            "Doesn't",
            "Didn't",
            "Can't",
            "Won't",
            "Shouldn't",
            "Wouldn't",
            "Haven't",
            "Hasn't",
            "Hadn't",
            "Aren't",
            "Isn't",
            "Wasn't",
            "Weren't",
        }

        # Prose detection at column 1 OR after whitespace (for prose after part labels)
        # BUT NOT inside solution markers (** ... **) to avoid consuming closing **
        if value in prose_starters and not self._in_solution_marker:
            # Looks like prose, capture whole line
            text_start = start_pos

            while not self._at_end() and self._current_char() != "\n":
                self._advance()

            text_content = self.text[start_pos : self.pos]
            return Token(TokenType.TEXT, text_content, start_line, start_column)

        # Special handling for articles A/An - only treat as prose if followed
        # by common English word
        if start_column == 1 and value in ("A", "An"):
            # Peek ahead to check if this is an article or a type name
            # Article: "A function is..." or "An element is..."
            # Type name: "A -> B" or "A union B" (union is Z keyword, not prose)
            temp_pos = self.pos
            # Skip whitespace
            while temp_pos < len(self.text) and self.text[temp_pos] in " \t":
                temp_pos += 1
            # Check next word
            if temp_pos < len(self.text):
                next_char = self.text[temp_pos]
                # If next word starts with lowercase, check if it's a Z keyword
                if next_char.islower():
                    # Scan the next word
                    next_word_start = temp_pos
                    while temp_pos < len(self.text) and (
                        self.text[temp_pos].isalnum() or self.text[temp_pos] == "_"
                    ):
                        temp_pos += 1
                    next_word = self.text[next_word_start:temp_pos]

                    # Z keywords that shouldn't trigger prose mode
                    z_keywords = {
                        "and",
                        "or",
                        "not",
                        "union",
                        "intersect",
                        "in",
                        "notin",
                        "subset",
                        "subseteq",
                        "cross",
                        "dom",
                        "ran",
                        "inv",
                        "id",
                        "comp",
                        "forall",
                        "exists",
                        "exists1",
                        "mu",
                        "lambda",
                        "given",
                        "axdef",
                        "schema",
                        "gendef",
                        "zed",
                        "where",
                        "end",
                        "if",
                        "then",
                        "else",
                        "otherwise",
                        "mod",
                    }

                    # If next word is NOT a Z keyword, treat as prose
                    if next_word not in z_keywords:
                        text_start = start_pos
                        while not self._at_end() and self._current_char() != "\n":
                            self._advance()
                        text_content = self.text[text_start : self.pos]
                        return Token(
                            TokenType.TEXT, text_content, start_line, start_column
                        )

        # Check for lowercase keywords at start of line that might be prose
        # Examples: "where cat.1a is", "and the second by"
        if start_column == 1 and value in ("where", "and"):
            # Peek ahead to see if this line looks like prose
            temp_pos = self.pos
            line_rest = ""
            while temp_pos < len(self.text) and self.text[temp_pos] != "\n":
                line_rest += self.text[temp_pos]
                temp_pos += 1

            # If line contains prose indicators, treat whole line as TEXT
            # Check for both " word " (middle of line) and " word" (end of line)
            full_line = value + line_rest
            prose_indicators = [
                " is ",
                " is",
                " by ",
                " by",
                " are ",
                " are",
                " was ",
                " was",
                " were ",
                " were",
            ]
            if any(indicator in full_line for indicator in prose_indicators):
                # This is prose, not Z notation
                text_start = start_pos

                while not self._at_end() and self._current_char() != "\n":
                    self._advance()

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
        if value == "lambda":
            return Token(TokenType.LAMBDA, value, start_line, start_column)

        # Check for set operators (Phase 3, enhanced in Phase 7, Phase 11.5)
        if value == "notin":
            return Token(TokenType.NOTIN, value, start_line, start_column)
        if value == "in":
            return Token(TokenType.IN, value, start_line, start_column)
        if value == "subset" or value == "subseteq":
            return Token(TokenType.SUBSET, value, start_line, start_column)
        if value == "union":
            return Token(TokenType.UNION, value, start_line, start_column)
        if value == "intersect":
            return Token(TokenType.INTERSECT, value, start_line, start_column)
        if value == "cross":
            return Token(TokenType.CROSS, value, start_line, start_column)

        # Check for Z notation keywords (Phase 4)
        if value == "given":
            return Token(TokenType.GIVEN, value, start_line, start_column)
        if value == "axdef":
            return Token(TokenType.AXDEF, value, start_line, start_column)
        if value == "schema":
            return Token(TokenType.SCHEMA, value, start_line, start_column)
        if value == "gendef":
            return Token(TokenType.GENDEF, value, start_line, start_column)
        if value == "zed":
            return Token(TokenType.ZED, value, start_line, start_column)
        if value == "where":
            return Token(TokenType.WHERE, value, start_line, start_column)
        if value == "end":
            return Token(TokenType.END, value, start_line, start_column)

        # Check for conditional expression keywords (Phase 16)
        if value == "if":
            return Token(TokenType.IF, value, start_line, start_column)
        if value == "then":
            return Token(TokenType.THEN, value, start_line, start_column)
        if value == "else":
            return Token(TokenType.ELSE, value, start_line, start_column)
        if value == "otherwise":
            return Token(TokenType.OTHERWISE, value, start_line, start_column)

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

        # Check for arithmetic operators (modulo)
        if value == "mod":
            return Token(TokenType.MOD, value, start_line, start_column)

        # Check for power set and finite set functions (Phase 11.5, enhanced Phase 19)
        if value == "P1":
            return Token(TokenType.POWER1, value, start_line, start_column)
        if value == "P":
            return Token(TokenType.POWER, value, start_line, start_column)
        if value == "F1":
            return Token(TokenType.FINSET1, value, start_line, start_column)
        if value == "F":
            return Token(TokenType.FINSET, value, start_line, start_column)

        # Check for sequence operator keywords (Phase 12)
        # Note: seq and seq1 are left as identifiers to support seq(X) and seq[X]
        if value == "head":
            return Token(TokenType.HEAD, value, start_line, start_column)
        if value == "tail":
            return Token(TokenType.TAIL, value, start_line, start_column)
        if value == "last":
            return Token(TokenType.LAST, value, start_line, start_column)
        if value == "front":
            return Token(TokenType.FRONT, value, start_line, start_column)
        if value == "rev":
            return Token(TokenType.REV, value, start_line, start_column)

        # Check for set operators (Phase 20)
        if value == "bigcup":
            return Token(TokenType.BIGCUP, value, start_line, start_column)
        if value == "bigcap":
            return Token(TokenType.BIGCAP, value, start_line, start_column)

        # Regular identifier (includes seq, seq1)
        return Token(TokenType.IDENTIFIER, value, start_line, start_column)

    def _scan_number(self, start_line: int, start_column: int) -> Token:
        """Scan number."""
        start_pos = self.pos
        while not self._at_end() and self._current_char().isdigit():
            self._advance()

        value = self.text[start_pos : self.pos]
        return Token(TokenType.NUMBER, value, start_line, start_column)
