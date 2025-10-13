"""Parser for txt2tex - converts tokens into AST."""

from __future__ import annotations

from txt2tex.ast_nodes import (
    Abbreviation,
    AxDef,
    BinaryOp,
    CaseAnalysis,
    Declaration,
    Document,
    DocumentItem,
    EquivChain,
    EquivStep,
    Expr,
    FreeType,
    GivenType,
    Identifier,
    Number,
    Paragraph,
    Part,
    ProofNode,
    ProofTree,
    Quantifier,
    Schema,
    Section,
    SetComprehension,
    Solution,
    Subscript,
    Superscript,
    TruthTable,
    UnaryOp,
)
from txt2tex.tokens import Token, TokenType


class ParserError(Exception):
    """Raised when parser encounters invalid syntax."""

    def __init__(self, message: str, token: Token) -> None:
        """Initialize parser error with token position."""
        super().__init__(f"Line {token.line}, column {token.column}: {message}")
        self.token = token


class Parser:
    """
    Recursive descent parser for Phase 0-4 + Phase 10a-b.

    Phase 0 - Expression grammar (precedence from lowest to highest):
        expr     ::= iff
        iff      ::= implies ( '<=>' implies )*
        implies  ::= or ( '=>' or )*
        or       ::= and ( 'or' and )*
        and      ::= unary ( 'and' unary )*
        unary    ::= 'not' unary | primary
        primary  ::= IDENTIFIER | '(' expr ')'

    Phase 1 - Document structure:
        document ::= document_item*
        document_item ::= section | solution | part | truth_table | expr
        section ::= '===' TEXT '===' document_item*
        solution ::= '**' TEXT '**' document_item*
        part ::= PART_LABEL document_item*
        truth_table ::= 'TRUTH TABLE:' table_rows

    Phase 2 - Equivalence chains:
        equiv_chain ::= 'EQUIV:' equiv_step+
        equiv_step ::= expr ('<=' '>')? justification?
        justification ::= '[' TEXT ']'

    Phase 3 - Quantifiers and mathematical notation (enhanced in Phase 6-7):
        expr       ::= quantifier | iff
        quantifier ::= ('forall' | 'exists' | 'exists1' | 'mu')
                       var_list (':' atom)? '|' expr
        var_list   ::= IDENTIFIER (',' IDENTIFIER)*
        iff        ::= implies ( '<=>' implies )*
        implies    ::= or ( '=>' or )*
        or         ::= and ( 'or' and )*
        and        ::= comparison ( 'and' comparison )*
        comparison ::= relation ( ('<' | '>' | '<=' | '>=' | '=' | '!=') relation )?
        relation   ::= set_op ( ('<->' | '|->' | '<|' | '|>' | '<<|' |
                                  '|>>' | 'o9' | 'comp' | ';') set_op )?
        set_op     ::= union ( ('in' | 'notin' | 'subset') union )?
        union      ::= intersect ( 'union' intersect )*
        intersect  ::= unary ( 'intersect' unary )*
        unary      ::= 'not' unary | postfix
        postfix    ::= atom ( '^' atom | '_' atom | '~' | '+' | '*' )*
        atom       ::= ('dom' | 'ran' | 'inv' | 'id') atom |
                       IDENTIFIER | NUMBER | '(' expr ')'

    Phase 10a - Relation operators:
        - Infix: <->, |->, <|, |>, comp, ;
        - Prefix functions: dom, ran

    Phase 10b - Extended relation operators:
        - Infix: <<| (domain subtraction), |>> (range subtraction), o9 (composition)
        - Prefix functions: inv (inverse), id (identity)
        - Postfix: ~ (inverse), + (transitive closure), * (reflexive-transitive closure)
    """

    def __init__(self, tokens: list[Token]) -> None:
        """Initialize parser with token list."""
        self.tokens = tokens
        self.pos = 0

    def parse(self) -> Document | Expr:
        """
        Parse tokens and return AST.

        Returns Document for multi-line input or structural elements,
        or single Expr for single expression (backward compatible).
        """
        self._skip_newlines()

        # Empty input
        if self._at_end():
            return Document(items=[], line=1, column=1)

        first_line = self._current().line

        # Check if we start with a structural element (Phase 1 + Phase 4)
        if self._is_structural_token():
            # Parse as document with structural elements
            items: list[DocumentItem] = []
            while not self._at_end():
                items.append(self._parse_document_item())
                self._skip_newlines()
            return Document(items=items, line=first_line, column=1)

        # Check for abbreviation or free type (Phase 4)
        # Look ahead to see if this is "identifier ::=" or "identifier =="
        if self._match(TokenType.IDENTIFIER):
            next_token = self._peek_ahead(1)
            if next_token.type == TokenType.FREE_TYPE:
                # This is a free type definition
                return Document(
                    items=[self._parse_free_type()], line=first_line, column=1
                )
            if next_token.type == TokenType.ABBREV:
                # This is an abbreviation
                return Document(
                    items=[self._parse_abbreviation()], line=first_line, column=1
                )

        # Check for abbreviation with generic parameters (Phase 9)
        # [X, Y] Name == expression
        if self._match(TokenType.LBRACKET):
            return Document(
                items=[self._parse_abbreviation()], line=first_line, column=1
            )

        # Try to parse as expression
        first_item = self._parse_expr()

        # Check if there are more items (multi-line document)
        if self._match(TokenType.NEWLINE):
            items_list: list[DocumentItem] = [first_item]
            self._skip_newlines()

            while not self._at_end():
                items_list.append(self._parse_document_item())
                self._skip_newlines()

            return Document(items=items_list, line=first_line, column=1)

        # Single expression (Phase 0 backward compatibility)
        if not self._at_end():
            raise ParserError(
                f"Unexpected token after expression: {self._current().value!r}",
                self._current(),
            )
        return first_item

    def _is_structural_token(self) -> bool:
        """Check if current token is a structural element."""
        return self._match(
            TokenType.SECTION_MARKER,
            TokenType.SOLUTION_MARKER,
            TokenType.PART_LABEL,
            TokenType.TRUTH_TABLE,
            TokenType.TEXT,
            TokenType.EQUIV,
            TokenType.GIVEN,
            TokenType.AXDEF,
            TokenType.SCHEMA,
            TokenType.PROOF,
        )

    def _parse_paragraph(self) -> Paragraph:
        """Parse plain text paragraph from TEXT token.

        The TEXT token value contains the raw text content (no tokenization).
        """
        text_token = self._advance()  # Consume TEXT token

        if text_token.type != TokenType.TEXT:
            raise ParserError("Expected TEXT token for paragraph", text_token)

        # The token value contains the raw text (already captured by lexer)
        text = text_token.value

        return Paragraph(text=text, line=text_token.line, column=text_token.column)

    def _parse_document_item(self) -> DocumentItem:
        """Parse a document item (expression or structural element)."""
        if self._match(TokenType.SECTION_MARKER):
            return self._parse_section()
        if self._match(TokenType.SOLUTION_MARKER):
            return self._parse_solution()
        if self._match(TokenType.PART_LABEL):
            return self._parse_part()
        if self._match(TokenType.TRUTH_TABLE):
            return self._parse_truth_table()
        if self._match(TokenType.EQUIV):
            return self._parse_equiv_chain()
        if self._match(TokenType.GIVEN):
            return self._parse_given_type()
        if self._match(TokenType.AXDEF):
            return self._parse_axdef()
        if self._match(TokenType.SCHEMA):
            return self._parse_schema()
        if self._match(TokenType.PROOF):
            return self._parse_proof_tree()
        if self._match(TokenType.TEXT):
            return self._parse_paragraph()

        # Check for abbreviation (identifier == expr) or free type (identifier ::= ...)
        if self._match(TokenType.IDENTIFIER):
            # Look ahead to determine type
            if self._peek_ahead(1).type == TokenType.FREE_TYPE:
                return self._parse_free_type()
            if self._peek_ahead(1).type == TokenType.ABBREV:
                return self._parse_abbreviation()
            # Otherwise fall through to expression parsing

        # Check for abbreviation with generic parameters (Phase 9)
        # [X, Y] Name == expression
        if self._match(TokenType.LBRACKET):
            return self._parse_abbreviation()

        # Default: parse as expression
        return self._parse_expr()

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

    def _parse_section(self) -> Section:
        """Parse section: === Title ==="""
        start_token = self._advance()  # Consume first '==='

        # Collect title text (all identifiers until closing ===)
        title_parts: list[str] = []
        while not self._match(TokenType.SECTION_MARKER) and not self._at_end():
            if self._match(TokenType.NEWLINE):
                break  # Section title on one line
            title_parts.append(self._current().value)
            self._advance()

        if not self._match(TokenType.SECTION_MARKER):
            raise ParserError("Expected closing '===' for section", self._current())

        self._advance()  # Consume closing '==='
        title = " ".join(title_parts)
        self._skip_newlines()

        # Parse section content until next section or end
        items: list[DocumentItem] = []
        while not self._at_end() and not self._match(TokenType.SECTION_MARKER):
            items.append(self._parse_document_item())
            self._skip_newlines()

        return Section(
            title=title, items=items, line=start_token.line, column=start_token.column
        )

    def _parse_solution(self) -> Solution:
        """Parse solution: ** Solution N **"""
        start_token = self._advance()  # Consume first '**'

        # Collect solution number/text (all tokens until closing **)
        solution_parts: list[str] = []
        while not self._match(TokenType.SOLUTION_MARKER) and not self._at_end():
            if self._match(TokenType.NEWLINE):
                break  # Solution marker on one line
            solution_parts.append(self._current().value)
            self._advance()

        if not self._match(TokenType.SOLUTION_MARKER):
            raise ParserError("Expected closing '**' for solution", self._current())

        self._advance()  # Consume closing '**'
        number = " ".join(solution_parts)
        self._skip_newlines()

        # Parse solution content until next solution/section or end
        items: list[DocumentItem] = []
        while not self._at_end() and not self._match(
            TokenType.SOLUTION_MARKER, TokenType.SECTION_MARKER
        ):
            items.append(self._parse_document_item())
            self._skip_newlines()

        return Solution(
            number=number, items=items, line=start_token.line, column=start_token.column
        )

    def _parse_part(self) -> Part:
        """Parse part: (a) content"""
        part_token = self._advance()  # Consume '(a)', '(b)', etc.

        # Extract label from token value: "(a)" -> "a"
        label = part_token.value[1:-1]
        self._skip_newlines()

        # Parse part content until next part/solution/section or end
        items: list[DocumentItem] = []
        while not self._at_end() and not self._match(
            TokenType.PART_LABEL,
            TokenType.SOLUTION_MARKER,
            TokenType.SECTION_MARKER,
        ):
            items.append(self._parse_document_item())
            self._skip_newlines()

        return Part(
            label=label, items=items, line=part_token.line, column=part_token.column
        )

    def _parse_truth_table(self) -> TruthTable:
        """Parse truth table: TRUTH TABLE: followed by table rows."""
        start_token = self._advance()  # Consume 'TRUTH TABLE:'
        self._skip_newlines()

        # Parse header row (columns separated by |)
        headers: list[str] = []
        if not self._match(TokenType.IDENTIFIER):
            raise ParserError("Expected truth table header row", self._current())

        # Collect columns (tokens between pipes)
        column_tokens: list[str] = []
        while not self._match(TokenType.NEWLINE) and not self._at_end():
            if self._match(TokenType.PIPE):
                # Save current column
                if column_tokens:
                    headers.append(" ".join(column_tokens))
                    column_tokens = []
                self._advance()  # Skip pipe
            elif self._match(
                TokenType.IDENTIFIER,
                TokenType.AND,
                TokenType.OR,
                TokenType.NOT,
                TokenType.IMPLIES,
                TokenType.IFF,
                TokenType.LPAREN,
                TokenType.RPAREN,
            ):
                column_tokens.append(self._current().value)
                self._advance()
            else:
                break

        # Add last column
        if column_tokens:
            headers.append(" ".join(column_tokens))

        if not headers:
            raise ParserError("Expected truth table headers", self._current())

        self._skip_newlines()

        # Parse data rows
        rows: list[list[str]] = []
        while not self._at_end() and not self._is_structural_token():
            row: list[str] = []

            # Check if line starts with T/t or F/f (truth values)
            if not self._match(TokenType.IDENTIFIER):
                break

            first_val = self._current().value
            if first_val.upper() not in ("T", "F"):
                break  # Not a truth table row

            # Collect row values separated by pipes, normalizing to uppercase
            while not self._match(TokenType.NEWLINE) and not self._at_end():
                if self._match(TokenType.PIPE):
                    self._advance()  # Skip pipe
                elif self._match(TokenType.IDENTIFIER):
                    val = self._current().value
                    # Normalize t/f to T/F
                    row.append(val.upper() if val.upper() in ("T", "F") else val)
                    self._advance()
                else:
                    break

            if row:
                rows.append(row)
            self._skip_newlines()

        return TruthTable(
            headers=headers,
            rows=rows,
            line=start_token.line,
            column=start_token.column,
        )

    def _parse_equiv_chain(self) -> EquivChain:
        """Parse equivalence chain: EQUIV: followed by steps."""
        start_token = self._advance()  # Consume 'EQUIV:'
        self._skip_newlines()

        steps: list[EquivStep] = []

        # Parse steps until we hit another structural element or end
        while not self._at_end() and not self._is_structural_token():
            # Consume leading <=> if present (for continuation lines)
            if self._match(TokenType.IFF):
                self._advance()  # Consume '<='

            # Parse expression
            expr = self._parse_expr()
            self._skip_newlines()

            # Check for optional justification [text]
            justification: str | None = None
            if self._match(TokenType.LBRACKET):
                self._advance()  # Consume '['

                # Collect justification text (all tokens until ']')
                just_parts: list[str] = []
                while not self._match(TokenType.RBRACKET) and not self._at_end():
                    if self._match(TokenType.NEWLINE):
                        break  # Justification on one line
                    just_parts.append(self._current().value)
                    self._advance()

                if not self._match(TokenType.RBRACKET):
                    raise ParserError(
                        "Expected closing ']' for justification", self._current()
                    )

                self._advance()  # Consume ']'
                justification = " ".join(just_parts)

            # Create step
            steps.append(
                EquivStep(
                    expression=expr,
                    justification=justification,
                    line=expr.line,
                    column=expr.column,
                )
            )

            self._skip_newlines()

        if not steps:
            raise ParserError(
                "Expected at least one step in EQUIV chain", self._current()
            )

        return EquivChain(steps=steps, line=start_token.line, column=start_token.column)

    def _parse_expr(self) -> Expr:
        """Parse expression (entry point)."""
        # Check for quantifier first (Phase 3, enhanced in Phase 6-7)
        if self._match(
            TokenType.FORALL, TokenType.EXISTS, TokenType.EXISTS1, TokenType.MU
        ):
            return self._parse_quantifier()
        return self._parse_iff()

    def _parse_iff(self) -> Expr:
        """Parse iff operation (<=>), lowest precedence."""
        left = self._parse_implies()

        while self._match(TokenType.IFF):
            op_token = self._advance()
            right = self._parse_implies()
            left = BinaryOp(
                operator=op_token.value,
                left=left,
                right=right,
                line=op_token.line,
                column=op_token.column,
            )

        return left

    def _parse_implies(self) -> Expr:
        """Parse implies operation (=>)."""
        left = self._parse_or()

        while self._match(TokenType.IMPLIES):
            op_token = self._advance()
            right = self._parse_or()
            left = BinaryOp(
                operator=op_token.value,
                left=left,
                right=right,
                line=op_token.line,
                column=op_token.column,
            )

        return left

    def _parse_or(self) -> Expr:
        """Parse or operation."""
        left = self._parse_and()

        while self._match(TokenType.OR):
            op_token = self._advance()
            right = self._parse_and()
            left = BinaryOp(
                operator=op_token.value,
                left=left,
                right=right,
                line=op_token.line,
                column=op_token.column,
            )

        return left

    def _parse_and(self) -> Expr:
        """Parse and operation."""
        left = self._parse_comparison()

        while self._match(TokenType.AND):
            op_token = self._advance()
            right = self._parse_comparison()
            left = BinaryOp(
                operator=op_token.value,
                left=left,
                right=right,
                line=op_token.line,
                column=op_token.column,
            )

        return left

    def _parse_unary(self) -> Expr:
        """Parse unary operation (not)."""
        if self._match(TokenType.NOT):
            op_token = self._advance()
            operand = self._parse_unary()
            return UnaryOp(
                operator=op_token.value,
                operand=operand,
                line=op_token.line,
                column=op_token.column,
            )

        return self._parse_postfix()

    def _parse_quantifier(self) -> Expr:
        """Parse quantifier: (forall|exists|exists1|mu) var [, var]* : domain | body.

        Phase 6 enhancement: Supports multiple variables with shared domain.
        Phase 7 enhancement: Supports mu-operator (definite description).
        Examples:
        - forall x : N | pred
        - forall x, y : N | pred
        - exists1 x : N | pred
        - mu x : N | pred (single variable only)
        """
        quant_token = self._advance()  # Consume 'forall', 'exists', 'exists1', or 'mu'

        # Parse first variable
        if not self._match(TokenType.IDENTIFIER):
            raise ParserError(
                f"Expected variable name after {quant_token.value}", self._current()
            )
        variables: list[str] = [self._advance().value]

        # Parse additional variables if comma-separated
        while self._match(TokenType.COMMA):
            self._advance()  # Consume ','
            if not self._match(TokenType.IDENTIFIER):
                raise ParserError("Expected variable name after ','", self._current())
            variables.append(self._advance().value)

        # Parse optional domain (: domain)
        domain: Expr | None = None
        if self._match(TokenType.COLON):
            self._advance()  # Consume ':'
            domain = self._parse_atom()

        # Parse separator |
        if not self._match(TokenType.PIPE):
            raise ParserError("Expected '|' after quantifier binding", self._current())
        self._advance()  # Consume '|'

        # Parse body (rest of expression)
        body = self._parse_expr()

        return Quantifier(
            quantifier=quant_token.value,
            variables=variables,
            domain=domain,
            body=body,
            line=quant_token.line,
            column=quant_token.column,
        )

    def _parse_set_comprehension(self) -> Expr:
        """Parse set comprehension.

        Syntax: { var [, var]* : domain | predicate [. expression] }.

        Phase 8: Set comprehension support.
        Examples:
        - { x : N | x > 0 }  (set by predicate)
        - { x : N | x > 0 . x^2 }  (set by expression)
        - { x, y : N | x + y = 4 }  (multi-variable)
        - { x | x in A }  (no domain)
        """
        start_token = self._advance()  # Consume '{'

        # Parse first variable
        if not self._match(TokenType.IDENTIFIER):
            raise ParserError(
                "Expected variable name in set comprehension", self._current()
            )
        variables: list[str] = [self._advance().value]

        # Parse additional variables if comma-separated
        while self._match(TokenType.COMMA):
            self._advance()  # Consume ','
            if not self._match(TokenType.IDENTIFIER):
                raise ParserError("Expected variable name after ','", self._current())
            variables.append(self._advance().value)

        # Parse optional domain (: domain)
        domain: Expr | None = None
        if self._match(TokenType.COLON):
            self._advance()  # Consume ':'
            # Parse domain as atom (could be identifier like N, or more complex)
            domain = self._parse_atom()

        # Parse separator |
        if not self._match(TokenType.PIPE):
            raise ParserError(
                "Expected '|' after set comprehension binding", self._current()
            )
        self._advance()  # Consume '|'

        # Parse predicate expression (up to . or })
        # We need to be careful not to consume . as part of the predicate
        # Strategy: parse expression normally, then check for . or }
        predicate = self._parse_set_predicate()

        # Parse optional expression part (. expression)
        expression: Expr | None = None
        if self._match(TokenType.PERIOD):
            self._advance()  # Consume '.'
            # Parse expression (up to })
            expression = self._parse_set_expression()

        # Expect closing brace
        if not self._match(TokenType.RBRACE):
            raise ParserError(
                "Expected '}' to close set comprehension", self._current()
            )
        self._advance()  # Consume '}'

        return SetComprehension(
            variables=variables,
            domain=domain,
            predicate=predicate,
            expression=expression,
            line=start_token.line,
            column=start_token.column,
        )

    def _parse_set_predicate(self) -> Expr:
        """Parse predicate in set comprehension (up to . or })."""
        # Parse expression, but stop at PERIOD or RBRACE
        # This is tricky because we need to parse a full expression
        # but stop before . or }
        # For now, use the standard expression parser but be aware of context
        return self._parse_iff()

    def _parse_set_expression(self) -> Expr:
        """Parse expression in set comprehension (after . and up to })."""
        # Parse expression up to }
        return self._parse_iff()

    def _parse_comparison(self) -> Expr:
        """Parse comparison operators (<, >, <=, >=, =, !=)."""
        left = self._parse_relation()

        if self._match(
            TokenType.LESS_THAN,
            TokenType.GREATER_THAN,
            TokenType.LESS_EQUAL,
            TokenType.GREATER_EQUAL,
            TokenType.EQUALS,
            TokenType.NOT_EQUAL,
        ):
            op_token = self._advance()
            right = self._parse_relation()
            left = BinaryOp(
                operator=op_token.value,
                left=left,
                right=right,
                line=op_token.line,
                column=op_token.column,
            )

        return left

    def _parse_relation(self) -> Expr:
        """Parse relation operators (Phase 10a-b).

        Phase 10a: <->, |->, <|, |>, comp, ;
        Phase 10b: <<|, |>>, o9
        """
        left = self._parse_set_op()

        # Phase 10a-b: Infix relation operators (left-associative)
        while self._match(
            TokenType.RELATION,  # <->
            TokenType.MAPLET,  # |->
            TokenType.DRES,  # <|
            TokenType.RRES,  # |>
            TokenType.NDRES,  # <<| (Phase 10b)
            TokenType.NRRES,  # |>> (Phase 10b)
            TokenType.CIRC,  # o9 (Phase 10b)
            TokenType.COMP,  # comp
            TokenType.SEMICOLON,  # ;
        ):
            op_token = self._advance()
            right = self._parse_set_op()
            left = BinaryOp(
                operator=op_token.value,
                left=left,
                right=right,
                line=op_token.line,
                column=op_token.column,
            )

        return left

    def _parse_set_op(self) -> Expr:
        """Parse set operators (in, notin, subset)."""
        left = self._parse_union()

        if self._match(TokenType.IN, TokenType.NOTIN, TokenType.SUBSET):
            op_token = self._advance()
            right = self._parse_union()
            left = BinaryOp(
                operator=op_token.value,
                left=left,
                right=right,
                line=op_token.line,
                column=op_token.column,
            )

        return left

    def _parse_union(self) -> Expr:
        """Parse union operator."""
        left = self._parse_intersect()

        while self._match(TokenType.UNION):
            op_token = self._advance()
            right = self._parse_intersect()
            left = BinaryOp(
                operator=op_token.value,
                left=left,
                right=right,
                line=op_token.line,
                column=op_token.column,
            )

        return left

    def _parse_intersect(self) -> Expr:
        """Parse intersect operator."""
        left = self._parse_unary()

        while self._match(TokenType.INTERSECT):
            op_token = self._advance()
            right = self._parse_unary()
            left = BinaryOp(
                operator=op_token.value,
                left=left,
                right=right,
                line=op_token.line,
                column=op_token.column,
            )

        return left

    def _parse_postfix(self) -> Expr:
        """Parse postfix operators.

        Phase 3: ^ (superscript), _ (subscript) - take operands
        Phase 10b: ~ (inverse), + (transitive closure),
                   * (reflexive-transitive closure) - no operands
        """
        base = self._parse_atom()

        # Keep applying postfix operators while we see them
        while self._match(
            TokenType.CARET,
            TokenType.UNDERSCORE,
            TokenType.TILDE,
            TokenType.PLUS,
            TokenType.STAR,
        ):
            op_token = self._advance()

            if op_token.type == TokenType.CARET:
                # Superscript takes an operand
                operand = self._parse_atom()
                base = Superscript(
                    base=base,
                    exponent=operand,
                    line=op_token.line,
                    column=op_token.column,
                )
            elif op_token.type == TokenType.UNDERSCORE:
                # Subscript takes an operand
                operand = self._parse_atom()
                base = Subscript(
                    base=base,
                    index=operand,
                    line=op_token.line,
                    column=op_token.column,
                )
            else:
                # Phase 10b: Unary postfix operators (no operand)
                base = UnaryOp(
                    operator=op_token.value,
                    operand=base,
                    line=op_token.line,
                    column=op_token.column,
                )

        return base

    def _parse_atom(self) -> Expr:
        """Parse atom.

        Handles: identifier, number, parenthesized expression, set comprehension,
        Phase 10a relation functions (dom, ran), and Phase 10b functions (inv, id).
        """
        # Phase 10a-b: Prefix relation functions (dom, ran, inv, id)
        if self._match(TokenType.DOM, TokenType.RAN, TokenType.INV, TokenType.ID):
            op_token = self._advance()
            operand = self._parse_atom()
            return UnaryOp(
                operator=op_token.value,
                operand=operand,
                line=op_token.line,
                column=op_token.column,
            )

        if self._match(TokenType.IDENTIFIER):
            token = self._advance()
            return Identifier(name=token.value, line=token.line, column=token.column)

        if self._match(TokenType.NUMBER):
            token = self._advance()
            return Number(value=token.value, line=token.line, column=token.column)

        if self._match(TokenType.LPAREN):
            self._advance()  # Consume '('
            expr = self._parse_expr()
            if not self._match(TokenType.RPAREN):
                raise ParserError("Expected ')' after expression", self._current())
            self._advance()  # Consume ')'
            return expr

        # Phase 8: Set comprehension { x : X | pred } or { x : X | pred . expr }
        if self._match(TokenType.LBRACE):
            return self._parse_set_comprehension()

        raise ParserError(
            f"Expected identifier, number, '(', or '{{',"
            f" got {self._current().type.name}",
            self._current(),
        )

    def _parse_given_type(self) -> GivenType:
        """Parse given type: given A, B, C"""
        start_token = self._advance()  # Consume 'given'

        names: list[str] = []

        # Parse comma-separated list of type names
        while not self._at_end() and not self._match(TokenType.NEWLINE):
            if self._match(TokenType.COMMA):
                self._advance()  # Skip comma
                continue

            if not self._match(TokenType.IDENTIFIER):
                raise ParserError(
                    "Expected type name in given declaration", self._current()
                )

            names.append(self._current().value)
            self._advance()

        if not names:
            raise ParserError(
                "Expected at least one type name in given declaration", self._current()
            )

        return GivenType(names=names, line=start_token.line, column=start_token.column)

    def _parse_free_type(self) -> FreeType:
        """Parse free type: Type ::= branch1 | branch2 | branch3"""
        # Identifier already consumed in _parse_document_item, need to back up
        name_token = self._current()
        type_name = name_token.value
        self._advance()  # Move to ::=

        if not self._match(TokenType.FREE_TYPE):
            raise ParserError("Expected '::=' in free type definition", self._current())
        self._advance()  # Consume '::='

        branches: list[str] = []

        # Parse pipe-separated list of branches
        while not self._at_end() and not self._match(TokenType.NEWLINE):
            if self._match(TokenType.IDENTIFIER):
                branches.append(self._current().value)
                self._advance()

            # Check for pipe separator
            if self._match(TokenType.PIPE):
                self._advance()
            elif not self._match(TokenType.NEWLINE) and not self._at_end():
                # Allow end of line or more branches
                pass

        if not branches:
            raise ParserError(
                "Expected at least one branch in free type definition", self._current()
            )

        return FreeType(
            name=type_name,
            branches=branches,
            line=name_token.line,
            column=name_token.column,
        )

    def _parse_generic_params(self) -> list[str] | None:
        """Parse optional generic parameters: [X, Y, Z].

        Phase 9: Generic parameter support for Z notation definitions.
        Returns None if no generic parameters present.
        """
        if not self._match(TokenType.LBRACKET):
            return None

        self._advance()  # Consume '['
        params: list[str] = []

        # Parse comma-separated list of type parameters
        while not self._match(TokenType.RBRACKET) and not self._at_end():
            if self._match(TokenType.COMMA):
                self._advance()  # Skip comma
                continue

            if not self._match(TokenType.IDENTIFIER):
                raise ParserError(
                    "Expected type parameter name in generic list", self._current()
                )

            params.append(self._current().value)
            self._advance()

        if not self._match(TokenType.RBRACKET):
            raise ParserError(
                "Expected ']' to close generic parameter list", self._current()
            )
        self._advance()  # Consume ']'

        return params if params else None

    def _parse_abbreviation(self) -> Abbreviation:
        """Parse abbreviation: [X] name == expression or name == expression.

        Phase 9 enhancement: Supports optional generic parameters.
        """
        start_token = self._current()

        # Check for generic parameters before name
        generic_params = self._parse_generic_params()

        # Parse name
        if not self._match(TokenType.IDENTIFIER):
            raise ParserError("Expected identifier in abbreviation", self._current())
        name_token = self._current()
        name = name_token.value
        self._advance()  # Move to ==

        if not self._match(TokenType.ABBREV):
            raise ParserError("Expected '==' in abbreviation", self._current())
        self._advance()  # Consume '=='

        # Parse expression
        expr = self._parse_expr()

        return Abbreviation(
            name=name,
            expression=expr,
            generic_params=generic_params,
            line=start_token.line if generic_params else name_token.line,
            column=start_token.column if generic_params else name_token.column,
        )

    def _parse_axdef(self) -> AxDef:
        """Parse axiomatic definition block.

        Phase 9 enhancement: Supports optional generic parameters.
        Syntax: axdef [X, Y] ... end
        """
        start_token = self._advance()  # Consume 'axdef'
        self._skip_newlines()

        # Check for generic parameters after 'axdef'
        generic_params = self._parse_generic_params()
        self._skip_newlines()

        declarations: list[Declaration] = []
        predicates: list[Expr] = []

        # Parse declarations until 'where' or 'end'
        while not self._at_end() and not self._match(TokenType.WHERE, TokenType.END):
            if self._match(TokenType.NEWLINE):
                self._advance()
                continue

            # Parse declaration: var : Type
            if self._match(TokenType.IDENTIFIER):
                var_token = self._current()
                var_name = var_token.value
                self._advance()

                if not self._match(TokenType.COLON):
                    raise ParserError("Expected ':' in declaration", self._current())
                self._advance()  # Consume ':'

                # Parse type expression
                type_expr = self._parse_expr()

                declarations.append(
                    Declaration(
                        variable=var_name,
                        type_expr=type_expr,
                        line=var_token.line,
                        column=var_token.column,
                    )
                )
                self._skip_newlines()
            else:
                break

        # Parse 'where' clause (optional)
        if self._match(TokenType.WHERE):
            self._advance()  # Consume 'where'
            self._skip_newlines()

            # Parse predicates until 'end'
            while not self._at_end() and not self._match(TokenType.END):
                if self._match(TokenType.NEWLINE):
                    self._advance()
                    continue

                predicates.append(self._parse_expr())
                self._skip_newlines()

        # Expect 'end'
        if not self._match(TokenType.END):
            raise ParserError("Expected 'end' to close axdef block", self._current())
        self._advance()  # Consume 'end'

        return AxDef(
            declarations=declarations,
            predicates=predicates,
            generic_params=generic_params,
            line=start_token.line,
            column=start_token.column,
        )

    def _parse_schema(self) -> Schema:
        """Parse schema definition block.

        Phase 9 enhancement: Supports optional generic parameters.
        Syntax: schema Name[X, Y] ... end or schema Name ... end
        """
        start_token = self._advance()  # Consume 'schema'

        # Parse schema name
        if not self._match(TokenType.IDENTIFIER):
            raise ParserError("Expected schema name", self._current())
        name = self._current().value
        self._advance()

        # Check for generic parameters after name
        generic_params = self._parse_generic_params()
        self._skip_newlines()

        declarations: list[Declaration] = []
        predicates: list[Expr] = []

        # Parse declarations until 'where' or 'end'
        while not self._at_end() and not self._match(TokenType.WHERE, TokenType.END):
            if self._match(TokenType.NEWLINE):
                self._advance()
                continue

            # Parse declaration: var : Type
            if self._match(TokenType.IDENTIFIER):
                var_token = self._current()
                var_name = var_token.value
                self._advance()

                if not self._match(TokenType.COLON):
                    raise ParserError("Expected ':' in declaration", self._current())
                self._advance()  # Consume ':'

                # Parse type expression
                type_expr = self._parse_expr()

                declarations.append(
                    Declaration(
                        variable=var_name,
                        type_expr=type_expr,
                        line=var_token.line,
                        column=var_token.column,
                    )
                )
                self._skip_newlines()
            else:
                break

        # Parse 'where' clause (optional)
        if self._match(TokenType.WHERE):
            self._advance()  # Consume 'where'
            self._skip_newlines()

            # Parse predicates until 'end'
            while not self._at_end() and not self._match(TokenType.END):
                if self._match(TokenType.NEWLINE):
                    self._advance()
                    continue

                predicates.append(self._parse_expr())
                self._skip_newlines()

        # Expect 'end'
        if not self._match(TokenType.END):
            raise ParserError("Expected 'end' to close schema block", self._current())
        self._advance()  # Consume 'end'

        return Schema(
            name=name,
            declarations=declarations,
            predicates=predicates,
            generic_params=generic_params,
            line=start_token.line,
            column=start_token.column,
        )

    def _parse_proof_tree(self) -> ProofTree:
        """Parse proof tree with Path C syntax (conclusion with supporting proof)."""
        start_token = self._advance()  # Consume 'PROOF:'
        self._skip_newlines()

        if self._at_end() or self._is_structural_token():
            raise ParserError("Expected proof node after PROOF:", self._current())

        # Parse the conclusion node (first top-level node)
        conclusion = self._parse_proof_node(base_indent=0, parent_indent=None)

        return ProofTree(
            conclusion=conclusion, line=start_token.line, column=start_token.column
        )

    def _parse_proof_node(
        self, base_indent: int, parent_indent: int | None
    ) -> ProofNode:
        """Parse a single proof node with Path C syntax."""
        if self._at_end() or self._is_structural_token():
            raise ParserError("Expected proof node", self._current())

        line_token = self._current()
        current_indent = line_token.column

        # If we've dedented past the parent level, stop
        if parent_indent is not None and current_indent <= parent_indent:
            raise ParserError("Unexpected dedent in proof tree", self._current())

        # Check for assumption label [1], [2], etc.
        label: int | None = None
        if self._match(TokenType.LBRACKET):
            self._advance()  # Consume '['
            if self._match(TokenType.NUMBER):
                label = int(self._current().value)
                self._advance()
                if not self._match(TokenType.RBRACKET):
                    raise ParserError(
                        "Expected ']' after assumption label", self._current()
                    )
                self._advance()  # Consume ']'
            else:
                # Not a label, must be justification - back up by recreating the bracket
                # Actually, we can't back up easily. Let's handle this differently.
                # For now, assume [number] is always a label at the start of a line.
                raise ParserError(
                    "Expected number in assumption label", self._current()
                )

        # Check for sibling marker ::
        is_sibling = False
        if self._match(TokenType.DOUBLE_COLON):
            is_sibling = True
            self._advance()  # Consume '::'

        # Parse the expression
        expr = self._parse_expr()

        # Check for justification [rule name]
        justification: str | None = None
        is_assumption = False
        if self._match(TokenType.LBRACKET):
            self._advance()  # Consume '['

            # Collect justification text
            just_parts: list[str] = []
            while not self._match(TokenType.RBRACKET) and not self._at_end():
                if self._match(TokenType.NEWLINE):
                    break
                just_parts.append(self._current().value)
                self._advance()

            if self._match(TokenType.RBRACKET):
                self._advance()  # Consume ']'
                justification = " ".join(just_parts)
                # Check if this is the [assumption] keyword
                if justification == "assumption":
                    is_assumption = True

        self._skip_newlines()

        # Parse children (nodes indented more than current)
        children: list[ProofNode | CaseAnalysis] = []
        while not self._at_end() and not self._is_structural_token():
            if self._match(TokenType.NEWLINE):
                self._skip_newlines()
                if self._at_end() or self._is_structural_token():
                    break

            next_token = self._current()
            next_indent = next_token.column

            # Check if still indented relative to current node
            if next_indent <= current_indent:
                break

            # Check for case analysis
            if self._match(TokenType.IDENTIFIER) and self._current().value == "case":
                case_analysis = self._parse_case_analysis(
                    base_indent=base_indent, parent_indent=current_indent
                )
                children.append(case_analysis)
            else:
                # Regular proof node
                child = self._parse_proof_node(
                    base_indent=base_indent, parent_indent=current_indent
                )
                children.append(child)

        return ProofNode(
            expression=expr,
            justification=justification,
            label=label,
            is_assumption=is_assumption,
            is_sibling=is_sibling,
            children=children,
            indent_level=current_indent - base_indent,
            line=line_token.line,
            column=line_token.column,
        )

    def _parse_case_analysis(
        self, base_indent: int, parent_indent: int
    ) -> CaseAnalysis:
        """Parse case analysis: case name: followed by proof steps."""
        if not self._match(TokenType.IDENTIFIER) or self._current().value != "case":
            raise ParserError("Expected 'case' keyword", self._current())

        case_token = self._advance()  # Consume 'case'

        # Parse case name - collect all tokens until colon
        case_parts: list[str] = []
        while not self._match(TokenType.COLON) and not self._at_end():
            if self._match(TokenType.NEWLINE):
                raise ParserError("Expected ':' after case name", self._current())
            case_parts.append(self._current().value)
            self._advance()

        if not case_parts:
            raise ParserError("Expected case name after 'case'", self._current())

        case_name = " ".join(case_parts)

        # Expect colon
        if not self._match(TokenType.COLON):
            raise ParserError("Expected ':' after case name", self._current())
        self._advance()  # Consume ':'

        self._skip_newlines()

        # Parse proof steps indented under this case
        steps: list[ProofNode] = []
        case_indent = case_token.column

        while not self._at_end() and not self._is_structural_token():
            if self._match(TokenType.NEWLINE):
                self._skip_newlines()
                if self._at_end() or self._is_structural_token():
                    break

            next_token = self._current()
            next_indent = next_token.column

            # Check if still indented relative to case
            if next_indent <= case_indent:
                break

            # Check if this is another case (sibling case)
            if self._match(TokenType.IDENTIFIER) and self._current().value == "case":
                break  # Stop parsing this case

            # Parse proof node for this case
            step = self._parse_proof_node(
                base_indent=base_indent, parent_indent=case_indent
            )
            steps.append(step)

        return CaseAnalysis(
            case_name=case_name,
            steps=steps,
            line=case_token.line,
            column=case_token.column,
        )
