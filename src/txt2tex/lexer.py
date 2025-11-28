"""Lexer for txt2tex - converts text into tokens."""

from __future__ import annotations

from txt2tex.tokens import Token, TokenType

# Keyword to token type mapping for simple keywords.
# This replaces ~40 individual if-statements in _scan_identifier,
# reducing cyclomatic complexity significantly.
KEYWORD_TO_TOKEN: dict[str, TokenType] = {
    # Logical operators (LaTeX-style only)
    "land": TokenType.AND,
    "lor": TokenType.OR,
    "lnot": TokenType.NOT,
    # Quantifiers
    "forall": TokenType.FORALL,
    "exists1": TokenType.EXISTS1,
    "exists": TokenType.EXISTS,
    "mu": TokenType.MU,
    "lambda": TokenType.LAMBDA,
    # Set operators
    "notin": TokenType.NOTIN,
    "elem": TokenType.IN,
    "psubset": TokenType.PSUBSET,
    "union": TokenType.UNION,
    "intersect": TokenType.INTERSECT,
    "cross": TokenType.CROSS,
    "bigcup": TokenType.BIGCUP,
    "bigcap": TokenType.BIGCAP,
    # Z notation keywords
    "given": TokenType.GIVEN,
    "axdef": TokenType.AXDEF,
    "schema": TokenType.SCHEMA,
    "gendef": TokenType.GENDEF,
    "zed": TokenType.ZED,
    "syntax": TokenType.SYNTAX,
    "where": TokenType.WHERE,
    "end": TokenType.END,
    # Conditional expression keywords
    "if": TokenType.IF,
    "then": TokenType.THEN,
    "else": TokenType.ELSE,
    "otherwise": TokenType.OTHERWISE,
    # Relation operators
    "comp": TokenType.COMP,
    "dom": TokenType.DOM,
    "ran": TokenType.RAN,
    "inv": TokenType.INV,
    "id": TokenType.ID,
    # Judgment operator
    "shows": TokenType.SHOWS,
    # Arithmetic
    "mod": TokenType.MOD,
    # Power set and finite set
    "P1": TokenType.POWER1,
    "P": TokenType.POWER,
    "F1": TokenType.FINSET1,
    "F": TokenType.FINSET,
    # Filter and bag operators
    "filter": TokenType.FILTER,
    "bag_union": TokenType.BAG_UNION,
}

# Keywords that map to the same token type (aliases)
KEYWORD_ALIASES: dict[str, TokenType] = {
    "subset": TokenType.SUBSET,
    "subseteq": TokenType.SUBSET,
}

# Single-character tokens that don't require lookahead.
# These can be dispatched directly without peek checks.
# Note: Characters like (, [, {, |, ., :, +, -, *, = require lookahead
# for multi-character operators, so they stay as if-statements.
SINGLE_CHAR_TOKENS: dict[str, TokenType] = {
    ")": TokenType.RPAREN,
    "]": TokenType.RBRACKET,
    "}": TokenType.RBRACE,
    ",": TokenType.COMMA,
    ";": TokenType.SEMICOLON,
    "#": TokenType.HASH,
    "~": TokenType.TILDE,
}


class LexerError(Exception):
    """Raised when lexer encounters invalid input."""

    # Instance variable type annotations
    message: str
    line: int
    column: int

    def __init__(self, message: str, line: int, column: int) -> None:
        """Initialize lexer error with position."""
        super().__init__(f"Line {line}, column {column}: {message}")
        self.message = message
        self.line = line
        self.column = column


