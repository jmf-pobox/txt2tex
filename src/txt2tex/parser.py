"""Parser for txt2tex - converts tokens into AST."""

from __future__ import annotations

import re

from txt2tex.ast_nodes import (
    Abbreviation,
    AxDef,
    BagLiteral,
    BinaryOp,
    CaseAnalysis,
    Conditional,
    Declaration,
    Document,
    DocumentItem,
    EquivChain,
    EquivStep,
    Expr,
    FreeBranch,
    FreeType,
    FunctionApp,
    FunctionType,
    GenDef,
    GenericInstantiation,
    GivenType,
    GuardedBranch,
    GuardedCases,
    Identifier,
    Lambda,
    LatexBlock,
    Number,
    PageBreak,
    Paragraph,
    Part,
    ProofNode,
    ProofTree,
    PureParagraph,
    Quantifier,
    Range,
    RelationalImage,
    Schema,
    Section,
    SequenceLiteral,
    SetComprehension,
    SetLiteral,
    Solution,
    Subscript,
    Superscript,
    TruthTable,
    Tuple,
    TupleProjection,
    UnaryOp,
    Zed,
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
    Recursive descent parser for Phase 0-4 + Phase 10a-b + Phase 11a.

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
                                  '|>>' | 'o9' | 'comp' | ';' |
                                  '->' | '+->' | '>->' | '>+>' |
                                  '-->>' | '+->>' | '>->>') set_op )*
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

    Phase 11a - Function type operators:
        - Infix: -> (total function), +-> (partial function),
                 >-> (total injection), >+> (partial injection),
                 -->> (total surjection), +->> (partial surjection),
                 >->> (bijection)
    """

    def __init__(self, tokens: list[Token]) -> None:
        """Initialize parser with token list."""
        self.tokens = tokens
        self.pos = 0
        # Track the end position of the last consumed token for whitespace detection
        self.last_token_end_column = 0
        self.last_token_line = 1
        # Track whether we're parsing schema text (lambda/set comp declarations)
        # where periods are separators, not projection operators
        self._parsing_schema_text = False
        # Track whether we're in a comprehension/quantifier body where
        # periods can be expression separators
        # ({ x : X | pred . expr } or mu x : X | pred . expr)
        self._in_comprehension_body = False

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
                # Parse free type and check for more items
                first_free_type = self._parse_free_type()
                self._skip_newlines()
                # Check if there are more items (multi-line document)
                if not self._at_end():
                    items_with_free: list[DocumentItem] = [first_free_type]
                    while not self._at_end():
                        items_with_free.append(self._parse_document_item())
                        self._skip_newlines()
                    return Document(items=items_with_free, line=first_line, column=1)
                # Single free type
                return Document(items=[first_free_type], line=first_line, column=1)
            if next_token.type == TokenType.ABBREV:
                # Parse abbreviation and check for more items
                first_abbrev = self._parse_abbreviation()
                self._skip_newlines()
                # Check if there are more items (multi-line document)
                if not self._at_end():
                    items_with_abbrev: list[DocumentItem] = [first_abbrev]
                    while not self._at_end():
                        items_with_abbrev.append(self._parse_document_item())
                        self._skip_newlines()
                    return Document(items=items_with_abbrev, line=first_line, column=1)
                # Single abbreviation
                return Document(items=[first_abbrev], line=first_line, column=1)

        # Check for abbreviation with generic parameters (Phase 9)
        # [X, Y] Name == expression
        # BUT: Phase 12 bag literals [[x]] start with [[ not [
        if self._match(TokenType.LBRACKET):
            # Check if this is a bag literal [[...]] or abbreviation [X, Y] Name ==
            next_token = self._peek_ahead(1)
            if next_token.type == TokenType.LBRACKET:
                # It's a bag literal - parse as expression
                first_item = self._parse_expr()
                # Single expression
                if not self._at_end():
                    raise ParserError(
                        f"Unexpected token after expression: {self._current().value!r}",
                        self._current(),
                    )
                return first_item
            # Parse abbreviation with generic parameters and check for more items
            first_generic_abbrev = self._parse_abbreviation()
            self._skip_newlines()
            # Check if there are more items (multi-line document)
            if not self._at_end():
                items_with_generic: list[DocumentItem] = [first_generic_abbrev]
                while not self._at_end():
                    items_with_generic.append(self._parse_document_item())
                    self._skip_newlines()
                return Document(items=items_with_generic, line=first_line, column=1)
            # Single abbreviation with generic parameters
            return Document(items=[first_generic_abbrev], line=first_line, column=1)

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
            TokenType.PURETEXT,
            TokenType.LATEX,
            TokenType.PAGEBREAK,
            TokenType.EQUIV,
            TokenType.GIVEN,
            TokenType.AXDEF,
            TokenType.GENDEF,
            TokenType.ZED,
            TokenType.SCHEMA,
            TokenType.PROOF,
        )

    def _parse_paragraph(self) -> Paragraph | Part:
        """Parse plain text paragraph from TEXT token.

        The TEXT token value contains the raw text content (no tokenization).
        If the text starts with a part label like "(a) content...",
        return a Part node containing a Paragraph instead.
        """
        text_token = self._advance()  # Consume TEXT token

        if text_token.type != TokenType.TEXT:
            raise ParserError("Expected TEXT token for paragraph", text_token)

        # The token value contains the raw text (already captured by lexer)
        text = text_token.value

        # Check if text starts with part label pattern: (letter) or (roman numeral)
        part_match = re.match(r"^\(([a-z]+|[ivxlcdm]+)\)\s+(.+)", text, re.IGNORECASE)
        if part_match:
            label = part_match.group(1)
            content = part_match.group(2)
            # Return a Part containing a Paragraph
            paragraph = Paragraph(
                text=content, line=text_token.line, column=text_token.column
            )
            return Part(
                label=label,
                items=[paragraph],
                line=text_token.line,
                column=text_token.column,
            )

        return Paragraph(text=text, line=text_token.line, column=text_token.column)

    def _parse_pure_paragraph(self) -> PureParagraph:
        """Parse pure text paragraph from PURETEXT token.

        PURETEXT: blocks contain raw text with NO processing:
        - No formula detection
        - No operator conversion
        - Only basic LaTeX escaping applied during generation
        """
        text_token = self._advance()  # Consume PURETEXT token
        if text_token.type != TokenType.PURETEXT:
            raise ParserError("Expected PURETEXT token for pure paragraph", text_token)

        # The token value contains the raw text (already captured by lexer)
        text = text_token.value

        return PureParagraph(text=text, line=text_token.line, column=text_token.column)

    def _parse_latex_block(self) -> LatexBlock:
        """Parse raw LaTeX block from LATEX token.

        LATEX: blocks contain raw LaTeX with NO escaping.
        The LaTeX is passed directly through to the output.
        """
        latex_token = self._advance()  # Consume LATEX token
        if latex_token.type != TokenType.LATEX:
            raise ParserError("Expected LATEX token for LaTeX block", latex_token)

        # The token value contains the raw LaTeX (already captured by lexer)
        latex = latex_token.value

        return LatexBlock(latex=latex, line=latex_token.line, column=latex_token.column)

    def _parse_pagebreak(self) -> PageBreak:
        """Parse page break from PAGEBREAK token.

        PAGEBREAK: inserts a page break in the PDF output.
        """
        pagebreak_token = self._advance()  # Consume PAGEBREAK token
        if pagebreak_token.type != TokenType.PAGEBREAK:
            raise ParserError("Expected PAGEBREAK token", pagebreak_token)

        return PageBreak(line=pagebreak_token.line, column=pagebreak_token.column)

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
        if self._match(TokenType.GENDEF):
            return self._parse_gendef()
        if self._match(TokenType.ZED):
            return self._parse_zed()
        if self._match(TokenType.SCHEMA):
            return self._parse_schema()
        if self._match(TokenType.PROOF):
            return self._parse_proof_tree()
        if self._match(TokenType.TEXT):
            return self._parse_paragraph()
        if self._match(TokenType.PURETEXT):
            return self._parse_pure_paragraph()
        if self._match(TokenType.LATEX):
            return self._parse_latex_block()
        if self._match(TokenType.PAGEBREAK):
            return self._parse_pagebreak()

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
        # BUT: Phase 12 bag literals [[x]] start with [[ not [
        if self._match(TokenType.LBRACKET):
            # Check if this is a bag literal [[...]] or abbreviation [X, Y] Name ==
            next_token = self._peek_ahead(1)
            if next_token.type == TokenType.LBRACKET:
                # It's a bag literal - parse as expression
                return self._parse_expr()
            # It's an abbreviation with generic parameters
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
            # Note: F may be lexed as FINSET, P as POWER (Phase 19)
            if not self._match(TokenType.IDENTIFIER, TokenType.FINSET, TokenType.POWER):
                break

            first_val = self._current().value
            if first_val.upper() not in ("T", "F", "P"):
                break  # Not a truth table row

            # Collect row values separated by pipes, normalizing to uppercase
            while not self._match(TokenType.NEWLINE) and not self._at_end():
                if self._match(TokenType.PIPE):
                    self._advance()  # Skip pipe
                elif self._match(
                    TokenType.IDENTIFIER, TokenType.FINSET, TokenType.POWER
                ):
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
        # Check for lambda expression (Phase 11d)
        if self._match(TokenType.LAMBDA):
            return self._parse_lambda()
        # Check for conditional expression (Phase 16)
        if self._match(TokenType.IF):
            return self._parse_conditional()
        return self._parse_iff()

    def _parse_conditional(self) -> Expr:
        """Parse conditional expression: if condition then expr1 else expr2.

        Phase 16: Conditional expressions.
        Examples:
        - if x > 0 then x else -x
        - if s = <> then 0 else head s
        - if x > 0 then 1 else if x < 0 then -1 else 0 (nested)

        The condition is parsed with _parse_iff() (no quantifiers/lambdas/conditionals),
        but the then/else branches use _parse_expr() to allow nested conditionals.
        """
        if_token = self._advance()  # Consume 'if'

        # Parse condition (up to 'then') - no quantifiers/lambdas/conditionals
        condition = self._parse_iff()

        # Expect 'then'
        if not self._match(TokenType.THEN):
            raise ParserError("Expected 'then' after if condition", self._current())
        self._advance()  # Consume 'then'

        # Parse then branch - allow nested conditionals
        then_expr = self._parse_expr()

        # Expect 'else'
        if not self._match(TokenType.ELSE):
            raise ParserError("Expected 'else' after then expression", self._current())
        self._advance()  # Consume 'else'

        # Parse else branch - allow nested conditionals
        else_expr = self._parse_expr()

        return Conditional(
            condition=condition,
            then_expr=then_expr,
            else_expr=else_expr,
            line=if_token.line,
            column=if_token.column,
        )

    def _parse_iff(self) -> Expr:
        """Parse iff operation (<=>), lowest precedence."""
        left = self._parse_implies()

        while self._match(TokenType.IFF):
            op_token = self._advance()
            # Phase 27: Check for continuation marker (\ at end of line)
            has_continuation = False
            if self._match(TokenType.CONTINUATION):
                self._advance()  # consume \
                has_continuation = True
                # Skip newline and any leading whitespace on next line
                if self._match(TokenType.NEWLINE):
                    self._advance()
                self._skip_newlines()
            right = self._parse_implies()
            left = BinaryOp(
                operator=op_token.value,
                left=left,
                right=right,
                line_break_after=has_continuation,
                line=op_token.line,
                column=op_token.column,
            )

        return left

    def _parse_implies(self) -> Expr:
        """Parse implies operation (=>).

        Right side can be a quantifier to support patterns like:
        exists d : Dog | gentle(d) => forall t : Trainer | groomed(d, t)
        """
        left = self._parse_or()

        while self._match(TokenType.IMPLIES):
            op_token = self._advance()
            # Phase 27: Check for continuation marker (\ at end of line)
            has_continuation = False
            if self._match(TokenType.CONTINUATION):
                self._advance()  # consume \
                has_continuation = True
                # Skip newline and any leading whitespace on next line
                if self._match(TokenType.NEWLINE):
                    self._advance()
                self._skip_newlines()
            # Use _parse_expr() to allow quantifiers on RHS
            right = self._parse_expr()
            left = BinaryOp(
                operator=op_token.value,
                left=left,
                right=right,
                line_break_after=has_continuation,
                line=op_token.line,
                column=op_token.column,
            )

        return left

    def _parse_or(self) -> Expr:
        """Parse or operation."""
        left = self._parse_and()

        while self._match(TokenType.OR):
            op_token = self._advance()
            # Phase 27: Check for continuation marker (\ at end of line)
            has_continuation = False
            if self._match(TokenType.CONTINUATION):
                self._advance()  # consume \
                has_continuation = True
                # Skip newline and any leading whitespace on next line
                if self._match(TokenType.NEWLINE):
                    self._advance()
                self._skip_newlines()
            right = self._parse_and()
            left = BinaryOp(
                operator=op_token.value,
                left=left,
                right=right,
                line_break_after=has_continuation,
                line=op_token.line,
                column=op_token.column,
            )

        return left

    def _parse_and(self) -> Expr:
        """Parse and operation."""
        left = self._parse_comparison()

        while self._match(TokenType.AND):
            op_token = self._advance()
            # Phase 27: Check for continuation marker (\ at end of line)
            has_continuation = False
            if self._match(TokenType.CONTINUATION):
                self._advance()  # consume \
                has_continuation = True
                # Skip newline and any leading whitespace on next line
                if self._match(TokenType.NEWLINE):
                    self._advance()
                self._skip_newlines()
            # Phase 21c: Allow quantifiers after 'and'
            # Check if next token is a quantifier keyword
            if self._match(
                TokenType.FORALL, TokenType.EXISTS, TokenType.EXISTS1, TokenType.MU
            ):
                right = self._parse_quantifier()
            else:
                right = self._parse_comparison()
            left = BinaryOp(
                operator=op_token.value,
                left=left,
                right=right,
                line_break_after=has_continuation,
                line=op_token.line,
                column=op_token.column,
            )

        return left

    def _parse_unary(self) -> Expr:
        """Parse unary operation (not, #, -).

        Phase 8 enhancement: Added cardinality operator (#) as prefix unary.
        Phase 16 enhancement: Added negation operator (-) as prefix unary.
        """
        if self._match(TokenType.NOT):
            op_token = self._advance()
            operand = self._parse_unary()
            return UnaryOp(
                operator=op_token.value,
                operand=operand,
                line=op_token.line,
                column=op_token.column,
            )

        # Cardinality operator (Phase 8)
        if self._match(TokenType.HASH):
            op_token = self._advance()
            operand = self._parse_unary()
            return UnaryOp(
                operator=op_token.value,
                operand=operand,
                line=op_token.line,
                column=op_token.column,
            )

        # Unary negation (Phase 16)
        if self._match(TokenType.MINUS):
            op_token = self._advance()
            operand = self._parse_unary()
            return UnaryOp(
                operator=op_token.value,
                operand=operand,
                line=op_token.line,
                column=op_token.column,
            )

        return self._parse_range()

    def _parse_additive(self) -> Expr:
        """Parse additive operators (+ and - and ⌢).

        Arithmetic operators: + (addition), - (subtraction)
        Sequence operator: ⌢ (concatenation) - Phase 12
        Note: + can also be postfix (transitive closure R+), handled by lookahead
        """
        left = self._parse_multiplicative()

        while self._match(TokenType.PLUS, TokenType.MINUS, TokenType.CAT):
            # Lookahead for +: only treat as infix if followed by operand
            # CAT (⌢) and MINUS are always infix, no ambiguity
            if self._match(TokenType.PLUS) and not self._is_operand_start():
                break
            op_token = self._advance()
            right = self._parse_multiplicative()
            left = BinaryOp(
                operator=op_token.value,
                left=left,
                right=right,
                line=op_token.line,
                column=op_token.column,
            )

        return left

    def _parse_range(self) -> Expr:
        """Parse range operator .. (Phase 13).

        Creates integer ranges: m..n represents {m, m+1, m+2, ..., n}
        Range has lower precedence than addition, so 1+2..3+4 means (1+2)..(3+4)
        Examples: 1..10, 1993..current, x.2..x.3
        """
        left = self._parse_additive()

        if self._match(TokenType.RANGE):
            op_token = self._advance()
            right = self._parse_additive()
            return Range(
                start=left,
                end=right,
                line=op_token.line,
                column=op_token.column,
            )

        return left

    def _parse_multiplicative(self) -> Expr:
        """Parse multiplicative operators (*, /, mod).

        Arithmetic operators: * (multiplication), / (division), mod (modulo)
        Note: * can also be postfix (reflexive-transitive closure R*),
        handled by lookahead
        """
        left = self._parse_postfix()

        while self._match(TokenType.STAR, TokenType.MOD):
            # Lookahead for *: only treat as infix if followed by operand
            if self._match(TokenType.STAR) and not self._is_operand_start():
                break
            op_token = self._advance()
            right = self._parse_postfix()
            left = BinaryOp(
                operator=op_token.value,
                left=left,
                right=right,
                line=op_token.line,
                column=op_token.column,
            )

        return left

    def _is_operand_start(self) -> bool:
        """Check if next token could start an operand expression.

        Used for lookahead to disambiguate postfix +/* from infix +/*.
        Checks the NEXT token, not the current one.

        Phase 16 enhancement: Added IF (conditional) and MINUS (unary negation)
        """
        next_token = self._peek_ahead(1)
        return next_token.type in (
            TokenType.IDENTIFIER,
            TokenType.NUMBER,
            TokenType.LPAREN,
            TokenType.LBRACE,
            TokenType.LBRACKET,
            TokenType.NOT,
            TokenType.HASH,
            TokenType.MINUS,  # Phase 16: unary negation
            TokenType.POWER,
            TokenType.POWER1,
            TokenType.FINSET,  # Phase 19: finite sets
            TokenType.FINSET1,  # Phase 19: non-empty finite sets
            TokenType.FORALL,
            TokenType.EXISTS,
            TokenType.EXISTS1,
            TokenType.MU,
            TokenType.LAMBDA,
            TokenType.IF,  # Phase 16: conditional expressions
        )

    def _should_parse_space_separated_arg(self) -> bool:
        """Check if we should parse next token as space-separated function argument.

        Phase 19: Space-separated application (f x).
        Returns True if next token could start an operand and we're not at
        a delimiter, separator, or infix operator.
        """
        # At end of input
        if self._at_end():
            return False

        current = self._current()

        # Reject common English prose words to avoid parsing text as math
        # This prevents "x >= 0 is true" from being parsed as function applications
        if current.type == TokenType.IDENTIFIER:
            prose_words = {
                "is",
                "are",
                "be",
                "was",
                "were",
                "true",
                "false",
                "the",
                "a",
                "an",
                "to",
                "of",
                "for",
                "with",
                "as",
                "by",
                "from",
                "that",
                "this",
                "these",
                "those",
                "it",
                "its",
                "they",
                "them",
                "syntax",
                "valid",
                "here",
                "there",
            }
            if current.value.lower() in prose_words:
                return False

        # Stop at delimiters
        if current.type in (
            TokenType.RPAREN,
            TokenType.RBRACE,
            TokenType.RBRACKET,
            TokenType.RANGLE,
            TokenType.COMMA,
        ):
            return False

        # Stop at separators
        if current.type in (
            TokenType.NEWLINE,
            TokenType.SEMICOLON,
            TokenType.PIPE,
        ):
            return False

        # Stop at keywords that end expressions
        if current.type in (
            TokenType.WHERE,
            TokenType.END,
            TokenType.THEN,
            TokenType.ELSE,
            TokenType.AND,
            TokenType.OR,
        ):
            return False

        # Stop at infix operators
        if current.type in (
            TokenType.PLUS,
            TokenType.MINUS,
            TokenType.STAR,
            TokenType.MOD,
            TokenType.CAT,  # ⌢ concatenation
            TokenType.RANGE,  # ..
            TokenType.EQUALS,
            TokenType.NOT_EQUAL,
            TokenType.LESS_THAN,
            TokenType.GREATER_THAN,
            TokenType.LESS_EQUAL,
            TokenType.GREATER_EQUAL,
            TokenType.IN,
            TokenType.NOTIN,
            TokenType.SUBSET,
            TokenType.UNION,
            TokenType.INTERSECT,
            TokenType.SETMINUS,  # \ set difference
            TokenType.CROSS,  # x cross product
            TokenType.OVERRIDE,  # ++ override
            TokenType.RELATION,  # <->
            TokenType.MAPLET,  # |->
            TokenType.DRES,  # <|
            TokenType.RRES,  # |>
            TokenType.NDRES,  # <<|
            TokenType.NRRES,  # |>>
            TokenType.CIRC,  # o9
            TokenType.COMP,  # comp
            TokenType.TFUN,  # ->
            TokenType.PFUN,  # +->
            TokenType.TINJ,  # >->
            TokenType.PINJ,  # >+>
            TokenType.PINJ_ALT,  # -|>
            TokenType.TSURJ,  # -->>
            TokenType.PSURJ,  # +->>
            TokenType.BIJECTION,  # >->>
            TokenType.IMPLIES,  # =>
            TokenType.IFF,  # <=>
        ):
            return False

        # Check if current token could start an operand
        return current.type in (
            TokenType.IDENTIFIER,
            TokenType.NUMBER,
            TokenType.LPAREN,
            TokenType.LBRACE,
            TokenType.LANGLE,
            TokenType.NOT,
            TokenType.HASH,
            TokenType.DOM,
            TokenType.RAN,
            TokenType.INV,
            TokenType.ID,
            TokenType.POWER,
            TokenType.POWER1,
            TokenType.FINSET,
            TokenType.FINSET1,
            TokenType.BIGCUP,
            TokenType.HEAD,
            TokenType.TAIL,
            TokenType.LAST,
            TokenType.FRONT,
            TokenType.REV,
            TokenType.LAMBDA,
            TokenType.IF,
        )

    def _parse_quantifier(self) -> Expr:
        """Parse quantifier: (forall|exists|exists1|mu) var [, var]* : domain | body.

        Phase 6 enhancement: Supports multiple variables with shared domain.
        Phase 7 enhancement: Supports mu-operator (definite description).
        Phase 11.5 enhancement: Supports mu with expression part (mu x : X | P . E).
        Phase 17: Supports semicolon-separated bindings (x : T; y : U).
        Examples:
        - forall x : N | pred
        - forall x, y : N | pred
        - forall x : T; y : U | pred (Phase 17: nested quantifiers)
        - exists1 x : N | pred
        - mu x : N | pred
        - mu x : N | pred . expr (Phase 11.5)
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
            # Phase 21/22: Use _parse_union to allow union/intersect in domain
            # Allows: forall x : A union B | P
            # TODO Phase 23: Support relation types (A <-> B) in quantifier domains
            # Set flag to prevent .identifier from being parsed as projection
            self._parsing_schema_text = True
            try:
                domain = self._parse_union()
            finally:
                self._parsing_schema_text = False

        # Phase 17: Check for semicolon-separated bindings
        # If we see SEMICOLON, we have more binding groups: x : T; y : U | body
        # Transform into nested quantifiers: Q x : T | Q y : U | body
        if self._match(TokenType.SEMICOLON):
            self._advance()  # Consume ';'

            # Recursively parse remaining quantifiers (same quantifier type)
            # We need to temporarily create a token for the nested quantifier
            # Save position for nested quantifier
            nested_line = self._current().line
            nested_column = self._current().column

            # Parse the rest as if it were a new quantifier of the same type
            # This will handle: y : U | body or y : U; z : V | body
            nested_quant = self._parse_quantifier_continuation(
                quant_token.value, nested_line, nested_column
            )

            # Now wrap the nested quantifier as the body of this quantifier
            return Quantifier(
                quantifier=quant_token.value,
                variables=variables,
                domain=domain,
                body=nested_quant,
                expression=None,
                line=quant_token.line,
                column=quant_token.column,
            )

        # Parse separator |
        if not self._match(TokenType.PIPE):
            raise ParserError("Expected '|' after quantifier binding", self._current())
        self._advance()  # Consume '|'

        # Phase 27: Check for continuation marker (\ at end of line)
        has_continuation = False
        if self._match(TokenType.CONTINUATION):
            self._advance()  # consume \
            has_continuation = True
            # Skip newline and any leading whitespace on next line
            if self._match(TokenType.NEWLINE):
                self._advance()

        # Phase 21: Allow newlines after | (multi-line quantifiers)
        self._skip_newlines()

        # Set flag: we're in quantifier body where . can be separator (for mu)
        self._in_comprehension_body = True
        try:
            # Parse body
            # Phase 21: Use _parse_expr() to allow nested quantifiers
            # Phase 21b: Check for constrained quantifier
            # (forall x : T | constraint | body)
            # Parse first expression (constraint or full body)
            body = self._parse_expr()

            # Phase 21b: Check for second pipe (constrained quantifier)
            # Syntax: forall x : T | constraint | body
            # Semantics: forall x : T | constraint and body
            if self._match(TokenType.PIPE):
                self._advance()  # Consume second '|'

                # Phase 27: Check for continuation marker after second pipe
                constraint_continuation = False
                if self._match(TokenType.CONTINUATION):
                    self._advance()  # consume \
                    constraint_continuation = True
                    # Skip newline and any leading whitespace on next line
                    if self._match(TokenType.NEWLINE):
                        self._advance()
                    self._skip_newlines()

                constraint = body
                actual_body = self._parse_expr()
                # Combine constraint and body with AND
                body = BinaryOp(
                    operator="and",
                    left=constraint,
                    right=actual_body,
                    line_break_after=constraint_continuation,
                    line=constraint.line,
                    column=constraint.column,
                )

            # Phase 11.5: Check for optional expression part (mu only)
            expression: Expr | None = None
            if quant_token.value == "mu" and self._match(TokenType.PERIOD):
                self._advance()  # Consume '.'
                expression = self._parse_iff()  # Parse the expression part
        finally:
            self._in_comprehension_body = False

        return Quantifier(
            quantifier=quant_token.value,
            variables=variables,
            domain=domain,
            body=body,
            expression=expression,
            line_break_after_pipe=has_continuation,
            line=quant_token.line,
            column=quant_token.column,
        )

    def _parse_quantifier_continuation(
        self, quantifier: str, line: int, column: int
    ) -> Expr:
        """Parse continuation of semicolon-separated quantifier bindings.

        Phase 17: Helper for parsing y : U | body or y : U; z : V | body
        after we've already parsed x : T;
        """
        # Parse variable(s)
        if not self._match(TokenType.IDENTIFIER):
            raise ParserError(
                "Expected variable name after ';' in quantifier", self._current()
            )
        variables: list[str] = [self._advance().value]

        # Parse additional comma-separated variables
        while self._match(TokenType.COMMA):
            self._advance()  # Consume ','
            if not self._match(TokenType.IDENTIFIER):
                raise ParserError("Expected variable name after ','", self._current())
            variables.append(self._advance().value)

        # Parse domain
        domain: Expr | None = None
        if self._match(TokenType.COLON):
            self._advance()  # Consume ':'
            # Phase 21/22: Use _parse_union to match main quantifier parser
            domain = self._parse_union()

        # Check for another semicolon (more bindings)
        if self._match(TokenType.SEMICOLON):
            self._advance()  # Consume ';'
            nested_quant = self._parse_quantifier_continuation(
                quantifier, self._current().line, self._current().column
            )
            return Quantifier(
                quantifier=quantifier,
                variables=variables,
                domain=domain,
                body=nested_quant,
                expression=None,
                line=line,
                column=column,
            )

        # Otherwise expect pipe
        if not self._match(TokenType.PIPE):
            raise ParserError("Expected '|' after quantifier binding", self._current())
        self._advance()  # Consume '|'

        # Phase 21: Allow newlines after | (multi-line quantifiers)
        self._skip_newlines()

        # Set flag: we're in quantifier body where . can be separator (for mu)
        self._in_comprehension_body = True
        try:
            # Parse body
            body = self._parse_iff()

            # Check for mu expression part
            expression: Expr | None = None
            if quantifier == "mu" and self._match(TokenType.PERIOD):
                self._advance()  # Consume '.'
                expression = self._parse_iff()
        finally:
            self._in_comprehension_body = False

        return Quantifier(
            quantifier=quantifier,
            variables=variables,
            domain=domain,
            body=body,
            expression=expression,
            line=line,
            column=column,
        )

    def _parse_lambda(self) -> Expr:
        """Parse lambda expression: lambda var [, var]* : domain . body.

        Phase 11d: Lambda expressions.
        Examples:
        - lambda x : N . x^2
        - lambda x, y : N . x and y
        - lambda f : X -> Y . lambda x : X . f(x)
        """
        lambda_token = self._advance()  # Consume 'lambda'

        # Parse first variable
        if not self._match(TokenType.IDENTIFIER):
            raise ParserError("Expected variable name after lambda", self._current())
        variables: list[str] = [self._advance().value]

        # Parse additional variables if comma-separated
        while self._match(TokenType.COMMA):
            self._advance()  # Consume ','
            if not self._match(TokenType.IDENTIFIER):
                raise ParserError("Expected variable name after ','", self._current())
            variables.append(self._advance().value)

        # Parse domain (: domain) - required for lambda
        if not self._match(TokenType.COLON):
            raise ParserError("Expected ':' after lambda variables", self._current())
        self._advance()  # Consume ':'
        # Parse domain as full type expression (can be complex like X -> Y)
        # Use _parse_comparison() to get function types but stop at PERIOD
        # Set flag to prevent .identifier from being parsed as projection
        self._parsing_schema_text = True
        try:
            domain = self._parse_comparison()
        finally:
            self._parsing_schema_text = False

        # Parse separator . (period)
        if not self._match(TokenType.PERIOD):
            raise ParserError("Expected '.' after lambda binding", self._current())
        self._advance()  # Consume '.'

        # Parse body (rest of expression) - use _parse_expr() to allow nested
        # quantifiers and lambdas in the body
        # Lambda binds tighter than quantifiers, so "lambda x : X . forall y : Y | P"
        # means the body is the entire quantifier expression
        body = self._parse_expr()

        return Lambda(
            variables=variables,
            domain=domain,
            body=body,
            line=lambda_token.line,
            column=lambda_token.column,
        )

    def _parse_set(self) -> Expr:
        """Parse set literal or set comprehension (Phase 11.5).

        Distinguishes between:
        - Set literal: {1, 2, 3} or {a, b} - comma-separated elements
        - Set comprehension: {x : X | pred} - has : and |

        Strategy: Look ahead for : or | to determine type.
        Multi-variable comprehensions like {x, y : N | ...} need special handling.
        """
        start_token = self._current()  # Save position before '{'
        self._advance()  # Consume '{'

        # Empty set: {}
        if self._match(TokenType.RBRACE):
            self._advance()  # Consume '}'
            return SetLiteral(
                elements=[], line=start_token.line, column=start_token.column
            )

        # Look ahead to distinguish literal from comprehension
        # Strategy: Parse potential identifiers, check for : to determine type
        saved_pos = self.pos
        first_elem = self._parse_expr()

        # Case 1: Immediate colon -> single-variable comprehension
        if self._match(TokenType.COLON):
            self.pos = saved_pos
            return self._parse_set_comprehension_from_brace()

        # Case 2: Immediate pipe + identifier -> comprehension without domain
        if self._match(TokenType.PIPE):
            if isinstance(first_elem, Identifier):
                self.pos = saved_pos
                return self._parse_set_comprehension_from_brace()
            raise ParserError(
                "Unexpected '|' in set literal",
                self._current(),
            )

        # Case 3: Comma - need to look ahead further
        # Could be {x, y : N | ...} or {1, 2, 3}
        if self._match(TokenType.COMMA):
            # Collect all comma-separated items
            items: list[Expr] = [first_elem]
            while self._match(TokenType.COMMA):
                self._advance()  # Consume ','
                if self._match(TokenType.RBRACE):
                    # Trailing comma: {1, 2,}
                    break
                items.append(self._parse_expr())

            # Check what follows the comma-separated items
            if self._match(TokenType.COLON):
                # Multi-variable comprehension: {x, y : N | ...}
                # All items must be identifiers
                if not all(isinstance(item, Identifier) for item in items):
                    raise ParserError(
                        "Set comprehension variables must be identifiers",
                        self._current(),
                    )
                # Backtrack and parse as comprehension
                self.pos = saved_pos
                return self._parse_set_comprehension_from_brace()

            # It's a literal: {1, 2, 3} or {a, b, c}
            if not self._match(TokenType.RBRACE):
                raise ParserError("Expected '}' to close set literal", self._current())
            self._advance()  # Consume '}'
            return SetLiteral(
                elements=items, line=start_token.line, column=start_token.column
            )

        # Case 4: Single element followed by closing brace
        if self._match(TokenType.RBRACE):
            self._advance()  # Consume '}'
            return SetLiteral(
                elements=[first_elem],
                line=start_token.line,
                column=start_token.column,
            )

        # Unexpected token
        raise ParserError(
            "Expected ',', ':', '|', or '}' in set expression", self._current()
        )

    def _parse_set_comprehension_from_brace(self) -> Expr:
        """Parse set comprehension after '{' already consumed.

        Helper for _parse_set().
        """
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
            # Phase 21/22: Use _parse_union to allow union/intersect in domain
            # Allows: forall x : A union B | P
            # TODO Phase 23: Support relation types (A <-> B) in quantifier domains
            # Set flag to prevent .identifier from being parsed as projection
            self._parsing_schema_text = True
            try:
                domain = self._parse_union()
            finally:
                self._parsing_schema_text = False

        # Phase 22: Parse separator | or .
        # Syntax: {x : T | predicate . expr} or {x : T . expr} (no predicate)
        predicate: Expr | None
        expression: Expr | None

        if self._match(TokenType.PERIOD):
            # Period separator: no predicate, directly to expression
            self._advance()  # Consume '.'
            predicate = None
            expression = self._parse_set_expression()
        elif self._match(TokenType.PIPE):
            # Pipe separator: parse predicate, optionally followed by . expr
            self._advance()  # Consume '|'
            # Set flag: we're in comprehension body where . can be separator
            self._in_comprehension_body = True
            try:
                predicate = self._parse_set_predicate()

                # Parse optional expression part (. expression)
                expression = None
                if self._match(TokenType.PERIOD):
                    self._advance()  # Consume '.'
                    # Parse expression (up to })
                    expression = self._parse_set_expression()
            finally:
                self._in_comprehension_body = False
        elif self._match(TokenType.RBRACE):
            # No separator: both predicate and expression are omitted
            # {x : T} means "all x of type T", equivalent to just T
            predicate = None
            expression = None
        else:
            raise ParserError(
                "Expected '|', '.', or '}' after set comprehension binding",
                self._current(),
            )

        # Expect closing brace
        if not self._match(TokenType.RBRACE):
            raise ParserError(
                "Expected '}' to close set comprehension", self._current()
            )
        self._advance()  # Consume '}'

        # Use saved start position from _parse_set
        start_token = self.tokens[self.pos - len(variables) - 5]  # Approximate
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
        """Parse comparison operators (<, >, <=, >=, =, !=).

        Phase 21d: Allow newlines before and after comparison operators.
        Phase 23: Support guarded cases after = operator.
        """
        left = self._parse_function_type()

        # Phase 21d: Peek ahead to see if there's a comparison operator
        # We need to skip newlines to check, but restore position if no operator
        saved_pos = self.pos
        self._skip_newlines()

        if self._match(
            TokenType.LESS_THAN,
            TokenType.GREATER_THAN,
            TokenType.LESS_EQUAL,
            TokenType.GREATER_EQUAL,
            TokenType.EQUALS,
            TokenType.NOT_EQUAL,
        ):
            # Found comparison operator, consume it
            op_token = self._advance()
            # Phase 21d: Allow newlines after comparison operator
            self._skip_newlines()
            right = self._parse_function_type()

            # Phase 23: Check for guarded cases after = operator
            # Syntax: expr1 = expr2 \n if cond2 \n expr3 \n if cond3 ...
            if op_token.type == TokenType.EQUALS:
                right = self._try_parse_guarded_cases(right)

            left = BinaryOp(
                operator=op_token.value,
                left=left,
                right=right,
                line=op_token.line,
                column=op_token.column,
            )
        else:
            # No comparison operator, restore position to not consume newlines
            self.pos = saved_pos

        return left

    def _try_parse_guarded_cases(self, first_expr: Expr) -> Expr:
        """Try to parse guarded cases (Phase 23).

        Checks if the current position is followed by:
          NEWLINE IF condition NEWLINE expr IF condition ...

        If so, parses all guarded branches and returns GuardedCases.
        Otherwise, returns the original expression unchanged.

        Args:
            first_expr: The first expression (already parsed)

        Returns:
            GuardedCases if guards found, otherwise first_expr unchanged
        """
        # Check if next is NEWLINE + IF (but not IF ... THEN)
        if not self._match(TokenType.NEWLINE):
            return first_expr

        # Save position in case we need to backtrack
        saved_pos = self.pos

        # Skip the newline
        self._advance()

        # Check if next token is IF
        if not self._match(TokenType.IF):
            # Not a guarded case, restore position and return
            self.pos = saved_pos
            return first_expr

        # It's a guarded case! Parse first branch
        self._advance()  # Consume IF
        first_guard = self._parse_expr()

        branches: list[GuardedBranch] = [
            GuardedBranch(
                expression=first_expr,
                guard=first_guard,
                line=first_expr.line,
                column=first_expr.column,
            )
        ]

        # Parse remaining branches: NEWLINE expr NEWLINE IF guard
        while True:
            # Expect NEWLINE + expr
            if not self._match(TokenType.NEWLINE):
                break
            self._advance()  # Consume NEWLINE

            # Check if we're at the end or a structural element
            if self._at_end() or self._match(TokenType.END, TokenType.WHERE):
                # Restore the newline for parent parser
                self.pos -= 1
                break

            # Parse branch expression
            branch_expr = self._parse_function_type()

            # Expect NEWLINE + IF
            if not self._match(TokenType.NEWLINE):
                # No more branches, this expression is something else
                # This shouldn't happen in well-formed input
                raise ParserError(
                    "Expected newline after guarded branch expression", self._current()
                )
            self._advance()  # Consume NEWLINE

            if not self._match(TokenType.IF):
                # No IF, so we're done with guarded cases
                # Restore position to before the expression
                raise ParserError(
                    "Expected 'if' guard after expression in guarded cases",
                    self._current(),
                )

            self._advance()  # Consume IF
            branch_guard = self._parse_expr()

            branches.append(
                GuardedBranch(
                    expression=branch_expr,
                    guard=branch_guard,
                    line=branch_expr.line,
                    column=branch_expr.column,
                )
            )

        return GuardedCases(
            branches=branches, line=first_expr.line, column=first_expr.column
        )

    def _parse_function_type(self) -> Expr:
        """Parse function type operators (Phase 11c, enhanced Phase 18).

        Function types: ->, +->, >->, >+>, -|>, -->>, +->>, >->>
        Right-associative: A -> B -> C parses as A -> (B -> C)
        """
        left = self._parse_relation()

        # Check for function type arrow (right-associative)
        if self._match(
            TokenType.TFUN,  # ->
            TokenType.PFUN,  # +->
            TokenType.TINJ,  # >->
            TokenType.PINJ,  # >+>
            TokenType.PINJ_ALT,  # -|>
            TokenType.TSURJ,  # -->>
            TokenType.PSURJ,  # +->>
            TokenType.BIJECTION,  # >->>
        ):
            arrow_token = self._advance()
            # Right-associative: recursively parse the right side as function type
            right = self._parse_function_type()
            return FunctionType(
                arrow=arrow_token.value,
                domain=left,
                range=right,
                line=arrow_token.line,
                column=arrow_token.column,
            )

        return left

    def _parse_relation(self) -> Expr:
        """Parse relation operators (Phase 10a-b).

        Phase 10a: <->, |->, <|, |>, comp, ;
        Phase 10b: <<|, |>>, o9
        """
        left = self._parse_set_op()

        # Phase 10a-b: Infix relation operators (left-associative)
        # Note: SEMICOLON is NOT included here - it's used for declaration separators
        # Use 'o9' for relational composition instead
        while self._match(
            # Relation operators (Phase 10)
            TokenType.RELATION,  # <->
            TokenType.MAPLET,  # |->
            TokenType.DRES,  # <|
            TokenType.RRES,  # |>
            TokenType.NDRES,  # <<| (Phase 10b)
            TokenType.NRRES,  # |>> (Phase 10b)
            TokenType.CIRC,  # o9 (Phase 10b)
            TokenType.COMP,  # comp
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
        """Parse union and override operators (Phase 13).

        Union: union operator (set union)
        Override: ++ (function/sequence override)
        Both have similar precedence in Z notation.
        """
        left = self._parse_cross()

        while self._match(TokenType.UNION, TokenType.OVERRIDE):
            op_token = self._advance()
            right = self._parse_cross()
            left = BinaryOp(
                operator=op_token.value,
                left=left,
                right=right,
                line=op_token.line,
                column=op_token.column,
            )

        return left

    def _parse_cross(self) -> Expr:
        """Parse Cartesian product operator (Phase 11.5)."""
        left = self._parse_intersect()

        while self._match(TokenType.CROSS):
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
        """Parse intersect and set difference operators (Phase 11.5)."""
        left = self._parse_unary()

        while self._match(TokenType.INTERSECT, TokenType.SETMINUS):
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

    def _parse_postfix(self, allow_space_separated: bool = True) -> Expr:
        """Parse postfix operators and space-separated application.

        Phase 3: ^ (superscript), _ (subscript) - take operands
        Phase 10b: ~ (inverse), + (transitive closure),
                   * (reflexive-transitive closure) - no operands
        Phase 11.8: (| ... |) (relational image) - takes set argument
        Phase 11.9: [ ... ] (generic instantiation) - takes type parameters
        Phase 19: Space-separated function application (f x y)

        Disambiguation: + and * are postfix only if NOT followed by operand.
        If followed by operand, they're infix arithmetic operators.

        Space-separated application: f x y parses as (f x) y (left-associative).
        The allow_space_separated parameter prevents right-associativity when
        parsing arguments recursively.
        """
        base = self._parse_atom()

        # Phase 11.9: Check for generic instantiation [...]
        # Only treat [ as generic instantiation if:
        # 1. Base is a type-like construct (Identifier or GenericInstantiation)
        # 2. The '[' immediately follows the last consumed token (no whitespace)
        # This prevents consuming '[' meant for justifications in equiv chains
        while isinstance(base, (Identifier, GenericInstantiation)) and self._match(
            TokenType.LBRACKET
        ):
            # Check if '[' immediately follows the last token (no whitespace)
            # Use the tracked end position of the last consumed token
            lbracket_col = self._current().column

            # If on different lines or there's a gap,
            # don't treat as generic instantiation
            if (
                self._current().line != self.last_token_line
                or lbracket_col > self.last_token_end_column
            ):
                # There's whitespace - likely a justification, not generic
                break

            lbracket_token = self._advance()  # Consume '['

            # Parse comma-separated type parameters
            type_params: list[Expr] = []

            # Parse first type parameter
            if self._match(TokenType.RBRACKET):
                raise ParserError(
                    "Expected at least one type parameter in generic instantiation",
                    self._current(),
                )

            type_params.append(self._parse_expr())

            # Parse additional type parameters
            while self._match(TokenType.COMMA):
                self._advance()  # Consume ','
                if self._match(TokenType.RBRACKET):
                    # Trailing comma: Type[X,]
                    break
                type_params.append(self._parse_expr())

            if not self._match(TokenType.RBRACKET):
                raise ParserError(
                    "Expected ']' after generic type parameters", self._current()
                )
            self._advance()  # Consume ']'

            base = GenericInstantiation(
                base=base,
                type_params=type_params,
                line=lbracket_token.line,
                column=lbracket_token.column,
            )

        # Phase 12/13: Check for tuple projection and function application
        # These need to be in the same loop so that f(x).1 works correctly
        # Tuple projection: .1, .2, .3
        # Function application: expr(...)
        while self._match(TokenType.PERIOD, TokenType.LPAREN):
            # Check for tuple projection .1, .2, .3 or field projection .fieldname
            if self._match(TokenType.PERIOD):
                # Peek ahead to see if it's followed by a number or identifier
                next_token = self._peek_ahead(1)

                if next_token.type == TokenType.NUMBER:
                    # Numeric tuple projection: .1, .2, .3 (mostly original behavior)
                    # Add context-sensitive safety check:
                    # - If in schema text AND base is simple Identifier
                    #   AND followed by binary op
                    #   → likely separator (lambda x : X . 2 * x)
                    # - Otherwise → safe to parse as projection

                    # Only apply safety check in schema text
                    # (lambda/set comp declarations)
                    if self._parsing_schema_text and isinstance(base, Identifier):
                        token_after_num = self._peek_ahead(2)

                        # In lambda/set comp, simple type name followed by
                        # . NUMBER OP suggests separator
                        likely_separator = (
                            TokenType.STAR,  # X . 2 * x (separator in lambda)
                            TokenType.PLUS,  # X . 2 + x (separator)
                            TokenType.MINUS,  # X . 2 - x (separator)
                        )

                        if token_after_num.type in likely_separator:
                            # Ambiguous context - don't parse as projection
                            break

                    # Safe to parse as numeric projection
                    period_token = self._advance()  # Consume '.'
                    number_token = self._advance()  # Consume number

                    # Convert number to integer index
                    index = int(number_token.value)
                    if index < 1:
                        raise ParserError(
                            f"Tuple projection index must be >= 1, got {index}",
                            number_token,
                        )

                    base = TupleProjection(
                        base=base,
                        index=index,
                        line=period_token.line,
                        column=period_token.column,
                    )

                elif next_token.type == TokenType.IDENTIFIER:
                    # Named field projection: .fieldname (new feature)
                    # Don't parse as projection if we're in schema text
                    # (lambda/set comp) where periods are separators, not operators
                    if self._parsing_schema_text:
                        # In schema text - leave period unparsed (separator)
                        break

                    # Don't allow field projections on number literals
                    # (only tuples/records have named fields)
                    # This prevents parsing "0 . x" as projection in
                    # "x > 0 . x + 1"
                    if isinstance(base, Number):
                        # Numbers don't have named fields
                        break

                    # Check if we're in a comprehension/quantifier body where
                    # period could be expression separator
                    # If so, check what follows the identifier
                    token_after_id = self._peek_ahead(2)

                    # In comprehension body, .identifier} likely means separator + expr
                    # Example: {z : Z | z = z_0 * z_0 * z_0 . z}
                    #          period is separator, not projection
                    if (
                        self._in_comprehension_body
                        and token_after_id.type == TokenType.RBRACE
                    ):
                        # Likely expression separator, not projection
                        break

                    # Only parse if followed by safe token
                    # (not ambiguous with separator)

                    # Safe followers that indicate this is field projection,
                    # not separator
                    safe_followers = (
                        TokenType.PERIOD,  # .field.other (chained)
                        TokenType.LPAREN,  # .field(x)
                        TokenType.RPAREN,  # .field)
                        TokenType.RBRACE,  # .field}
                        TokenType.RBRACKET,  # .field]
                        TokenType.RANGLE,  # .field>
                        TokenType.COMMA,  # .field,
                        TokenType.SEMICOLON,  # .field;
                        TokenType.EQUALS,  # .field =
                        TokenType.NOT_EQUAL,  # .field !=
                        TokenType.IN,  # .field in
                        TokenType.NOTIN,  # .field notin
                        TokenType.SUBSET,  # .field subset
                        TokenType.LESS_THAN,  # .field <
                        TokenType.GREATER_THAN,  # .field >
                        TokenType.LESS_EQUAL,  # .field <=
                        TokenType.GREATER_EQUAL,  # .field >=
                        TokenType.IMPLIES,  # .field =>
                        TokenType.IFF,  # .field <=>
                        TokenType.AND,  # .field and
                        TokenType.OR,  # .field or
                        TokenType.PLUS,  # .field +
                        TokenType.MINUS,  # .field -
                        TokenType.EOF,  # .field (standalone)
                        TokenType.NEWLINE,  # .field\n (end of line)
                    )

                    if token_after_id.type in safe_followers:
                        # Safe context - parse as field projection
                        period_token = self._advance()  # Consume '.'
                        field_token = self._advance()  # Consume identifier

                        base = TupleProjection(
                            base=base,
                            index=field_token.value,  # Field name as string
                            line=period_token.line,
                            column=period_token.column,
                        )
                    else:
                        # Not safe - likely a separator, leave PERIOD unparsed
                        break
                else:
                    # Not projection, leave PERIOD for other uses
                    break

            # Check for function application expr(...)
            elif self._match(TokenType.LPAREN):
                lparen_token = self._advance()  # Consume '('
                args = self._parse_argument_list()
                if not self._match(TokenType.RPAREN):
                    raise ParserError(
                        "Expected ')' after function arguments", self._current()
                    )
                self._advance()  # Consume ')'
                base = FunctionApp(
                    function=base,
                    args=args,
                    line=lparen_token.line,
                    column=lparen_token.column,
                )

        # Keep applying other postfix operators
        while self._match(
            TokenType.CARET,
            TokenType.UNDERSCORE,
            TokenType.TILDE,
            TokenType.PLUS,
            TokenType.STAR,
            TokenType.LIMG,  # (| for relational image
        ):
            # Check for postfix +/* disambiguation
            # If + or * followed by operand, treat as infix (don't consume as postfix)
            if self._match(TokenType.PLUS, TokenType.STAR) and self._is_operand_start():
                break

            # Phase 11.8: Relational image R(| S |)
            if self._match(TokenType.LIMG):
                limg_token = self._advance()  # Consume '(|'
                set_expr = self._parse_expr()  # Parse the set argument
                if not self._match(TokenType.RIMG):
                    raise ParserError(
                        "Expected '|)' after relational image argument", self._current()
                    )
                self._advance()  # Consume '|)'
                base = RelationalImage(
                    relation=base,
                    set=set_expr,
                    line=limg_token.line,
                    column=limg_token.column,
                )
                continue

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

        # Phase 19: Space-separated function application
        # Pattern: f x y z → (((f x) y) z) (left-associative)
        # Only parse if allow_space_separated is True (prevents right-associativity)
        if allow_space_separated:
            while self._should_parse_space_separated_arg():
                # Save position for error reporting
                arg_start_token = self._current()

                # Parse argument with all its postfix operators
                # but WITHOUT space-separated application (prevents right-associativity)
                arg = self._parse_postfix(allow_space_separated=False)

                # Wrap in function application
                base = FunctionApp(
                    function=base,
                    args=[arg],
                    line=arg_start_token.line,
                    column=arg_start_token.column,
                )

        return base

    def _parse_atom(self) -> Expr:
        """Parse atom.

        Handles: identifier, number, parenthesized expression, set comprehension,
        Phase 10a relation functions (dom, ran), and Phase 10b functions (inv, id),
        Phase 11b function application (f(x), g(x, y)),
        Phase 11d lambda expressions (lambda x : X . body).
        """
        # Phase 10a-b: Prefix relation functions (dom, ran, inv, id)
        # Phase 11.5: Prefix set functions (P, P1)
        # Phase 11.9: Check for generic instantiation P[X] before treating as prefix
        # Phase 12: Prefix sequence operators (head, tail, last, front, rev)
        # Phase 19: Finite set types (F, F1)
        if self._match(
            TokenType.DOM,
            TokenType.RAN,
            TokenType.INV,
            TokenType.ID,
            TokenType.POWER,
            TokenType.POWER1,
            TokenType.FINSET,
            TokenType.FINSET1,
            TokenType.BIGCUP,  # Phase 20: distributed union
            TokenType.HEAD,
            TokenType.TAIL,
            TokenType.LAST,
            TokenType.FRONT,
            TokenType.REV,
        ):
            op_token = self._advance()

            # Phase 11.9: Check if followed by '[' for generic instantiation
            # If so, return as identifier-like node and let postfix handle it
            if self._match(TokenType.LBRACKET):
                # This is generic instantiation, not prefix operator
                # Return as Identifier and let _parse_postfix handle the [...]
                # Need to backtrack and reparse
                self.pos -= 1  # Back up before the operator token
                op_token = self._advance()  # Re-read it
                return Identifier(
                    name=op_token.value,
                    line=op_token.line,
                    column=op_token.column,
                )

            # Check if followed by a valid operand for prefix operator
            # If not, treat as standalone identifier (e.g., "R \ id" not "id R")
            if not self._match(
                TokenType.IDENTIFIER,
                TokenType.NUMBER,
                TokenType.LPAREN,
                TokenType.LBRACE,
                TokenType.LANGLE,
                TokenType.LAMBDA,
                TokenType.IF,
                TokenType.DOM,
                TokenType.RAN,
                TokenType.INV,
                TokenType.ID,
                TokenType.POWER,
                TokenType.POWER1,
                TokenType.FINSET,
                TokenType.FINSET1,
                TokenType.BIGCUP,
                TokenType.HEAD,
                TokenType.TAIL,
                TokenType.LAST,
                TokenType.FRONT,
                TokenType.REV,
            ):
                # Not followed by valid operand, treat as identifier
                return Identifier(
                    name=op_token.value,
                    line=op_token.line,
                    column=op_token.column,
                )

            # Not followed by '[', so it's a prefix operator
            operand = self._parse_atom()
            return UnaryOp(
                operator=op_token.value,
                operand=operand,
                line=op_token.line,
                column=op_token.column,
            )

        # Phase 11d: Lambda expressions
        if self._match(TokenType.LAMBDA):
            return self._parse_lambda()

        # Phase 16: Conditional expressions (allow as atoms)
        if self._match(TokenType.IF):
            return self._parse_conditional()

        # Phase 7: Quantified expressions (forall, exists, exists1, mu) as atoms
        # These can appear in expressions like: BadMu = mu n : N | n > 0
        if self._match(
            TokenType.FORALL, TokenType.EXISTS, TokenType.EXISTS1, TokenType.MU
        ):
            return self._parse_quantifier()

        # Phase 11b / Phase 13 / Phase 22: Identifiers
        # Note: Function application expr(...) is now handled in _parse_postfix()
        # Note: Generic instantiation Type[X] is handled in _parse_postfix()
        # Note: Relational image R(| S |) is handled in _parse_postfix()
        # Phase 22: Allow keywords to be used as function names (union, intersect)
        if self._match(TokenType.IDENTIFIER, TokenType.UNION, TokenType.INTERSECT):
            name_token = self._advance()
            return Identifier(
                name=name_token.value, line=name_token.line, column=name_token.column
            )

        if self._match(TokenType.NUMBER):
            token = self._advance()
            return Number(value=token.value, line=token.line, column=token.column)

        if self._match(TokenType.LPAREN):
            lparen_token = self._advance()  # Consume '('

            # Parse first expression
            first_expr = self._parse_expr()

            # Phase 21d: Allow newlines before checking what follows
            self._skip_newlines()

            # Check for comma (tuple) vs single parenthesized expression
            if self._match(TokenType.COMMA):
                # It's a tuple: (expr, expr, ...)
                elements: list[Expr] = [first_expr]

                while self._match(TokenType.COMMA):
                    self._advance()  # Consume ','
                    # Phase 21d: Allow newlines after comma
                    self._skip_newlines()
                    # Check for trailing comma: (a, b,)
                    if self._match(TokenType.RPAREN):
                        break
                    elements.append(self._parse_expr())
                    # Phase 21d: Allow newlines after element
                    self._skip_newlines()

                if not self._match(TokenType.RPAREN):
                    raise ParserError("Expected ')' after tuple", self._current())
                self._advance()  # Consume ')'

                return Tuple(
                    elements=elements,
                    line=lparen_token.line,
                    column=lparen_token.column,
                )

            # Single parenthesized expression
            if not self._match(TokenType.RPAREN):
                raise ParserError("Expected ')' after expression", self._current())
            self._advance()  # Consume ')'
            return first_expr

        # Phase 8 + 11.5: Set comprehension or set literal
        if self._match(TokenType.LBRACE):
            return self._parse_set()

        # Phase 12: Sequence literals ⟨a, b, c⟩
        if self._match(TokenType.LANGLE):
            return self._parse_sequence_literal()

        # Phase 12: Bag literals [[a, b, c]]
        # Check for two consecutive left brackets
        if self._match(TokenType.LBRACKET):
            # Peek ahead to see if next token is also LBRACKET
            if self._peek_ahead(1).type == TokenType.LBRACKET:
                return self._parse_bag_literal()
            # Single bracket - not a bag literal, error out
            raise ParserError(
                "Unexpected '[' - did you mean '[[' for bag literal?",
                self._current(),
            )

        # Handle unary prefix operators in restricted contexts
        # This allows # and not to work in set comprehension predicates
        # and other contexts where _parse_atom() is called directly
        if self._match(TokenType.HASH, TokenType.NOT, TokenType.MINUS):
            return self._parse_unary()

        raise ParserError(
            f"Expected identifier, number, '(', '{{', '⟨', or lambda,"
            f" got {self._current().type.name}",
            self._current(),
        )

    def _parse_argument_list(self) -> list[Expr]:
        """Parse comma-separated argument list for function application.

        Phase 11b: Handles empty list f(), single arg f(x), multiple args f(x, y, z).
        Returns: List of expressions (arguments).
        """
        args: list[Expr] = []

        # Empty argument list: f()
        if self._match(TokenType.RPAREN):
            return args

        # Parse first argument
        args.append(self._parse_expr())

        # Parse remaining arguments (comma-separated)
        while self._match(TokenType.COMMA):
            self._advance()  # Consume ','
            args.append(self._parse_expr())

        return args

    def _parse_sequence_literal(self) -> Expr:
        """Parse sequence literal: ⟨⟩, ⟨a⟩, ⟨a, b, c⟩.

        Phase 12: Sequence literal support.
        """
        langle_token = self._advance()  # Consume '⟨'

        elements: list[Expr] = []

        # Empty sequence: ⟨⟩
        if self._match(TokenType.RANGLE):
            self._advance()  # Consume '⟩'
            return SequenceLiteral(
                elements=elements,
                line=langle_token.line,
                column=langle_token.column,
            )

        # Parse comma-separated elements
        elements.append(self._parse_expr())

        while self._match(TokenType.COMMA):
            self._advance()  # Consume ','
            # Check for trailing comma: ⟨a, b,⟩
            if self._match(TokenType.RANGLE):
                break
            elements.append(self._parse_expr())

        # Expect closing angle bracket
        if not self._match(TokenType.RANGLE):
            raise ParserError("Expected '⟩' to close sequence literal", self._current())
        self._advance()  # Consume '⟩'

        return SequenceLiteral(
            elements=elements,
            line=langle_token.line,
            column=langle_token.column,
        )

    def _parse_bag_literal(self) -> Expr:
        """Parse bag literal: [[a]], [[a, b, c]].

        Phase 12: Bag literal support.
        Bag literals use double brackets: [[...]]
        """
        # Consume first '['
        lbag_token = self._advance()
        # Consume second '['
        if not self._match(TokenType.LBRACKET):
            raise ParserError("Expected second '[' for bag literal", self._current())
        self._advance()

        elements: list[Expr] = []

        # Parse comma-separated elements
        elements.append(self._parse_expr())

        while self._match(TokenType.COMMA):
            self._advance()  # Consume ','
            # Check for closing brackets
            if self._match(TokenType.RBRACKET):
                break
            elements.append(self._parse_expr())

        # Expect first closing bracket
        if not self._match(TokenType.RBRACKET):
            raise ParserError("Expected ']' to close bag literal", self._current())
        self._advance()  # Consume first ']'

        # Expect second closing bracket
        if not self._match(TokenType.RBRACKET):
            raise ParserError(
                "Expected second ']' to close bag literal", self._current()
            )
        self._advance()  # Consume second ']'

        return BagLiteral(
            elements=elements,
            line=lbag_token.line,
            column=lbag_token.column,
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
        """Parse free type: Type ::= branch1 | branch2⟨N⟩ | branch3⟨Tree x Tree⟩.

        Phase 17 enhancement: Supports recursive constructors with parameters.

        Examples:
        - Status ::= active | inactive (simple branches)
        - Tree ::= stalk | leaf⟨N⟩ | branch⟨Tree x Tree⟩ (with parameters)
        """
        # Identifier already consumed in _parse_document_item, need to back up
        name_token = self._current()
        type_name = name_token.value
        self._advance()  # Move to ::=

        if not self._match(TokenType.FREE_TYPE):
            raise ParserError("Expected '::=' in free type definition", self._current())
        self._advance()  # Consume '::='

        branches: list[FreeBranch] = []

        # Parse pipe-separated list of branches
        while not self._at_end() and not self._match(TokenType.NEWLINE):
            # Accept IDENTIFIER or keywords that could be branch names (P, F, etc.)
            if (
                self._match(TokenType.IDENTIFIER)
                or self._match(TokenType.POWER)
                or self._match(TokenType.POWER1)
                or self._match(TokenType.FINSET)
                or self._match(TokenType.FINSET1)
            ):
                branch_token = self._current()
                branch_name = branch_token.value
                self._advance()

                # Check for constructor parameters: ⟨...⟩
                parameters: Expr | None = None
                if self._match(TokenType.LANGLE):
                    langle_token = self._current()
                    self._advance()  # Consume '⟨'

                    # Check for empty parameters: ⟨⟩
                    if self._match(TokenType.RANGLE):
                        # Empty parameters - create empty sequence literal
                        parameters = SequenceLiteral(
                            elements=[],
                            line=langle_token.line,
                            column=langle_token.column,
                        )
                        self._advance()  # Consume '⟩'
                    else:
                        # Parse parameter type expression (can be cross product)
                        # Examples: ⟨N⟩, ⟨Tree⟩, ⟨Tree x Tree⟩
                        # Use _parse_cross to parse identifiers and cross products
                        # Stops at operators higher than cross (union, comparison)
                        parameters = self._parse_cross()

                        # Expect closing angle bracket
                        if not self._match(TokenType.RANGLE):
                            raise ParserError(
                                "Expected '⟩' after constructor parameters",
                                self._current(),
                            )
                        self._advance()  # Consume '⟩'

                # Create FreeBranch
                branches.append(
                    FreeBranch(
                        name=branch_name,
                        parameters=parameters,
                        line=branch_token.line,
                        column=branch_token.column,
                    )
                )

            # Check for pipe separator
            if self._match(TokenType.PIPE):
                self._advance()
            elif not self._match(TokenType.NEWLINE) and not self._at_end():
                # Unexpected token - raise error to prevent infinite loop
                current = self._current()
                if current.type == TokenType.EQUALS:
                    raise ParserError(
                        "Unexpected '=' in free type definition. "
                        "Did you mean '::=' instead of '::=='?",
                        current,
                    )
                else:
                    raise ParserError(
                        f"Expected branch name or '|' in free type definition, "
                        f"got {current.type.name}",
                        current,
                    )

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
        Supports semicolon-separated declarations: x : N; y : N
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

                # Check for semicolon separator (allows multiple declarations)
                if self._match(TokenType.SEMICOLON):
                    self._advance()  # Consume ';'
                    self._skip_newlines()
                    # Continue to parse next declaration
                else:
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

    def _parse_gendef(self) -> GenDef:
        """Parse generic definition block.

        Generic definitions require generic parameters.
        Syntax: gendef [X, Y] ... end
        Supports semicolon-separated declarations: f : X -> Y; g : X -> Y
        """
        start_token = self._advance()  # Consume 'gendef'
        self._skip_newlines()

        # Generic parameters are REQUIRED for gendef
        generic_params = self._parse_generic_params()
        if not generic_params:
            raise ParserError(
                "Generic parameters required for gendef (e.g., gendef [X, Y])",
                self._current(),
            )
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

                # Check for semicolon separator (allows multiple declarations)
                if self._match(TokenType.SEMICOLON):
                    self._advance()  # Consume ';'
                    self._skip_newlines()
                    # Continue to parse next declaration
                else:
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
            raise ParserError("Expected 'end' to close gendef block", self._current())
        self._advance()  # Consume 'end'

        return GenDef(
            generic_params=generic_params,
            declarations=declarations,
            predicates=predicates,
            line=start_token.line,
            column=start_token.column,
        )

    def _parse_zed(self) -> Zed:
        """Parse zed block for standalone predicates.

        Zed blocks contain unboxed Z notation paragraphs.
        Syntax: zed <content> end

        The content can be:
        - Standalone predicates (quantified or not)
        - Basic type declarations
        - Abbreviations
        - Free type definitions
        """
        start_token = self._advance()  # Consume 'zed'
        self._skip_newlines()

        # Parse the content as a single expression
        # This handles predicates, quantifiers, etc.
        content = self._parse_expr()
        self._skip_newlines()

        # Expect 'end'
        if not self._match(TokenType.END):
            raise ParserError("Expected 'end' to close zed block", self._current())
        self._advance()  # Consume 'end'

        return Zed(
            content=content,
            line=start_token.line,
            column=start_token.column,
        )

    def _parse_schema(self) -> Schema:
        """Parse schema definition block.

        Phase 9 enhancement: Supports optional generic parameters.
        Phase 13 enhancement: Supports anonymous schemas (no name).
        Syntax:
        - schema Name[X, Y] ... end (named with generics)
        - schema Name ... end (named)
        - schema ... end (anonymous)
        Supports semicolon-separated declarations: x : N; y : N
        """
        start_token = self._advance()  # Consume 'schema'

        # Parse optional schema name
        name: str | None = None
        generic_params: list[str] | None = None

        if self._match(TokenType.IDENTIFIER):
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

                # Check for semicolon separator (allows multiple declarations)
                if self._match(TokenType.SEMICOLON):
                    self._advance()  # Consume ';'
                    self._skip_newlines()
                    # Continue to parse next declaration
                else:
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
