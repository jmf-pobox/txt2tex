"""Parser for txt2tex - converts tokens into AST."""

from __future__ import annotations

from txt2tex.ast_nodes import (
    Abbreviation,
    AxDef,
    BinaryOp,
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
    Part,
    ProofNode,
    ProofTree,
    Quantifier,
    Schema,
    Section,
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
    Recursive descent parser for Phase 0 + Phase 1 + Phase 2 + Phase 3.

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

    Phase 3 - Quantifiers and mathematical notation:
        expr       ::= quantifier | iff
        quantifier ::= ('forall' | 'exists') IDENTIFIER ':' atom '|' expr
        iff        ::= implies ( '<=>' implies )*
        implies    ::= or ( '=>' or )*
        or         ::= and ( 'or' and )*
        and        ::= comparison ( 'and' comparison )*
        comparison ::= set_op ( ('<' | '>' | '<=' | '>=' | '=') set_op )?
        set_op     ::= union ( ('in' | 'subset') union )?
        union      ::= intersect ( 'union' intersect )*
        intersect  ::= unary ( 'intersect' unary )*
        unary      ::= 'not' unary | postfix
        postfix    ::= atom ( '^' atom | '_' atom )*
        atom       ::= IDENTIFIER | NUMBER | '(' expr ')'
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
            TokenType.EQUIV,
            TokenType.GIVEN,
            TokenType.AXDEF,
            TokenType.SCHEMA,
            TokenType.PROOF,
        )

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

        # Check for abbreviation (identifier == expr) or free type (identifier ::= ...)
        if self._match(TokenType.IDENTIFIER):
            # Look ahead to determine type
            if self._peek_ahead(1).type == TokenType.FREE_TYPE:
                return self._parse_free_type()
            if self._peek_ahead(1).type == TokenType.ABBREV:
                return self._parse_abbreviation()
            # Otherwise, fall through to expression parsing

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

            # Check if line starts with T or F (truth values)
            if not self._match(TokenType.IDENTIFIER):
                break

            first_val = self._current().value
            if first_val not in ("T", "F"):
                break  # Not a truth table row

            # Collect row values separated by pipes
            while not self._match(TokenType.NEWLINE) and not self._at_end():
                if self._match(TokenType.PIPE):
                    self._advance()  # Skip pipe
                elif self._match(TokenType.IDENTIFIER):
                    row.append(self._current().value)
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
        # Check for quantifier first (Phase 3)
        if self._match(TokenType.FORALL, TokenType.EXISTS):
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
        """Parse quantifier: (forall|exists) var : domain | body."""
        quant_token = self._advance()  # Consume 'forall' or 'exists'

        # Parse variable
        if not self._match(TokenType.IDENTIFIER):
            raise ParserError(
                f"Expected variable name after {quant_token.value}", self._current()
            )
        var_token = self._advance()

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
            variable=var_token.value,
            domain=domain,
            body=body,
            line=quant_token.line,
            column=quant_token.column,
        )

    def _parse_comparison(self) -> Expr:
        """Parse comparison operators (<, >, <=, >=, =)."""
        left = self._parse_set_op()

        if self._match(
            TokenType.LESS_THAN,
            TokenType.GREATER_THAN,
            TokenType.LESS_EQUAL,
            TokenType.GREATER_EQUAL,
            TokenType.EQUALS,
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
        """Parse set operators (in, subset)."""
        left = self._parse_union()

        if self._match(TokenType.IN, TokenType.SUBSET):
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
        """Parse postfix operators (^ for superscript, _ for subscript)."""
        base = self._parse_atom()

        # Keep applying postfix operators while we see them
        while self._match(TokenType.CARET, TokenType.UNDERSCORE):
            op_token = self._advance()
            operand = self._parse_atom()

            if op_token.type == TokenType.CARET:
                base = Superscript(
                    base=base,
                    exponent=operand,
                    line=op_token.line,
                    column=op_token.column,
                )
            else:  # UNDERSCORE
                base = Subscript(
                    base=base,
                    index=operand,
                    line=op_token.line,
                    column=op_token.column,
                )

        return base

    def _parse_atom(self) -> Expr:
        """Parse atom (identifier, number, or parenthesized expression)."""
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

        raise ParserError(
            f"Expected identifier, number, or '(', got {self._current().type.name}",
            self._current(),
        )

    def _parse_given_type(self) -> GivenType:
        """Parse given type: given A, B, C"""
        start_token = self._advance()  # Consume 'given'

        names: list[str] = []

        # Parse comma-separated list of type names
        while not self._at_end() and not self._match(TokenType.NEWLINE):
            if not self._match(TokenType.IDENTIFIER):
                raise ParserError(
                    "Expected type name in given declaration", self._current()
                )

            names.append(self._current().value)
            self._advance()

            # Check for comma
            if not self._match(TokenType.NEWLINE) and not self._at_end():
                # Expect comma (represented as identifier in current lexer)
                # Skip any whitespace/tokens until next identifier or newline
                pass

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

    def _parse_abbreviation(self) -> Abbreviation:
        """Parse abbreviation: name == expression"""
        name_token = self._current()
        name = name_token.value
        self._advance()  # Move to ==

        if not self._match(TokenType.ABBREV):
            raise ParserError("Expected '==' in abbreviation", self._current())
        self._advance()  # Consume '=='

        # Parse expression
        expr = self._parse_expr()

        return Abbreviation(
            name=name, expression=expr, line=name_token.line, column=name_token.column
        )

    def _parse_axdef(self) -> AxDef:
        """Parse axiomatic definition block."""
        start_token = self._advance()  # Consume 'axdef'
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
            line=start_token.line,
            column=start_token.column,
        )

    def _parse_schema(self) -> Schema:
        """Parse schema definition block."""
        start_token = self._advance()  # Consume 'schema'

        # Parse schema name
        if not self._match(TokenType.IDENTIFIER):
            raise ParserError("Expected schema name", self._current())
        name = self._current().value
        self._advance()
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
            line=start_token.line,
            column=start_token.column,
        )

    def _parse_proof_tree(self) -> ProofTree:
        """Parse proof tree with indentation-based structure."""
        start_token = self._advance()  # Consume 'PROOF:'
        self._skip_newlines()

        # Parse proof nodes with indentation tracking
        nodes = self._parse_proof_nodes(base_indent=0)

        return ProofTree(nodes=nodes, line=start_token.line, column=start_token.column)

    def _parse_proof_nodes(
        self, base_indent: int, parent_indent: int | None = None
    ) -> list[ProofNode]:
        """Parse proof nodes recursively based on indentation."""
        nodes: list[ProofNode] = []

        while not self._at_end() and not self._is_structural_token():
            if self._match(TokenType.NEWLINE):
                self._advance()
                continue

            # Get the indentation of this line (column of first token)
            current_indent = self._current().column

            # If we've dedented past the parent level, stop parsing at this level
            if parent_indent is not None and current_indent <= parent_indent:
                break

            # Parse the expression on this line
            line_token = self._current()
            expr = self._parse_expr()

            # Check for optional justification [rule name]
            justification: str | None = None
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

            self._skip_newlines()

            # Look ahead to see if the next line is more indented (children)
            children: list[ProofNode] = []
            if not self._at_end() and not self._is_structural_token():
                next_token = self._current()
                if next_token.type != TokenType.NEWLINE:
                    next_indent = next_token.column
                    if next_indent > current_indent:
                        # Parse children at this indentation level
                        children = self._parse_proof_nodes(
                            base_indent=base_indent, parent_indent=current_indent
                        )

            # Create proof node
            node = ProofNode(
                expression=expr,
                justification=justification,
                children=children,
                indent_level=current_indent - base_indent,
                line=line_token.line,
                column=line_token.column,
            )
            nodes.append(node)

        return nodes