class Lexer:
    """Tokenizes input text for txt2tex.

    Supports propositional logic, document structure, equivalence chains,
    predicate logic with quantifiers and mathematical notation, Z notation,
    relational operators (<->, |->, <|, |>, comp, ;, dom, ran, <<|, |>>, etc.),
    and function types (->, +->, >->, >+>, -->>, +->>, >->>).
    """

    # Instance variable type annotations
    text: str
    pos: int
    line: int
    column: int
    _in_solution_marker: bool

    def __init__(self, text: str) -> None:
        """Initialize lexer with input text."""
        self.text = text
        self.pos = 0
        self.line = 1
        self.column = 1
        self._in_solution_marker = False  # Track if inside ** ... **

    def _raise_infinite_loop_error(
        self,
        context_msg: str,
        peek_pos: int | None = None,
        current_char: str | None = None,
    ) -> None:
        """
        Raise RuntimeError with diagnostic information about infinite loop.

        Args:
            context_msg: Description of where the loop occurred
            peek_pos: Optional peek position for detailed diagnostics
            current_char: Optional current character for diagnostics
        """
        context_start = max(0, self.pos - 20)
        context_end = min(len(self.text), self.pos + 20)
        context = repr(self.text[context_start:context_end])

        # Build detailed error message with all diagnostic info
        details = [
            f"Infinite loop detected in lexer at position {self.pos}, "
            f"line {self.line}, column {self.column}: {context_msg}",
            f"Text length: {len(self.text)}",
            f"Context (-20/+20): {context}",
        ]

        if current_char is not None:
            details.append(f"Current char: {current_char!r}")
        if peek_pos is not None:
            details.append(f"Peek pos: {peek_pos}")
            details.append(f"Next 50 chars: {self.text[self.pos : self.pos + 50]!r}")

        raise RuntimeError("\n".join(details))

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

    def _scan_token(self) -> Token | None:  # noqa: C901
        """Scan next token from input."""
        start_line = self.line
        start_column = self.column

        char = self._current_char()

        # Whitespace (skip but track)
        if char in " \t":
            self._advance()
            return None  # Skip whitespace

        # Line comments: // ... (skip to end of line)
        if char == "/" and self._peek_char() == "/":
            # Skip the entire line including the newline
            while not self._at_end() and self._current_char() != "\n":
                self._advance()
            # Don't consume the newline - let normal newline handling do it
            return None

        # Newline (significant for multi-line documents)
        if char == "\n":
            self._advance()
            return Token(TokenType.NEWLINE, "\n", start_line, start_column)

        # Single-character token dispatch (no lookahead needed)
        # This replaces individual if-statements for ), ], }, ,, ;, #, ~
        if char in SINGLE_CHAR_TOKENS:
            self._advance()
            return Token(SINGLE_CHAR_TOKENS[char], char, start_line, start_column)

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

        # Relation type operator: <->
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

        # Part label: (a), (b), ..., (j), (aa), (ab), etc.
        # Only match at start of line to avoid function app conflict
        # Single letters restricted to (a)-(j) to avoid conflict with vars like (x), (s)
        # Multi-letter (2+) allowed for extended numbering: (aa), (ab), (ba), (bb), ...
        # Must be followed by whitespace/newline (structural) not operators (expression)
        if char == "(" and start_column == 1:
            # Peek ahead to check for part label pattern
            lookahead_pos = 1
            label_chars = ""

            # Collect consecutive lowercase letters
            while True:
                peek_char = self._peek_char(lookahead_pos)
                if peek_char.islower():
                    label_chars += peek_char
                    lookahead_pos += 1
                else:
                    break

            # Check if we have valid part label:
            # - Single letter (a)-(j), OR
            # - Multi-letter (2+): (aa), (ab), (abc), etc.
            # Must be followed by ')' and then whitespace/newline
            if label_chars and self._peek_char(lookahead_pos) == ")":
                is_valid_label = False
                if len(label_chars) == 1 and "a" <= label_chars[0] <= "j":
                    is_valid_label = True  # (a)-(j)
                elif len(label_chars) >= 2:
                    is_valid_label = True  # (aa), (ab), etc.

                if is_valid_label:
                    char_after = self._peek_char(lookahead_pos + 1)
                    # Part labels are structural - must be followed by space/tab/newline
                    # NOT EOF - that would match (x) in parse_expr("(x)")
                    if char_after in (" ", "\t", "\n"):
                        self._advance()  # consume '('
                        # Consume all label characters
                        for _ in label_chars:
                            self._advance()
                        self._advance()  # consume ')'
                        return Token(
                            TokenType.PART_LABEL,
                            f"({label_chars})",
                            start_line,
                            start_column,
                        )

        # Relational image operators: (| and |)
        # Check before simple parentheses
        if char == "(" and self._peek_char() == "|":
            self._advance()
            self._advance()
            return Token(TokenType.LIMG, "(|", start_line, start_column)

        # Parentheses
        if char == "(":
            self._advance()
            return Token(TokenType.LPAREN, "(", start_line, start_column)

        # Brackets (for justifications and generics)
        # Note: Bag literals [[...]] are handled at parser level, not lexer level
        # to avoid conflicts with nested brackets like Type[List[N]]
        if char == "[":
            self._advance()
            return Token(TokenType.LBRACKET, "[", start_line, start_column)

        # Braces (for sets and grouping subscripts/superscripts)
        if char == "{":
            self._advance()
            return Token(TokenType.LBRACE, "{", start_line, start_column)

        # Maplet operator: |-> - check before | alone
        if char == "|" and self._peek_char() == "-" and self._peek_char(2) == ">":
            self._advance()
            self._advance()
            self._advance()
            return Token(TokenType.MAPLET, "|->", start_line, start_column)

        # Range subtraction operator: |>> - check before |> and | alone
        if char == "|" and self._peek_char() == ">" and self._peek_char(2) == ">":
            self._advance()
            self._advance()
            self._advance()
            return Token(TokenType.NRRES, "|>>", start_line, start_column)

        # Range restriction operator: |> - check before | alone
        if char == "|" and self._peek_char() == ">":
            self._advance()
            self._advance()
            return Token(TokenType.RRES, "|>", start_line, start_column)

        # Relational image right bracket: |) - check before | alone
        if char == "|" and self._peek_char() == ")":
            self._advance()
            self._advance()
            return Token(TokenType.RIMG, "|)", start_line, start_column)

        # Pipe (for truth tables and quantifiers)
        if char == "|":
            self._advance()
            return Token(TokenType.PIPE, "|", start_line, start_column)

        # Ellipsis ... - check before range operator
        if char == "." and self._peek_char() == "." and self._peek_char(2) == ".":
            self._advance()
            self._advance()
            self._advance()
            return Token(TokenType.ELLIPSIS, "...", start_line, start_column)

        # Range operator .. - check before period alone
        if char == "." and self._peek_char() == ".":
            self._advance()
            self._advance()
            return Token(TokenType.RANGE, "..", start_line, start_column)

        # Period (for sentences in paragraphs and tuple projection)
        if char == ".":
            self._advance()
            return Token(TokenType.PERIOD, ".", start_line, start_column)

        # Free type operator ::= - check before :: and :
        if char == ":" and self._peek_char() == ":" and self._peek_char(2) == "=":
            self._advance()
            self._advance()
            self._advance()
            return Token(TokenType.FREE_TYPE, "::=", start_line, start_column)

        # Double colon :: (sibling marker in proofs) - check before : alone
        if char == ":" and self._peek_char() == ":":
            self._advance()
            self._advance()
            return Token(TokenType.DOUBLE_COLON, "::", start_line, start_column)

        # Colon (for quantifiers and declarations)
        if char == ":":
            self._advance()
            return Token(TokenType.COLON, ":", start_line, start_column)

        # Comparison operators
        # Check <= and >= before < and >
        # But watch out for <=> and <-> which are handled earlier
        # Domain subtraction operator: <<| - check before <| and < alone
        if char == "<" and self._peek_char() == "<" and self._peek_char(2) == "|":
            self._advance()
            self._advance()
            self._advance()
            return Token(TokenType.NDRES, "<<|", start_line, start_column)

        # Domain restriction operator: <| - check before < alone
        if char == "<" and self._peek_char() == "|":
            self._advance()
            self._advance()
            return Token(TokenType.DRES, "<|", start_line, start_column)

        if char == "<" and self._peek_char() == "=" and self._peek_char(2) != ">":
            self._advance()
            self._advance()
            return Token(TokenType.LESS_EQUAL, "<=", start_line, start_column)

        # ASCII sequence brackets <> as alternative to Unicode ⟨⟩
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

        # Function type operators starting with >
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

        # ASCII sequence brackets - recognize > as RANGLE
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

        # Not equal != - check before other operators
        if char == "!" and self._peek_char() == "=":
            self._advance()
            self._advance()
            return Token(TokenType.NOT_EQUAL, "!=", start_line, start_column)

        # Not equal /= (Z notation slash negation)
        if char == "/" and self._peek_char() == "=":
            self._advance()
            self._advance()
            return Token(TokenType.NOT_EQUAL, "/=", start_line, start_column)

        # Not in /in (Z notation slash negation)
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

        # Abbreviation operator == - check before = alone
        # Already checked for === and => earlier
        if char == "=" and self._peek_char() == "=":
            self._advance()
            self._advance()
            return Token(TokenType.ABBREV, "==", start_line, start_column)

        # Equals - but not =>, ==, or === which are handled earlier
        if char == "=":
            self._advance()
            return Token(TokenType.EQUALS, "=", start_line, start_column)

        # Math operators
        # Caret: ^ can mean superscript OR sequence concatenation
        # Whitespace-sensitive disambiguation:
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

        # Function type operators starting with +
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

        # Override operator: ++
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

        # Function type operators starting with -
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

        # Check 3-character: -|> (partial injection alternative)
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

        # Visual separator lines (-----, ===== etc.)
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

        # Check for --- (derive separator in INFRULE)
        if char == "-" and self._peek_char() == "-" and self._peek_char(2) == "-":
            self._advance()
            self._advance()
            self._advance()
            return Token(TokenType.DERIVE, "---", start_line, start_column)

        # Standalone minus (subtraction/negation)
        if char == "-":
            self._advance()
            return Token(TokenType.MINUS, "-", start_line, start_column)

        # Identifiers and keywords (allow underscore in identifiers)
        if char.isalpha() or char == "_":
            return self._scan_identifier(start_line, start_column)

        # Numbers and digit-starting identifiers
        # Digit-starting identifiers: 479_courses (digit followed by underscore+letter)
        # Pure numbers: 479 (digits only)
        # Finite function operator: 77->
        if (
            char == "7"
            and self._peek_char() == "7"
            and self._peek_char(2) == "-"
            and self._peek_char(3) == ">"
        ):
            self._advance()  # 7
            self._advance()  # 7
            self._advance()  # -
            self._advance()  # >
            return Token(TokenType.FINFUN, "77->", start_line, start_column)

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

        # Unicode symbols
        if char == "×":  # noqa: RUF001
            self._advance()
            return Token(TokenType.CROSS, "×", start_line, start_column)  # noqa: RUF001

        # Set difference operator OR line continuation
        if char == "\\":
            # Look ahead for newline (continuation marker)
            peek_pos = 1
            # Skip optional whitespace after backslash
            # Safety limit to prevent infinite loops
            max_iterations = 10000
            iterations = 0
            # Bug fix: empty string is "in" any string in Python,
            # so we must check for it explicitly
            ch = self._peek_char(peek_pos)
            while ch != "" and ch in " \t":
                peek_pos += 1
                ch = self._peek_char(peek_pos)
                iterations += 1
                if iterations >= max_iterations:
                    self._raise_infinite_loop_error(
                        "skipping whitespace after backslash",
                        peek_pos=peek_pos,
                        current_char=char,
                    )

            # If followed by newline, it's a continuation marker
            if self._peek_char(peek_pos) == "\n":
                self._advance()  # consume \
                # Consume optional trailing whitespace
                # Safety limit to prevent infinite loops
                iterations = 0
                while self._current_char() in " \t":
                    self._advance()
                    iterations += 1
                    if iterations >= max_iterations:
                        self._raise_infinite_loop_error(
                            "consuming trailing whitespace after backslash-newline"
                        )
                # Don't consume newline - let it be a separate token
                return Token(TokenType.CONTINUATION, "\\", start_line, start_column)

            # Not followed by newline → set difference operator
            self._advance()
            return Token(TokenType.SETMINUS, "\\", start_line, start_column)

        # Sequence literals - Unicode angle brackets
        if char == "⟨":
            self._advance()
            return Token(TokenType.LANGLE, "⟨", start_line, start_column)

        if char == "⟩":
            self._advance()
            return Token(TokenType.RANGLE, "⟩", start_line, start_column)

        # Sequence concatenation
        if char == "⌢":
            self._advance()
            return Token(TokenType.CAT, "⌢", start_line, start_column)

        # Sequence filter
        if char == "↾":
            self._advance()
            return Token(TokenType.FILTER, "↾", start_line, start_column)

        # Bag union
        if char == "⊎":
            self._advance()
            return Token(TokenType.BAG_UNION, "⊎", start_line, start_column)

        # Unknown character
        raise LexerError(f"Unexpected character: {char!r}", self.line, self.column)

    def _scan_identifier(self, start_line: int, start_column: int) -> Token:  # noqa: C901
        """Scan identifier or keyword."""
        start_pos = self.pos

        # Check for special o9 operator - composition
        if self._current_char() == "o" and self._peek_char() == "9":
            self._advance()  # consume 'o'
            self._advance()  # consume '9'
            return Token(TokenType.CIRC, "o9", start_line, start_column)

        # Include underscore in identifiers and apostrophes in contractions
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

        # Check for ARGUE: or EQUIV: keywords (both map to ARGUE token)
        # EQUIV is backwards-compatible alias for ARGUE
        if (value == "ARGUE" or value == "EQUIV") and self._current_char() == ":":
            self._advance()  # Consume ':'
            keyword = f"{value}:"
            return Token(TokenType.ARGUE, keyword, start_line, start_column)

        # Check for INFRULE: keyword
        if value == "INFRULE" and self._current_char() == ":":
            self._advance()  # Consume ':'
            return Token(TokenType.INFRULE, "INFRULE:", start_line, start_column)

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

        # Check for title metadata keywords: TITLE:, AUTHOR:, DATE:, etc.
        title_keywords = {
            "TITLE": TokenType.TITLE,
            "SUBTITLE": TokenType.SUBTITLE,
            "AUTHOR": TokenType.AUTHOR,
            "DATE": TokenType.DATE,
            "INSTITUTION": TokenType.INSTITUTION,
        }
        if value in title_keywords and self._current_char() == ":":
            token_type = title_keywords[value]
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

            return Token(token_type, text_content, start_line, start_column)

        # Check for CONTENTS: keyword (table of contents)
        if value == "CONTENTS" and self._current_char() == ":":
            self._advance()  # Consume ':'
            # Skip whitespace after colon
            while not self._at_end() and self._current_char() in " \t":
                self._advance()
            # Capture optional depth parameter (e.g., "full" or "2")
            depth_start = self.pos
            while not self._at_end() and self._current_char() not in "\n":
                self._advance()
            depth_value = self.text[depth_start : self.pos].strip()
            return Token(TokenType.CONTENTS, depth_value, start_line, start_column)

        # Check for PARTS: keyword (parts formatting style)
        if value == "PARTS" and self._current_char() == ":":
            self._advance()  # Consume ':'
            # Skip whitespace after colon
            while not self._at_end() and self._current_char() in " \t":
                self._advance()
            # Capture style value (e.g., "inline" or "subsection")
            style_start = self.pos
            while not self._at_end() and self._current_char() not in "\n":
                self._advance()
            style_value = self.text[style_start : self.pos].strip()
            return Token(TokenType.PARTS, style_value, start_line, start_column)

        # Check for BIBLIOGRAPHY: keyword (bibliography file)
        if value == "BIBLIOGRAPHY" and self._current_char() == ":":
            self._advance()  # Consume ':'
            # Skip whitespace after colon
            while not self._at_end() and self._current_char() in " \t":
                self._advance()
            # Capture filename (e.g., "references.bib")
            file_start = self.pos
            while not self._at_end() and self._current_char() not in "\n":
                self._advance()
            file_value = self.text[file_start : self.pos].strip()
            return Token(TokenType.BIBLIOGRAPHY, file_value, start_line, start_column)

        # Check for BIBLIOGRAPHY_STYLE: keyword (bibliography style)
        if value == "BIBLIOGRAPHY_STYLE" and self._current_char() == ":":
            self._advance()  # Consume ':'
            # Skip whitespace after colon
            while not self._at_end() and self._current_char() in " \t":
                self._advance()
            # Capture style name (e.g., "harvard", "plainnat")
            style_start = self.pos
            while not self._at_end() and self._current_char() not in "\n":
                self._advance()
            style_value = self.text[style_start : self.pos].strip()
            return Token(
                TokenType.BIBLIOGRAPHY_STYLE, style_value, start_line, start_column
            )

        # Check for PAGEBREAK: keyword
        if value == "PAGEBREAK" and self._current_char() == ":":
            self._advance()  # Consume ':'
            return Token(TokenType.PAGEBREAK, "PAGEBREAK:", start_line, start_column)

        # Auto-detect prose paragraphs BEFORE keyword checks
        # Also detect prose after part labels (any column)
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
            "Show",
            "Prove",
            "Verify",
            "Check",
            "Using",
            "Calculate",
            "Find",
            "Determine",
            # Common contractions
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
        # AND NOT in section headers (lines containing ===)
        if value in prose_starters and not self._in_solution_marker:
            # Check if the rest of the line contains "===" (section header)
            temp_pos = self.pos
            while temp_pos < len(self.text) and self.text[temp_pos] != "\n":
                if (
                    temp_pos + 2 < len(self.text)
                    and self.text[temp_pos : temp_pos + 3] == "==="
                ):
                    # This is a section header, not prose
                    # Return as regular identifier
                    return Token(TokenType.IDENTIFIER, value, start_line, start_column)
                temp_pos += 1

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
            # Article: "A function is..." or "An element is..."  # noqa: ERA001
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
                        "land",
                        "lor",
                        "lnot",
                        "union",
                        "intersect",
                        "elem",
                        "notin",
                        "subset",
                        "subseteq",
                        "psubset",
                        "cross",
                        "dom",
                        "ran",
                        "inv",
                        "id",
                        "comp",
                        "shows",
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
                        "syntax",
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

        # Check for keywords using lookup tables (replaces ~40 if-statements)
        # This reduces cyclomatic complexity significantly
        if value in KEYWORD_TO_TOKEN:
            return Token(KEYWORD_TO_TOKEN[value], value, start_line, start_column)

        # Check for keyword aliases (subset/subseteq both map to SUBSET)
        if value in KEYWORD_ALIASES:
            return Token(KEYWORD_ALIASES[value], value, start_line, start_column)

        # Regular identifier (includes seq, seq1)
        return Token(TokenType.IDENTIFIER, value, start_line, start_column)

    def _scan_number(self, start_line: int, start_column: int) -> Token:
        """Scan number."""
        start_pos = self.pos
        while not self._at_end() and self._current_char().isdigit():
            self._advance()

        value = self.text[start_pos : self.pos]
        return Token(TokenType.NUMBER, value, start_line, start_column)
