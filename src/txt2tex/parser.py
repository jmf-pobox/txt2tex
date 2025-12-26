"""Parser for txt2tex - converts tokens into AST."""

from __future__ import annotations

import dataclasses
import re

from txt2tex.ast_nodes import (
    Abbreviation,
    ArgueChain,
    ArgueStep,
    AxDef,
    BagLiteral,
    BibliographyMetadata,
    BinaryOp,
    CaseAnalysis,
    Conditional,
    Contents,
    Declaration,
    Document,
    DocumentItem,
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
    InfruleBlock,
    Lambda,
    LatexBlock,
    Number,
    PageBreak,
    Paragraph,
    Part,
    PartsFormat,
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
    SyntaxBlock,
    SyntaxDefinition,
    TitleMetadata,
    TruthTable,
    Tuple,
    TupleProjection,
    UnaryOp,
    Zed,
)
from txt2tex.constants import PROSE_WORDS
from txt2tex.tokens import Token, TokenType


class ParserError(Exception):
    """Raised when parser encounters invalid syntax."""

    # Instance variable type annotations
    message: str
    token: Token

    def __init__(self, message: str, token: Token) -> None:
        """Initialize parser error with token position."""
        super().__init__(f"Line {token.line}, column {token.column}: {message}")
        self.message = message
        self.token = token


class Parser:
    """Recursive descent parser for txt2tex whiteboard notation.

    Expression grammar (precedence from lowest to highest):
        expr       ::= quantifier | iff
        quantifier ::= ('forall' | 'exists' | 'exists1' | 'mu')
                       var_list (':' atom)? '|' expr
        var_list   ::= IDENTIFIER (',' IDENTIFIER)*
        iff        ::= implies ( '<=>' implies )*
        implies    ::= or ( '=>' or )*
        or         ::= and ( 'or' and )*
        and        ::= comparison ( 'and' comparison )*
        comparison ::= relation ( ('<' | '>' | '<=' | '>=' | '=' | '!=') relation )?
        relation   ::= set_op ( relation_op set_op )*
        set_op     ::= union ( ('in' | 'notin' | 'subset') union )?
        union      ::= intersect ( 'union' intersect )*
        intersect  ::= unary ( 'intersect' unary )*
        unary      ::= 'not' unary | postfix
        postfix    ::= atom ( '^' atom | '_' atom | '~' | '+' | '*' )*
        atom       ::= prefix_op atom | IDENTIFIER | NUMBER | '(' expr ')' |
                       '{' set_comprehension '}' | '⟨' sequence '⟩' | '[[' bag ']]'

    Document structure:
        document ::= document_item*
        document_item ::= section | solution | part | truth_table | equiv_chain |
                         z_definition | proof_tree | expr

    Relation operators:
        - Infix: <-> (relation), |-> (maplet), <| (domain restriction),
                 |> (range restriction), <<| (domain subtraction),
                 |>> (range subtraction), o9/comp (composition)
        - Prefix: dom, ran, inv, id
        - Postfix: ~ (inverse), + (transitive closure), * (reflexive-transitive)

    Function type operators:
        - -> (total), +-> (partial), >-> (injection), >+> (partial injection),
          -->> (surjection), +->> (partial surjection), >->> (bijection)
    """

    # Instance variable type annotations
    tokens: list[Token]
    pos: int
    last_token_end_column: int
    last_token_line: int
    _parsing_schema_text: bool
    _in_comprehension_body: bool

    def __init__(self, tokens: list[Token]) -> None:
        """Initialize parser with token list.

        Args:
            tokens: List of tokens from Lexer to parse.
        """
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
        """Parse tokens and return AST.

        Parses the entire token stream into an Abstract Syntax Tree.
        Handles both document-level constructs (sections, solutions, Z blocks)
        and expression-level parsing.

        Returns:
            Document: For multi-line input or structural elements.
            Expr: For single expression input (backward compatible).

        Raises:
            ParserError: If the input contains syntax errors.
        """
        self._skip_newlines()

        # Empty input
        if self._at_end():
            return Document(
                items=[],
                title_metadata=None,
                parts_format="subsection",
                bibliography_metadata=None,
                line=1,
                column=1,
            )

        first_line = self._current().line

        # Parse title metadata, bibliography metadata, and parts format
        # at document start (if present)
        title_metadata = self._parse_title_metadata()
        bibliography_metadata = self._parse_bibliography_metadata()
        parts_format = self._parse_parts_format()

        # Check if we start with a structural element (section, solution, etc.)
        if self._is_structural_token():
            # Parse as document with structural elements
            items: list[DocumentItem] = []
            while not self._at_end():
                items.append(self._parse_document_item())
                self._skip_newlines()
            return Document(
                items=items,
                title_metadata=title_metadata,
                parts_format=parts_format,
                bibliography_metadata=bibliography_metadata,
                line=first_line,
                column=1,
            )

        # Check for abbreviation (identifier ==) or free type (identifier ::=)
        # Note: Partial support for compound identifiers like "R+ =="
        # (GitHub #3 still open)
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
                    return Document(
                        items=items_with_free,
                        title_metadata=None,
                        parts_format=parts_format,
                        bibliography_metadata=None,
                        line=first_line,
                        column=1,
                    )
                # Single free type
                return Document(
                    items=[first_free_type],
                    title_metadata=None,
                    parts_format=parts_format,
                    bibliography_metadata=None,
                    line=first_line,
                    column=1,
                )
            # Check for abbreviation with or without postfix operator
            # Cases: "R ==", "R+ ==", "R* ==", "R~ ==" (partial support, GitHub #3 open)
            is_abbrev = next_token.type == TokenType.ABBREV
            if not is_abbrev and next_token.type in (
                TokenType.PLUS,
                TokenType.STAR,
                TokenType.TILDE,
            ):
                # Check if postfix operator is followed by ==
                token_after_postfix = self._peek_ahead(2)
                is_abbrev = token_after_postfix.type == TokenType.ABBREV
            if is_abbrev:
                # Parse abbreviation and check for more items
                first_abbrev = self._parse_abbreviation()
                self._skip_newlines()
                # Check if there are more items (multi-line document)
                if not self._at_end():
                    items_with_abbrev: list[DocumentItem] = [first_abbrev]
                    while not self._at_end():
                        items_with_abbrev.append(self._parse_document_item())
                        self._skip_newlines()
                    return Document(
                        items=items_with_abbrev,
                        title_metadata=None,
                        parts_format=parts_format,
                        bibliography_metadata=None,
                        line=first_line,
                        column=1,
                    )
                # Single abbreviation
                return Document(
                    items=[first_abbrev],
                    title_metadata=None,
                    parts_format=parts_format,
                    bibliography_metadata=None,
                    line=first_line,
                    column=1,
                )

        # Check for abbreviation with generic parameters [X, Y] Name == expression
        # Note: Bag literals [[x]] start with [[ which is distinct
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
                return Document(
                    items=items_with_generic,
                    title_metadata=None,
                    parts_format=parts_format,
                    bibliography_metadata=None,
                    line=first_line,
                    column=1,
                )
            # Single abbreviation with generic parameters
            return Document(
                items=[first_generic_abbrev],
                title_metadata=None,
                parts_format=parts_format,
                bibliography_metadata=None,
                line=first_line,
                column=1,
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

            return Document(
                items=items_list,
                title_metadata=None,
                parts_format=parts_format,
                bibliography_metadata=None,
                line=first_line,
                column=1,
            )

        # Single expression (backward compatibility)
        if not self._at_end():
            raise ParserError(
                f"Unexpected token after expression: {self._current().value!r}",
                self._current(),
            )
        return first_item

    def _parse_title_metadata(self) -> TitleMetadata | None:
        """Parse title metadata at document start (TITLE:, AUTHOR:, etc.).

        This method consumes tokens, so it should only be called once at the
        start of document parsing.
        """
        title: str | None = None
        subtitle: str | None = None
        author: str | None = None
        date: str | None = None
        institution: str | None = None

        # Parse title metadata lines (must be at start of document)
        while not self._at_end():
            if self._match(TokenType.TITLE):
                token = self._advance()  # Consume TITLE token (value contains text)
                title = token.value.strip()
                self._skip_newlines()
            elif self._match(TokenType.SUBTITLE):
                token = self._advance()  # Consume SUBTITLE token
                subtitle = token.value.strip()
                self._skip_newlines()
            elif self._match(TokenType.AUTHOR):
                token = self._advance()  # Consume AUTHOR token
                author = token.value.strip()
                self._skip_newlines()
            elif self._match(TokenType.DATE):
                token = self._advance()  # Consume DATE token
                date = token.value.strip()
                self._skip_newlines()
            elif self._match(TokenType.INSTITUTION):
                token = self._advance()  # Consume INSTITUTION token
                institution = token.value.strip()
                self._skip_newlines()
            elif self._match(TokenType.PARTS):
                # PARTS directive - stop here, will be parsed by _parse_parts_format()
                break
            else:
                # Not a title metadata line, stop parsing
                break

        # Return metadata if any field was set, otherwise None
        if title or subtitle or author or date or institution:
            return TitleMetadata(
                title=title,
                subtitle=subtitle,
                author=author,
                date=date,
                institution=institution,
                line=1,
                column=1,
            )
        return None

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
            TokenType.CONTENTS,
            TokenType.PARTS,
            TokenType.ARGUE,  # Both EQUIV: and ARGUE: map to this token
            TokenType.INFRULE,
            TokenType.GIVEN,
            TokenType.AXDEF,
            TokenType.GENDEF,
            TokenType.ZED,
            TokenType.SCHEMA,
            TokenType.SYNTAX,
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

    def _parse_contents(self) -> Contents:
        """Parse table of contents directive from CONTENTS token.

        CONTENTS: generates table of contents (sections only)
        CONTENTS: full generates table of contents (sections + subsections)
        CONTENTS: 2 also generates table of contents (sections + subsections)
        """
        contents_token = self._advance()  # Consume CONTENTS token
        if contents_token.type != TokenType.CONTENTS:
            raise ParserError("Expected CONTENTS token", contents_token)

        depth = contents_token.value.strip()  # "full", "2", or empty
        return Contents(
            depth=depth, line=contents_token.line, column=contents_token.column
        )

    def _parse_bibliography_metadata(self) -> BibliographyMetadata:
        """Parse bibliography metadata directives.

        Parses BIBLIOGRAPHY: and BIBLIOGRAPHY_STYLE: directives.
        Returns BibliographyMetadata with file and style, or None values
        if not present.
        """
        file: str | None = None
        style: str | None = None

        # Parse BIBLIOGRAPHY: and BIBLIOGRAPHY_STYLE: tokens
        while not self._at_end():
            if self._match(TokenType.BIBLIOGRAPHY):
                token = self._advance()
                file = token.value.strip()
                self._skip_newlines()
            elif self._match(TokenType.BIBLIOGRAPHY_STYLE):
                token = self._advance()
                style = token.value.strip()
                self._skip_newlines()
            elif self._match(
                TokenType.TITLE,
                TokenType.SUBTITLE,
                TokenType.AUTHOR,
                TokenType.DATE,
                TokenType.INSTITUTION,
                TokenType.PARTS,
                TokenType.CONTENTS,
            ):
                # Other metadata directives - stop here, let them be parsed separately
                break
            else:
                # Not a metadata directive - stop parsing metadata
                break

        return BibliographyMetadata(
            file=file if file else None,
            style=style if style else None,
            line=self._current().line if not self._at_end() else 1,
            column=self._current().column if not self._at_end() else 1,
        )

    def _parse_parts_format(self) -> str:
        """Parse parts formatting style from PARTS token.

        PARTS: inline generates inline parts formatting
        PARTS: subsection generates subsection parts formatting (default)
        Returns the style string or "subsection" if not found.
        """
        if self._match(TokenType.PARTS):
            parts_token = self._advance()  # Consume PARTS token
            style = parts_token.value.strip().lower()
            # Validate style
            if style not in ("inline", "subsection"):
                raise ParserError(
                    f"Invalid parts format: {style}. Must be 'inline' or 'subsection'",
                    parts_token,
                )
            self._skip_newlines()  # Skip newlines after PARTS directive
            return style
        return "subsection"  # Default

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
        if self._match(TokenType.ARGUE):  # Handles both EQUIV: and ARGUE: keywords
            return self._parse_argue_chain()
        if self._match(TokenType.INFRULE):
            return self._parse_infrule_block()
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
        if self._match(TokenType.SYNTAX):
            return self._parse_syntax_block()
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
        if self._match(TokenType.CONTENTS):
            return self._parse_contents()
        if self._match(TokenType.PARTS):
            # PARTS directive parsed at document start, but can appear in content
            # Parse it but it will be ignored (document-level setting already applied)
            parts_token = self._advance()
            return PartsFormat(
                style=parts_token.value.strip().lower(),
                line=parts_token.line,
                column=parts_token.column,
            )

        # Check for abbreviation (identifier == expr) or free type (identifier ::= ...)
        # Note: Partial support for compound identifiers like "R+ =="
        # (GitHub #3 still open)
        if self._match(TokenType.IDENTIFIER):
            # Look ahead to determine type
            next_token = self._peek_ahead(1)
            if next_token.type == TokenType.FREE_TYPE:
                return self._parse_free_type()
            # Check for abbreviation with or without postfix operator
            # Cases: "R ==", "R+ ==", "R* ==", "R~ ==" (partial support, GitHub #3 open)
            is_abbrev = next_token.type == TokenType.ABBREV
            if not is_abbrev and next_token.type in (
                TokenType.PLUS,
                TokenType.STAR,
                TokenType.TILDE,
            ):
                # Check if postfix operator is followed by ==
                token_after_postfix = self._peek_ahead(2)
                is_abbrev = token_after_postfix.type == TokenType.ABBREV
            if is_abbrev:
                return self._parse_abbreviation()
            # Otherwise fall through to expression parsing

        # Check for abbreviation with generic parameters [X, Y] Name == expression
        # Note: Bag literals [[x]] start with [[ which is distinct
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

    def _parse_predicate_groups(
        self, end_tokens: tuple[TokenType, ...]
    ) -> list[list[Expr]]:
        """Parse predicates grouped by blank lines for \\also generation.

        Args:
            end_tokens: Token types that end the predicate section (e.g., END, WHERE)

        Returns:
            List of predicate groups, where each group is separated by blank lines
        """
        groups: list[list[Expr]] = []
        current_group: list[Expr] = []

        while not self._at_end() and not self._match(*end_tokens):
            # Skip leading newlines before checking for predicates
            if self._match(TokenType.NEWLINE):
                # Check if this is a blank line (2+ consecutive newlines)
                if self._has_blank_line():
                    # Save current group if non-empty
                    if current_group:
                        groups.append(current_group)
                        current_group = []
                    # Skip all newlines (including the blank line)
                    self._skip_newlines()
                else:
                    # Single newline - just skip it
                    self._advance()
                continue

            # Parse predicate and add to current group
            current_group.append(self._parse_expr())

        # Add final group if non-empty
        if current_group:
            groups.append(current_group)

        return groups  # Return [] if no predicates

    def _is_keyword_usable_as_identifier(self) -> bool:
        """Check if current token is a keyword that can be used as an identifier.

        Z notation keywords (id, dom, ran, etc.) are context-sensitive.
        In declaration contexts (schema/axdef/gendef), they can be variable names.
        In expression contexts, they remain operators/functions.

        Returns:
            True if current token is a keyword usable as identifier in declarations
        """
        return self._current().type in (
            TokenType.ID,  # id (identity relation)
            TokenType.DOM,  # dom (domain)
            TokenType.RAN,  # ran (range)
            TokenType.INV,  # inv (inverse)
            TokenType.COMP,  # comp (composition)
            TokenType.MOD,  # mod (modulo)
            TokenType.BIGCUP,  # bigcup (distributed union)
            TokenType.BIGCAP,  # bigcap (distributed intersection)
            TokenType.FILTER,  # filter (sequence filter)
        )

    def _smart_join_justification(self, parts: list[str]) -> str:
        """Join justification tokens intelligently.

        Strategy: Join with spaces (preserving word separation), then remove
        spaces around parentheses, brackets, and equals signs to compact
        mathematical notation.

        Examples:
        - ["length", "(", "<", "ple", ">", "^", "pl", ")"] → "length(<ple>^pl)"
        - ["commutativity", "of", "or"] → "commutativity of or"
        - ["x", "is", "not", "free", "in", "y", "|->", "z"] → "x is not free in y|->z"
        """
        if not parts:
            return ""

        # First join with spaces (preserves all word separation)
        result = " ".join(parts)

        # Remove spaces around specific punctuation to compact notation
        # ONLY touch safe characters that aren't part of operators
        result = re.sub(r"\s*\(\s*", "(", result)  # Remove space before/after (
        result = re.sub(r"\s*\)\s*", ")", result)  # Remove space before/after )
        result = re.sub(r"\s*=\s*", "=", result)  # Remove space around =
        return re.sub(r"\s*,", ",", result)  # Remove space BEFORE comma only

        # DO NOT touch < or > as they appear in many operators (=>, ->>, etc.)
        # Sequences like <ple> will have internal spacing, but that's acceptable
        # to avoid breaking operator conversion in _escape_justification

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
            # Note: F may be lexed as FINSET, P as POWER
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

    def _parse_argue_chain(self) -> ArgueChain:
        """Parse argue chain: ARGUE: or EQUIV: followed by reasoning steps.

        Both EQUIV: and ARGUE: keywords are supported (backwards-compatible).
        Generates argue environment for better page breaking.
        """
        start_token = self._advance()  # Consume 'ARGUE:' or 'EQUIV:'
        self._skip_newlines()

        steps: list[ArgueStep] = []

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
                # Join tokens smartly: add spaces only between consecutive identifiers
                justification = self._smart_join_justification(just_parts)

            # Create step
            steps.append(
                ArgueStep(
                    expression=expr,
                    justification=justification,
                    line=expr.line,
                    column=expr.column,
                )
            )

            self._skip_newlines()

        if not steps:
            raise ParserError(
                "Expected at least one step in ARGUE chain", self._current()
            )

        return ArgueChain(steps=steps, line=start_token.line, column=start_token.column)

    def _parse_infrule_block(self) -> InfruleBlock:
        """Parse INFRULE: block with premises, ---, and conclusion.

        Format:
          INFRULE:
          premise1 [label1]
          premise2 [label2]
          ---
          conclusion [label]
        """
        start_token = self._advance()  # Consume 'INFRULE:'
        self._skip_newlines()

        premises: list[tuple[Expr, str | None]] = []

        # Parse premises until we hit ---
        while not self._at_end() and not self._match(TokenType.DERIVE):
            # Check if we hit another structural token (error)
            if self._is_structural_token():
                raise ParserError(
                    "Expected '---' separator in INFRULE block", self._current()
                )

            # Parse premise expression
            expr = self._parse_expr()
            self._skip_newlines()

            # Check for optional label [text]
            label: str | None = None
            if self._match(TokenType.LBRACKET):
                self._advance()  # Consume '['

                # Collect label text (all tokens until ']')
                label_parts: list[str] = []
                while not self._match(TokenType.RBRACKET) and not self._at_end():
                    if self._match(TokenType.NEWLINE):
                        break  # Label on one line
                    label_parts.append(self._current().value)
                    self._advance()

                if not self._match(TokenType.RBRACKET):
                    raise ParserError("Expected closing ']' for label", self._current())

                self._advance()  # Consume ']'
                label = self._smart_join_justification(label_parts)

            premises.append((expr, label))
            self._skip_newlines()

        # Check for --- separator
        if not self._match(TokenType.DERIVE):
            raise ParserError(
                "Expected '---' separator in INFRULE block", self._current()
            )

        self._advance()  # Consume '---'
        self._skip_newlines()

        # Parse conclusion expression
        if self._at_end() or self._is_structural_token():
            raise ParserError(
                "Expected conclusion after '---' in INFRULE block", self._current()
            )

        conclusion_expr = self._parse_expr()
        self._skip_newlines()

        # Check for optional label [text]
        conclusion_label: str | None = None
        if self._match(TokenType.LBRACKET):
            self._advance()  # Consume '['

            # Collect label text
            conclusion_label_parts: list[str] = []
            while not self._match(TokenType.RBRACKET) and not self._at_end():
                if self._match(TokenType.NEWLINE):
                    break
                conclusion_label_parts.append(self._current().value)
                self._advance()

            if not self._match(TokenType.RBRACKET):
                raise ParserError(
                    "Expected closing ']' for conclusion label", self._current()
                )

            self._advance()  # Consume ']'
            conclusion_label = self._smart_join_justification(conclusion_label_parts)

        if not premises:
            raise ParserError(
                "Expected at least one premise in INFRULE block", self._current()
            )

        return InfruleBlock(
            premises=premises,
            conclusion=(conclusion_expr, conclusion_label),
            line=start_token.line,
            column=start_token.column,
        )

    def _parse_expr(self) -> Expr:
        """Parse expression (entry point)."""
        # Check for quantifier first (forall, exists, exists1, mu)
        if self._match(
            TokenType.FORALL, TokenType.EXISTS, TokenType.EXISTS1, TokenType.MU
        ):
            return self._parse_quantifier()
        # Check for lambda expression
        if self._match(TokenType.LAMBDA):
            return self._parse_lambda()
        # Check for conditional expression (if/then/else)
        if self._match(TokenType.IF):
            return self._parse_conditional()
        return self._parse_iff()

    def _parse_conditional(self) -> Expr:
        """Parse conditional expression: if condition then expr1 else expr2.

        Examples:
            if x > 0 then x else -x
            if s = <> then 0 else head s
            if x > 0 then 1 else if x < 0 then -1 else 0 (nested)

        Supports explicit line breaks with \\ continuation marker:
            if x > 0 \\
              then x \\
              else -x

        The condition is parsed with _parse_iff() (no quantifiers/lambdas/conditionals),
        but the then/else branches use _parse_expr() to allow nested conditionals.
        """
        if_token = self._advance()  # Consume 'if'

        # Parse condition (up to 'then') - no quantifiers/lambdas/conditionals
        condition = self._parse_iff()

        # Check for explicit line break after condition (before 'then')
        line_break_after_condition = False
        if self._match(TokenType.CONTINUATION):
            self._advance()  # consume \\
            line_break_after_condition = True

        # Skip newlines before 'then' (multi-line support)
        self._skip_newlines()

        # Expect 'then'
        if not self._match(TokenType.THEN):
            raise ParserError("Expected 'then' after if condition", self._current())
        self._advance()  # Consume 'then'

        # Skip newlines after 'then' (multi-line support)
        self._skip_newlines()

        # Parse then branch - allow nested conditionals
        then_expr = self._parse_expr()

        # Check for explicit line break after then expression (before 'else')
        line_break_after_then = False
        if self._match(TokenType.CONTINUATION):
            self._advance()  # consume \\
            line_break_after_then = True

        # Skip newlines before 'else' (multi-line support)
        self._skip_newlines()

        # Expect 'else'
        if not self._match(TokenType.ELSE):
            raise ParserError("Expected 'else' after then expression", self._current())
        self._advance()  # Consume 'else'

        # Skip newlines after 'else' (multi-line support)
        self._skip_newlines()

        # Parse else branch - allow nested conditionals
        else_expr = self._parse_expr()

        return Conditional(
            condition=condition,
            then_expr=then_expr,
            else_expr=else_expr,
            line_break_after_condition=line_break_after_condition,
            line_break_after_then=line_break_after_then,
            line=if_token.line,
            column=if_token.column,
        )

    def _parse_iff(self) -> Expr:
        """Parse iff operation (<=>), lowest precedence.

        Supports multi-line expressions with natural line breaks.
        """
        left = self._parse_implies()

        while self._match(TokenType.IFF):
            op_token = self._advance()
            # Detect line continuation (backslash or natural newline)
            has_continuation = False
            if self._match(TokenType.CONTINUATION):
                self._advance()  # consume \
                has_continuation = True
                # Skip newline and any leading whitespace on next line
                if self._match(TokenType.NEWLINE):
                    self._advance()
                self._skip_newlines()
            elif self._match(TokenType.NEWLINE):
                # Natural line break without \ marker (WYSIWYG)
                has_continuation = True
                self._skip_newlines()
            else:
                # No line break, but still skip newlines for flexibility
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

        Implies is right-associative: a => b => c parses as a => (b => c)
        Implies binds tighter than iff: a => b <=> c parses as (a => b) <=> c

        Supports multi-line expressions with natural line breaks.
        """
        left = self._parse_or()

        while self._match(TokenType.IMPLIES):
            op_token = self._advance()
            # Detect line continuation (backslash or natural newline)
            has_continuation = False
            if self._match(TokenType.CONTINUATION):
                self._advance()  # consume \
                has_continuation = True
                # Skip newline and any leading whitespace on next line
                if self._match(TokenType.NEWLINE):
                    self._advance()
                self._skip_newlines()
            elif self._match(TokenType.NEWLINE):
                # Natural line break without \ marker (WYSIWYG)
                has_continuation = True
                self._skip_newlines()
            else:
                # No line break, but still skip newlines for flexibility
                self._skip_newlines()
            # Parse RHS: allow quantifiers/lambdas/conditionals but NOT iff (<=>)
            # This ensures => binds tighter than <=>
            right = self._parse_implies_rhs()
            left = BinaryOp(
                operator=op_token.value,
                left=left,
                right=right,
                line_break_after=has_continuation,
                line=op_token.line,
                column=op_token.column,
            )

        return left

    def _parse_implies_rhs(self) -> Expr:
        """Parse right-hand side of implies: allows quantifiers but not iff.

        This ensures proper precedence: a => b <=> c parses as (a => b) <=> c
        while still allowing: a => forall x : T | P
        """
        # Check for quantifier first (forall, exists, exists1, mu)
        if self._match(
            TokenType.FORALL, TokenType.EXISTS, TokenType.EXISTS1, TokenType.MU
        ):
            return self._parse_quantifier()
        # Check for lambda expression
        if self._match(TokenType.LAMBDA):
            return self._parse_lambda()
        # Check for conditional expression (if/then/else)
        if self._match(TokenType.IF):
            return self._parse_conditional()
        # Parse implies level (right-associative) - NOT iff level
        return self._parse_implies()

    def _parse_or(self) -> Expr:
        """Parse or operation.

        Supports multi-line expressions with natural line breaks.
        """
        left = self._parse_and()

        while self._match(TokenType.OR):
            op_token = self._advance()
            # Detect line continuation (backslash or natural newline)
            has_continuation = False
            if self._match(TokenType.CONTINUATION):
                self._advance()  # consume \
                has_continuation = True
                # Skip newline and any leading whitespace on next line
                if self._match(TokenType.NEWLINE):
                    self._advance()
                self._skip_newlines()
            elif self._match(TokenType.NEWLINE):
                # Natural line break without \ marker (WYSIWYG)
                has_continuation = True
                self._skip_newlines()
            else:
                # No line break, but still skip newlines for flexibility
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
        """Parse and operation.

        Allows quantifiers after 'and' (e.g., p and forall x : T | q).
        Supports multi-line expressions with natural line breaks.
        """
        left = self._parse_comparison()

        while self._match(TokenType.AND):
            op_token = self._advance()
            # Detect line continuation (backslash or natural newline)
            has_continuation = False
            if self._match(TokenType.CONTINUATION):
                self._advance()  # consume \
                has_continuation = True
                # Skip newline and any leading whitespace on next line
                if self._match(TokenType.NEWLINE):
                    self._advance()
                self._skip_newlines()
            elif self._match(TokenType.NEWLINE):
                # Natural line break without \ marker (WYSIWYG)
                has_continuation = True
                self._skip_newlines()
            else:
                # No line break, but still skip newlines for flexibility
                self._skip_newlines()
            # Quantifiers can appear after 'and' (e.g., p and forall x : T | q)
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

        Handles logical not, cardinality (#), and arithmetic negation (-).
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

        # Cardinality operator (#)
        if self._match(TokenType.HASH):
            op_token = self._advance()
            operand = self._parse_unary()
            return UnaryOp(
                operator=op_token.value,
                operand=operand,
                line=op_token.line,
                column=op_token.column,
            )

        # Unary negation (-)
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
        Sequence operator: ⌢ (concatenation)
        Note: + can also be postfix (transitive closure R+), handled by lookahead
        """
        left = self._parse_multiplicative()

        while self._match(
            TokenType.PLUS,
            TokenType.MINUS,
            TokenType.CAT,
            TokenType.FILTER,
            TokenType.BAG_UNION,
        ):
            # Lookahead for +: only treat as infix if followed by operand
            # CAT, FILTER, BAG_UNION, and MINUS are always infix
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
        """Parse range operator (m..n).

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
            TokenType.MINUS,  # Unary negation
            TokenType.POWER,
            TokenType.POWER1,
            TokenType.FINSET,  # F (finite sets)
            TokenType.FINSET1,  # F1 (non-empty finite sets)
            TokenType.FORALL,
            TokenType.EXISTS,
            TokenType.EXISTS1,
            TokenType.MU,
            TokenType.LAMBDA,
            TokenType.IF,  # Conditional expressions (if/then/else)
        )

    def _should_parse_space_separated_arg(self) -> bool:
        """Check if we should parse next token as space-separated function argument.

        Space-separated application parses f x as function application.
        Returns True if next token could start an operand and we're not at
        a delimiter, separator, or infix operator.
        """
        # At end of input
        if self._at_end():
            return False

        current = self._current()

        # Reject common English prose words to avoid parsing text as math
        # This prevents "x >= 0 is true" from being parsed as function applications
        if (
            current.type == TokenType.IDENTIFIER
            and current.value.lower() in PROSE_WORDS
        ):
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
            TokenType.CONTINUATION,  # Line break marker
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
            TokenType.FILTER,  # ↾ sequence filter
            TokenType.BAG_UNION,  # ⊎ bag union
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
            TokenType.PSUBSET,  # psubset (strict subset)
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
            TokenType.FINFUN,  # 77-> (finite partial function)
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
            TokenType.BIGCAP,
            TokenType.LAMBDA,
            TokenType.IF,
        )

    def _parse_quantifier(self) -> Expr:
        """Parse quantifier: (forall|exists|exists1|mu) var [, var]* : domain | body.

        Supports:
            - Multiple variables with shared domain: forall x, y : N | pred
            - Tuple patterns for destructuring: forall (x, y) : T | pred
            - Semicolon-separated bindings (nested): forall x : T; y : U | pred
            - Mu-operator with expression: mu x : N | pred . expr

        Examples:
            forall x : N | pred
            forall x, y : N | pred
            forall (x, y) : T | pred
            exists1 x : N | pred
            mu x : N | pred . expr
        """
        quant_token = self._advance()  # Consume 'forall', 'exists', 'exists1', or 'mu'

        # Parse variable pattern: simple identifiers or tuple pattern like (x, y)
        tuple_pattern: Expr | None = None
        variables: list[str]

        if self._match(TokenType.LPAREN):
            # Tuple pattern: forall (x, y) : T | P
            tuple_pattern = self._parse_parenthesized_expr_or_tuple()

            # Extract variable names from tuple (validation: must be all identifiers)
            variables = []
            if isinstance(tuple_pattern, Tuple):
                for element in tuple_pattern.elements:
                    if isinstance(element, Identifier):
                        variables.append(element.name)
                    else:
                        raise ParserError(
                            "Tuple pattern in quantifier must contain only "
                            f"identifiers, not {type(element).__name__}",
                            self._current(),
                        )
            else:
                raise ParserError("Expected tuple pattern after '('", self._current())

            if not variables:
                raise ParserError(
                    "Tuple pattern in quantifier cannot be empty", self._current()
                )

        elif self._match(TokenType.IDENTIFIER):
            # Simple variable pattern: forall x : T | P
            variables = [self._advance().value]

            # Parse additional variables if comma-separated
            while self._match(TokenType.COMMA):
                self._advance()  # Consume ','
                if not self._match(TokenType.IDENTIFIER):
                    raise ParserError(
                        "Expected variable name after ','", self._current()
                    )
                variables.append(self._advance().value)
        else:
            raise ParserError(
                f"Expected variable name or tuple pattern after {quant_token.value}",
                self._current(),
            )

        # Parse optional domain (: domain)
        domain: Expr | None = None
        if self._match(TokenType.COLON):
            self._advance()  # Consume ':'
            # Parse type expression: union, cross, function & relation types
            # Allows: forall x : A union B | P
            # Allows: forall f : X -> Y | P (function type)
            # Allows: forall R : X <-> Y | P (relation type)
            # Set flag to prevent .identifier from being parsed as projection
            self._parsing_schema_text = True
            try:
                domain = self._parse_function_type()
            finally:
                self._parsing_schema_text = False

        # Check for semicolon-separated bindings (x : T; y : U | body)
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
                tuple_pattern=tuple_pattern,
                line=quant_token.line,
                column=quant_token.column,
            )

        # Parse separator |
        if not self._match(TokenType.PIPE):
            raise ParserError("Expected '|' after quantifier binding", self._current())
        self._advance()  # Consume '|'

        # Detect line continuation (backslash or natural newline)
        has_continuation = False
        if self._match(TokenType.CONTINUATION):
            self._advance()  # consume \
            has_continuation = True
            # Skip newline and any leading whitespace on next line
            if self._match(TokenType.NEWLINE):
                self._advance()
            self._skip_newlines()
        elif self._match(TokenType.NEWLINE):
            # Natural line break without \ marker (WYSIWYG)
            has_continuation = True
            self._skip_newlines()
        else:
            # Allow newlines after | for multi-line quantifiers
            self._skip_newlines()

        # Set flag: we're in quantifier body where . can be separator (for mu)
        self._in_comprehension_body = True
        try:
            # Parse body (may be followed by constraint pipe)
            body = self._parse_expr()

            # Check for second pipe (constrained quantifier)
            # forall x : T | constraint | body → constraint => body
            if self._match(TokenType.PIPE):
                self._advance()  # Consume second '|'

                # Check for continuation marker after second pipe
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
                # Combine constraint and body with IMPLIES (filter semantics)
                body = BinaryOp(
                    operator="implies",
                    left=constraint,
                    right=actual_body,
                    line_break_after=constraint_continuation,
                    line=constraint.line,
                    column=constraint.column,
                )

            # Check for bullet separator (Q x : T | pred . expr)
            expression: Expr | None = None
            bullet_continuation = False
            if self._match(TokenType.PERIOD):
                self._advance()  # Consume '.'

                # Handle continuation marker or newline after bullet separator
                if self._match(TokenType.CONTINUATION):
                    self._advance()  # consume \
                    bullet_continuation = True
                    # Skip newline and any leading whitespace on next line
                    if self._match(TokenType.NEWLINE):
                        self._advance()
                    self._skip_newlines()
                elif self._match(TokenType.NEWLINE):
                    # Allow bare newline after bullet (no backslash needed) - WYSIWYG
                    bullet_continuation = True
                    self._advance()
                    self._skip_newlines()

                # Expression after bullet is not part of comprehension body
                self._in_comprehension_body = False
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
            line_break_after_bullet=bullet_continuation,
            tuple_pattern=tuple_pattern,
            line=quant_token.line,
            column=quant_token.column,
        )

    def _parse_quantifier_continuation(
        self, quantifier: str, line: int, column: int
    ) -> Expr:
        """Parse continuation of semicolon-separated quantifier bindings.

        Helper for parsing y : U | body or y : U; z : V | body
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
            # Parse type expression to match main quantifier parser
            domain = self._parse_function_type()

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
                tuple_pattern=None,  # No tuple pattern in continuation
                line=line,
                column=column,
            )

        # Otherwise expect pipe
        if not self._match(TokenType.PIPE):
            raise ParserError("Expected '|' after quantifier binding", self._current())
        self._advance()  # Consume '|'

        # Allow newlines after | for multi-line quantifiers
        self._skip_newlines()

        # Set flag: we're in quantifier body where . can be separator (for mu)
        self._in_comprehension_body = True
        try:
            # Parse body (constraint part if bullet separator follows)
            body = self._parse_iff()

            # Check for bullet separator (Q x : T | pred . expr)
            expression: Expr | None = None
            bullet_continuation = False
            if self._match(TokenType.PERIOD):
                self._advance()  # Consume '.'

                # Handle continuation marker or newline after bullet separator
                if self._match(TokenType.CONTINUATION):
                    self._advance()  # consume \
                    bullet_continuation = True
                    # Skip newline and any leading whitespace on next line
                    if self._match(TokenType.NEWLINE):
                        self._advance()
                    self._skip_newlines()
                elif self._match(TokenType.NEWLINE):
                    # Allow bare newline after bullet (no backslash needed) - WYSIWYG
                    bullet_continuation = True
                    self._advance()
                    self._skip_newlines()

                # Expression after bullet is not part of comprehension body
                self._in_comprehension_body = False
                expression = self._parse_iff()
        finally:
            self._in_comprehension_body = False

        return Quantifier(
            quantifier=quantifier,
            variables=variables,
            domain=domain,
            body=body,
            expression=expression,
            line_break_after_bullet=bullet_continuation,
            tuple_pattern=None,  # No tuple pattern in continuation
            line=line,
            column=column,
        )

    def _parse_lambda(self) -> Expr:
        """Parse lambda expression: lambda var [, var]* : domain . body.

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
        """Parse set literal or set comprehension.

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
            # Parse type expression: union, cross, function & relation types
            # Allows: forall x : A union B | P
            # Allows: forall f : X -> Y | P (function type)
            # Allows: forall R : X <-> Y | P (relation type)
            # Set flag to prevent .identifier from being parsed as projection
            self._parsing_schema_text = True
            try:
                domain = self._parse_function_type()
            finally:
                self._parsing_schema_text = False

        # Parse separator | or . for set comprehension
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

        Allows newlines before and after comparison operators.
        Supports guarded cases after = operator (pattern matching).
        Supports line continuation with \\ after = operator.
        """
        left = self._parse_function_type()

        # Peek ahead to see if there's a comparison operator
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
            TokenType.SHOWS,
        ):
            # Found comparison operator, consume it
            op_token = self._advance()

            # Detect line continuation (backslash after operator)
            has_continuation = False
            if self._match(TokenType.CONTINUATION):
                self._advance()  # consume \
                has_continuation = True
                # Skip newline and any leading whitespace on next line
                if self._match(TokenType.NEWLINE):
                    self._advance()
                self._skip_newlines()
            else:
                # Allow newlines after comparison operator
                self._skip_newlines()

            right = self._parse_function_type()

            # Check for guarded cases after = operator (pattern matching)
            # Syntax: expr1 = expr2 \n if cond2 \n expr3 \n if cond3 ...
            if op_token.type == TokenType.EQUALS:
                right = self._try_parse_guarded_cases(right)

            left = BinaryOp(
                operator=op_token.value,
                left=left,
                right=right,
                line_break_after=has_continuation,
                line=op_token.line,
                column=op_token.column,
            )
        else:
            # No comparison operator, restore position to not consume newlines
            self.pos = saved_pos

        return left

    def _try_parse_guarded_cases(self, first_expr: Expr) -> Expr:
        """Try to parse guarded cases for pattern matching.

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
        """Parse function and relation type operators.

        Function/relation types: ->, +->, >->, >+>, -|>, -->>, +->>, >->>, <->
        Right-associative: A -> B -> C parses as A -> (B -> C)
        Also used in quantifier domains: forall f : X -> Y | P
        """
        left = self._parse_relation()

        # Check for function/relation type operators (right-associative)
        if self._match(
            TokenType.TFUN,  # ->
            TokenType.PFUN,  # +->
            TokenType.TINJ,  # >->
            TokenType.PINJ,  # >+>
            TokenType.PINJ_ALT,  # -|>
            TokenType.TSURJ,  # -->>
            TokenType.PSURJ,  # +->>
            TokenType.BIJECTION,  # >->>
            TokenType.FINFUN,  # 77-> (finite partial function)
            TokenType.RELATION,  # <-> (relation type)
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
        """Parse relation operators.

        Infix: <->, |->, <|, |>, <<|, |>>, o9/comp
        """
        left = self._parse_set_op()

        # Infix relation operators (left-associative)
        # Note: SEMICOLON is NOT included here - it's used for declaration separators
        # Use 'o9' for relational composition instead
        while self._match(
            TokenType.RELATION,  # <->
            TokenType.MAPLET,  # |->
            TokenType.DRES,  # <| (domain restriction)
            TokenType.RRES,  # |> (range restriction)
            TokenType.NDRES,  # <<| (domain subtraction)
            TokenType.NRRES,  # |>> (range subtraction)
            TokenType.CIRC,  # o9 (relational composition)
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
        """Parse set operators (in, notin, subset, psubset)."""
        left = self._parse_union()

        if self._match(
            TokenType.IN, TokenType.NOTIN, TokenType.SUBSET, TokenType.PSUBSET
        ):
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
        """Parse union and override operators.

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
        """Parse Cartesian product operator (cross)."""
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
        """Parse intersect and set difference operators."""
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

    def _parse_postfix(self, *, allow_space_separated: bool = True) -> Expr:  # noqa: C901
        """Parse postfix operators and space-separated application.

        Postfix operators:
            ^ (superscript), _ (subscript) - take operands
            ~ (inverse), + (transitive), * (reflexive-transitive) - no operands
            (| ... |) (relational image) - takes set argument
            [ ... ] (generic instantiation) - takes type parameters

        Disambiguation: + and * are postfix only if NOT followed by operand.
        If followed by operand, they're infix arithmetic operators.

        Space-separated application: f x y parses as (f x) y (left-associative).
        The allow_space_separated parameter prevents right-associativity when
        parsing arguments recursively.
        """
        base = self._parse_atom()

        # Check for generic instantiation [...] like P[X], F[T]
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

        # Check for tuple projection and function application
        # These need to be in the same loop so that f(x).1 works correctly
        # Tuple projection: .1, .2, .3 or .fieldname
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
                    # In set comprehensions like {c : children(p) . children(c)},
                    # the . after children(p) is the body separator, not field access
                    if self._parsing_schema_text:
                        # In schema text, period is always separator, not projection
                        break

                    # Don't allow field projections on number literals
                    # (only tuples/records have named fields)
                    # This prevents parsing "0 . x" as projection in
                    # "x > 0 . x + 1"
                    if isinstance(base, Number):
                        # Numbers don't have named fields
                        break

                    # Check if we're in a comprehension/quantifier body where
                    # period could be expression separator in comprehension/quantifier
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

                    # In quantifier bodies, avoid parsing .identifier as
                    # projection when it's actually a bullet separator
                    # Heuristic: Check what follows the identifier
                    next_token = self._peek_ahead(1)
                    if (
                        self._in_comprehension_body
                        and next_token.type == TokenType.IDENTIFIER
                        and not next_token.value.isdigit()
                    ):
                        token_after_id = self._peek_ahead(2)

                        # Strong bullet separator indicators:
                        # - Set/logical operators starting new predicates
                        # - Base is complex expression (not simple id)
                        is_bullet_indicator = token_after_id.type in (
                            TokenType.IN,
                            TokenType.NOTIN,
                            TokenType.SUBSET,
                            TokenType.PSUBSET,
                            TokenType.AND,
                            TokenType.OR,
                            TokenType.IMPLIES,
                            TokenType.IFF,
                        )

                        # Special case: When base is FunctionApp and followed by
                        # .identifier = , this is almost always a bullet separator
                        # Example: f(x) = g(y) . x = y (the . is bullet, not projection)
                        # This pattern is common in quantifier bodies like:
                        # forall x : X | f(x) = g(x) . h(x) = k(x)
                        if (
                            isinstance(base, FunctionApp)
                            and token_after_id.type == TokenType.EQUALS
                        ):
                            is_bullet_indicator = True

                        # Allow field projection on safe base types that can have fields
                        # (GitHub issue #13: FunctionApp and TupleProjection are safe)
                        safe_projection_bases = (
                            Identifier,
                            FunctionApp,
                            TupleProjection,
                        )
                        if is_bullet_indicator or not isinstance(
                            base, safe_projection_bases
                        ):
                            # Likely bullet separator - break
                            break

                        # For other cases (like EQUALS on non-FunctionApp),
                        # rely on safe_followers.
                        # Allows "e.field = value" while catching most bullets

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
                        TokenType.PSUBSET,  # .field psubset
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

            # Relational image R(| S |)
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
                # Postfix: ~ (inverse), + (transitive), * (reflexive-transitive)
                base = UnaryOp(
                    operator=op_token.value,
                    operand=base,
                    line=op_token.line,
                    column=op_token.column,
                )

        # Space-separated function application: f x y z → (((f x) y) z)
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

    def _parse_parenthesized_expr_or_tuple(self) -> Expr:
        """Parse parenthesized expression or tuple.

        This parses (expr), (expr,), or (expr1, expr2, ...).
        Used by both _parse_atom and _parse_quantifier for tuple patterns.
        """
        lparen_token = self._advance()  # Consume '('

        # Parse first expression
        first_expr = self._parse_expr()

        # Allow newlines for multi-line expressions
        self._skip_newlines()

        # Check for comma (tuple) vs single parenthesized expression
        if self._match(TokenType.COMMA):
            # It's a tuple: (expr, expr, ...)
            elements: list[Expr] = [first_expr]

            while self._match(TokenType.COMMA):
                self._advance()  # Consume ','
                # Allow newlines after comma in tuples
                self._skip_newlines()
                # Check for trailing comma: (a, b,)
                if self._match(TokenType.RPAREN):
                    break
                elements.append(self._parse_expr())
                # Allow newlines for multi-line tuples
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

        # Mark BinaryOp as explicitly parenthesized to preserve user intent
        if isinstance(first_expr, BinaryOp):
            return dataclasses.replace(first_expr, explicit_parens=True)

        return first_expr

    def _parse_atom(self) -> Expr:
        """Parse atom.

        Handles: identifier, number, parenthesized expression, set comprehension,
        prefix operators (dom, ran, inv, id, P, P1, F, F1, bigcup, bigcap),
        function application f(x), and lambda expressions.
        """
        # Prefix operators: relation functions, set functions, sequence operators
        # Check for generic instantiation P[X] before treating as prefix
        if self._match(
            TokenType.DOM,
            TokenType.RAN,
            TokenType.INV,
            TokenType.ID,
            TokenType.POWER,
            TokenType.POWER1,
            TokenType.FINSET,
            TokenType.FINSET1,
            TokenType.BIGCUP,  # Distributed union
            TokenType.BIGCAP,  # Distributed intersection
        ):
            op_token = self._advance()

            # Check if followed by '[' for generic instantiation like P[X]
            # If so, return as identifier and let postfix handle the [...]
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
                TokenType.BIGCAP,
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

        # Lambda expressions (lambda x : X . body)
        if self._match(TokenType.LAMBDA):
            return self._parse_lambda()

        # Conditional expressions (if/then/else)
        if self._match(TokenType.IF):
            return self._parse_conditional()

        # Quantified expressions (forall, exists, exists1, mu) as atoms
        # These can appear in expressions like: BadMu = mu n : N | n > 0
        if self._match(
            TokenType.FORALL, TokenType.EXISTS, TokenType.EXISTS1, TokenType.MU
        ):
            return self._parse_quantifier()

        # Identifiers (including keywords allowed as function names)
        # Note: Function application expr(...) is handled in _parse_postfix()
        # Note: Generic instantiation Type[X] is handled in _parse_postfix()
        # Note: Relational image R(| S |) is handled in _parse_postfix()
        if self._match(
            TokenType.IDENTIFIER,
            TokenType.UNION,
            TokenType.INTERSECT,
            TokenType.FILTER,
        ):
            name_token = self._advance()
            return Identifier(
                name=name_token.value, line=name_token.line, column=name_token.column
            )

        if self._match(TokenType.NUMBER):
            token = self._advance()
            return Number(value=token.value, line=token.line, column=token.column)

        if self._match(TokenType.LPAREN):
            return self._parse_parenthesized_expr_or_tuple()

        # Set comprehension or set literal {x : X | pred} or {a, b, c}
        if self._match(TokenType.LBRACE):
            return self._parse_set()

        # Sequence literals ⟨a, b, c⟩
        if self._match(TokenType.LANGLE):
            return self._parse_sequence_literal()

        # Bag literals [[a, b, c]]
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

        Handles empty list f(), single arg f(x), multiple args f(x, y, z).
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
        """Parse sequence literal: ⟨⟩, ⟨a⟩, ⟨a, b, c⟩."""
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
        # Stop at NEWLINE, END (for zed blocks), or EOF
        while not self._at_end() and not self._match(TokenType.NEWLINE, TokenType.END):
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

    def _parse_free_branch(self, branch_token: Token) -> FreeBranch:
        """Parse a single free type branch with optional parameters.

        Assumes the branch name token has already been consumed. Parses
        optional constructor parameters in angle brackets: <...> or ⟨...⟩

        Args:
            branch_token: The token containing the branch name

        Returns:
            FreeBranch with name and optional parameters
        """
        branch_name = branch_token.value

        # Check for constructor parameters: ⟨...⟩ or <...>
        parameters: Expr | None = None
        if self._match(TokenType.LANGLE):
            langle_token = self._current()
            self._advance()  # Consume '⟨' or '<'

            # Check for empty parameters: ⟨⟩
            if self._match(TokenType.RANGLE):
                # Empty parameters - create empty sequence literal
                parameters = SequenceLiteral(
                    elements=[],
                    line=langle_token.line,
                    column=langle_token.column,
                )
                self._advance()  # Consume '⟩' or '>'
            else:
                # Parse parameter type expression (can be cross product)
                # Examples: ⟨N⟩, ⟨Tree⟩, ⟨Tree x Tree⟩
                parameters = self._parse_cross()

                # Expect closing angle bracket
                if not self._match(TokenType.RANGLE):
                    raise ParserError(
                        "Expected '⟩' or '>' after constructor parameters",
                        self._current(),
                    )
                self._advance()  # Consume '⟩' or '>'

        return FreeBranch(
            name=branch_name,
            parameters=parameters,
            line=branch_token.line,
            column=branch_token.column,
        )

    def _parse_free_type(self) -> FreeType:
        """Parse free type: Type ::= branch1 | branch2⟨N⟩ | branch3⟨Tree x Tree⟩.

        Supports recursive constructors with parameters.

        Examples:
            Status ::= active | inactive (simple branches)
            Tree ::= stalk | leaf⟨N⟩ | branch⟨Tree x Tree⟩ (with parameters)
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
        # Stop at NEWLINE, END (for zed blocks), or EOF
        while not self._at_end() and not self._match(TokenType.NEWLINE, TokenType.END):
            # Accept IDENTIFIER or keywords that could be branch names (P, F, etc.)
            if (
                self._match(TokenType.IDENTIFIER)
                or self._match(TokenType.POWER)
                or self._match(TokenType.POWER1)
                or self._match(TokenType.FINSET)
                or self._match(TokenType.FINSET1)
            ):
                branch_token = self._current()
                self._advance()
                branches.append(self._parse_free_branch(branch_token))

            # Check for pipe separator
            if self._match(TokenType.PIPE):
                self._advance()
            elif (
                not self._match(TokenType.NEWLINE, TokenType.END) and not self._at_end()
            ):
                # Unexpected token - raise error to prevent infinite loop
                current = self._current()
                if current.type == TokenType.EQUALS:
                    raise ParserError(
                        "Unexpected '=' in free type definition. "
                        "Did you mean '::=' instead of '::=='?",
                        current,
                    )
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

    def _parse_syntax_block(self) -> SyntaxBlock:
        """Parse syntax environment for aligned free type definitions.

        Syntax:
          syntax
            TypeName ::= branch1 | branch2

            AnotherType ::= branch1<Param>
                         |  branch2<Param1 cross Param2>
          end

        Generates column-aligned LaTeX with \also between groups.
        """
        start_token = self._advance()  # Consume 'syntax'
        self._skip_newlines()

        # Parse groups of definitions separated by blank lines
        groups: list[list[SyntaxDefinition]] = []
        current_group: list[SyntaxDefinition] = []

        while not self._at_end() and not self._match(TokenType.END):
            # Check for blank line (group separator)
            if self._match(TokenType.NEWLINE):
                # Count consecutive newlines
                newline_count = 0
                while self._match(TokenType.NEWLINE):
                    newline_count += 1
                    self._advance()

                # Blank line (2+ newlines) separates groups
                if newline_count >= 2 and current_group:
                    groups.append(current_group)
                    current_group = []

                # Skip any remaining newlines
                self._skip_newlines()

                if self._match(TokenType.END):
                    break

            # Parse a single free type definition
            if not self._match(TokenType.IDENTIFIER):
                if not self._match(TokenType.END):
                    current_type = self._current().type.name
                    raise ParserError(
                        f"Expected type name in syntax block, got {current_type}",
                        self._current(),
                    )
                break

            # Parse: TypeName ::= branches
            type_name_token = self._current()
            type_name = type_name_token.value
            self._advance()

            if not self._match(TokenType.FREE_TYPE):
                raise ParserError(
                    "Expected '::=' after type name in syntax block",
                    self._current(),
                )
            self._advance()  # Consume '::='

            # Parse branches using shared helper
            branches: list[FreeBranch] = []

            # Parse initial set of branches on the same line
            while not self._at_end():
                if self._match(TokenType.NEWLINE, TokenType.END):
                    break
                # Parse branch name
                if not self._match(TokenType.IDENTIFIER):
                    if self._match(TokenType.PIPE):
                        # Skip leading pipe if present
                        self._advance()
                        continue
                    break

                branch_token = self._current()
                self._advance()
                branches.append(self._parse_free_branch(branch_token))

                # Check for pipe separator
                if self._match(TokenType.PIPE):
                    self._advance()

            # Check for continuation lines (starting with |)
            while not self._at_end() and not self._match(TokenType.END):
                # Skip single newline
                if self._match(TokenType.NEWLINE):
                    self._advance()

                # Check if next line starts with |
                if not self._match(TokenType.PIPE):
                    break

                self._advance()  # Consume continuation '|'

                # Parse branches on this continuation line
                while not self._at_end():
                    if self._match(TokenType.NEWLINE, TokenType.END):
                        break

                    if not self._match(TokenType.IDENTIFIER):
                        if self._match(TokenType.PIPE):
                            self._advance()
                            continue
                        break

                    branch_token = self._current()
                    self._advance()
                    branches.append(self._parse_free_branch(branch_token))

                    if self._match(TokenType.PIPE):
                        self._advance()

            if not branches:
                raise ParserError(
                    f"Expected at least one branch for type {type_name}",
                    type_name_token,
                )

            # Create SyntaxDefinition
            current_group.append(
                SyntaxDefinition(
                    name=type_name,
                    branches=branches,
                    line=type_name_token.line,
                    column=type_name_token.column,
                )
            )

            # Skip trailing newline after definition
            if self._match(TokenType.NEWLINE):
                self._advance()

        # Add final group if not empty
        if current_group:
            groups.append(current_group)

        # Expect 'end'
        if not self._match(TokenType.END):
            raise ParserError("Expected 'end' to close syntax block", self._current())
        self._advance()  # Consume 'end'

        if not groups:
            raise ParserError(
                "Expected at least one type definition in syntax block", start_token
            )

        return SyntaxBlock(
            groups=groups,
            line=start_token.line,
            column=start_token.column,
        )

    def _parse_generic_params(self) -> list[str] | None:
        """Parse optional generic parameters: [X, Y, Z].

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

    def _parse_compound_identifier_name(self) -> str:
        """Parse identifier name that may have postfix operator suffix.

        Handles compound identifiers like R+, R*, R~ used in abbreviations
        and schema names where the postfix operator is part of the name itself,
        not an operation on the identifier.

        Examples:
            R+ == {a, b : N | b > a}  # R+ is the abbreviation name
            R* == R+ o9 R+             # R* is the abbreviation name
            R~ == inv R                # R~ is the abbreviation name

        Returns:
            Compound identifier string (e.g., "R+", "R*", "R~")
        """
        if not self._match(TokenType.IDENTIFIER):
            raise ParserError("Expected identifier", self._current())

        name_token = self._advance()
        name = name_token.value

        # Check for postfix closure operators as part of the name
        # These are valid in definition contexts (not expression contexts)
        if self._match(TokenType.PLUS, TokenType.STAR, TokenType.TILDE):
            op_token = self._advance()
            name = name + op_token.value  # "R" + "+" → "R+"

        return name

    def _parse_abbreviation(self) -> Abbreviation:
        """Parse abbreviation: [X] name == expression or name == expression.

        Supports optional generic parameters.
        """
        start_token = self._current()

        # Check for generic parameters before name
        generic_params = self._parse_generic_params()

        # Parse name (may include postfix operator suffix like R+, R*, R~)
        name_token = self._current()  # Save for line/column info
        name = self._parse_compound_identifier_name()

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

        Syntax: axdef [X, Y] ... end
        Supports optional generic parameters and semicolon-separated declarations.
        """
        start_token = self._advance()  # Consume 'axdef'
        self._skip_newlines()

        # Check for generic parameters after 'axdef'
        generic_params = self._parse_generic_params()
        self._skip_newlines()

        declarations: list[Declaration] = []

        # Parse declarations until 'where' or 'end'
        while not self._at_end() and not self._match(TokenType.WHERE, TokenType.END):
            if self._match(TokenType.NEWLINE):
                self._advance()
                continue

            # Parse declaration: var : Type
            # Allow keywords as variable names in declarations (e.g., id, dom, ran)
            if (
                self._match(TokenType.IDENTIFIER)
                or self._is_keyword_usable_as_identifier()
            ):
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
        predicate_groups: list[list[Expr]] = []  # Default: no groups
        if self._match(TokenType.WHERE):
            self._advance()  # Consume 'where'
            self._skip_newlines()

            # Parse predicates grouped by blank lines
            predicate_groups = self._parse_predicate_groups((TokenType.END,))

        # Expect 'end'
        if not self._match(TokenType.END):
            raise ParserError("Expected 'end' to close axdef block", self._current())
        self._advance()  # Consume 'end'

        return AxDef(
            declarations=declarations,
            predicates=predicate_groups,
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

        # Parse declarations until 'where' or 'end'
        while not self._at_end() and not self._match(TokenType.WHERE, TokenType.END):
            if self._match(TokenType.NEWLINE):
                self._advance()
                continue

            # Parse declaration: var : Type
            # Allow keywords as variable names in declarations (e.g., id, dom, ran)
            if (
                self._match(TokenType.IDENTIFIER)
                or self._is_keyword_usable_as_identifier()
            ):
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
        predicate_groups: list[list[Expr]] = []  # Default: no groups
        if self._match(TokenType.WHERE):
            self._advance()  # Consume 'where'
            self._skip_newlines()

            # Parse predicates grouped by blank lines
            predicate_groups = self._parse_predicate_groups((TokenType.END,))

        # Expect 'end'
        if not self._match(TokenType.END):
            raise ParserError("Expected 'end' to close gendef block", self._current())
        self._advance()  # Consume 'end'

        return GenDef(
            generic_params=generic_params,
            declarations=declarations,
            predicates=predicate_groups,
            line=start_token.line,
            column=start_token.column,
        )

    def _parse_zed(self) -> Zed:
        """Parse zed block for Z notation constructs.

        Zed blocks contain unboxed Z notation paragraphs (\\begin{zed}...\\end{zed}).
        Syntax: zed <content> end

        The content can be:
        - Given types: given A, B, C
        - Free types: Type ::= branch1 | branch2
        - Abbreviations: Name == expression
        - Predicates: forall x : N | x >= 0

        Multiple constructs can appear in one zed block (mixed content).
        Single predicates are parsed as expressions (backward compatible).
        """
        start_token = self._advance()  # Consume 'zed'
        self._skip_newlines()

        items: list[DocumentItem] = []

        # Parse multiple statements until 'end'
        while not self._at_end() and not self._match(TokenType.END):
            if self._match(TokenType.NEWLINE):
                self._advance()
                continue

            # Check for given types
            if self._match(TokenType.GIVEN):
                items.append(self._parse_given_type())
                self._skip_newlines()
                continue

            # Check for abbreviations with generic parameters [X] Name == ...
            if self._match(TokenType.LBRACKET):
                items.append(self._parse_abbreviation())
                self._skip_newlines()
                continue

            # Check for free types or abbreviations (both start with IDENTIFIER)
            if self._match(TokenType.IDENTIFIER):
                # Save position to potentially backtrack
                saved_pos = self.pos

                # Try to parse as compound identifier (handles R, R+, R*, R~, etc.)
                try:
                    _ = self._parse_compound_identifier_name()

                    # Check what follows the identifier
                    if self._match(TokenType.FREE_TYPE):
                        # It's a free type, backtrack and parse properly
                        self.pos = saved_pos
                        items.append(self._parse_free_type())
                    elif self._match(TokenType.ABBREV):
                        # It's an abbreviation, backtrack and parse properly
                        self.pos = saved_pos
                        items.append(self._parse_abbreviation())
                    else:
                        # Not a recognized Z notation construct, backtrack and
                        # parse as expression
                        self.pos = saved_pos
                        items.append(self._parse_expr())
                except ParserError:
                    # Failed to parse compound identifier, backtrack and
                    # parse as expression
                    self.pos = saved_pos
                    items.append(self._parse_expr())

                self._skip_newlines()
                continue

            # Otherwise, parse as expression (predicate)
            items.append(self._parse_expr())
            self._skip_newlines()
            break  # Single expression mode (backward compatible)

        # Expect 'end'
        if not self._match(TokenType.END):
            raise ParserError("Expected 'end' to close zed block", self._current())
        self._advance()  # Consume 'end'

        # If single item and it's an expression, return Zed(content=expr)
        # for backward compatibility. Otherwise, wrap in Document
        if len(items) == 1 and isinstance(items[0], Expr):
            return Zed(
                content=items[0],
                line=start_token.line,
                column=start_token.column,
            )
        # Multiple items or non-expression items - wrap in Document
        doc = Document(
            items=items,
            line=start_token.line,
            column=start_token.column,
        )
        return Zed(
            content=doc,
            line=start_token.line,
            column=start_token.column,
        )

    def _parse_schema(self) -> Schema:
        """Parse schema definition block.

        Syntax:
            schema Name[X, Y] ... end (named with generics)
            schema Name ... end (named)
            schema ... end (anonymous)

        Supports optional generic parameters and semicolon-separated declarations.
        """
        start_token = self._advance()  # Consume 'schema'

        # Parse optional schema name
        # Note: May include postfix operator suffix like S+, S*, S~
        # (partial support, GitHub #3 open)
        name: str | None = None
        generic_params: list[str] | None = None

        if self._match(TokenType.IDENTIFIER):
            name = self._parse_compound_identifier_name()
            # Check for generic parameters after name
            generic_params = self._parse_generic_params()

        self._skip_newlines()

        declarations: list[Declaration] = []

        # Parse declarations until 'where' or 'end'
        while not self._at_end() and not self._match(TokenType.WHERE, TokenType.END):
            if self._match(TokenType.NEWLINE):
                self._advance()
                continue

            # Parse declaration: var : Type
            # Allow keywords as variable names in declarations (e.g., id, dom, ran)
            if (
                self._match(TokenType.IDENTIFIER)
                or self._is_keyword_usable_as_identifier()
            ):
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
        predicate_groups: list[list[Expr]] = []  # Default: no groups
        if self._match(TokenType.WHERE):
            self._advance()  # Consume 'where'
            self._skip_newlines()

            # Parse predicates grouped by blank lines
            predicate_groups = self._parse_predicate_groups((TokenType.END,))

        # Expect 'end'
        if not self._match(TokenType.END):
            raise ParserError("Expected 'end' to close schema block", self._current())
        self._advance()  # Consume 'end'

        return Schema(
            name=name,
            declarations=declarations,
            predicates=predicate_groups,
            generic_params=generic_params,
            line=start_token.line,
            column=start_token.column,
        )

    def _parse_proof_tree(self) -> ProofTree:
        """Parse proof tree with Path C syntax (conclusion with supporting proof).

        Supports top-level CASE analysis where proof starts with cases.
        """
        start_token = self._advance()  # Consume 'PROOF:'
        self._skip_newlines()

        if self._at_end() or self._is_structural_token():
            raise ParserError("Expected proof node after PROOF:", self._current())

        # Check if first item is a case keyword (top-level case analysis)
        if self._match(TokenType.IDENTIFIER) and self._current().value == "case":
            # Parse all top-level cases
            cases: list[CaseAnalysis] = []

            while (
                not self._at_end()
                and not self._is_structural_token()
                and self._match(TokenType.IDENTIFIER)
                and self._current().value == "case"
            ):
                case_analysis = self._parse_case_analysis(
                    base_indent=0, parent_indent=None
                )
                cases.append(case_analysis)
                self._skip_newlines()

            # Check if there's a final conclusion after the cases
            final_conclusion_expr: Expr | None = None
            final_justification: str | None = None

            if not self._at_end() and not self._is_structural_token():
                # Parse potential final conclusion (e.g., "q [or elim]")
                final_conclusion_node = self._parse_proof_node(
                    base_indent=0, parent_indent=None
                )
                final_conclusion_expr = final_conclusion_node.expression
                final_justification = final_conclusion_node.justification

            # Create synthetic conclusion node to wrap the cases
            # Use the final conclusion if present, otherwise placeholder
            if final_conclusion_expr is None:
                final_conclusion_expr = Identifier(
                    name="[case_analysis]",
                    line=start_token.line,
                    column=start_token.column,
                )
                final_justification = "case analysis"

            # Type hint for children: explicitly cast to expected union type
            children_list: list[ProofNode | CaseAnalysis] = list(cases)

            conclusion = ProofNode(
                expression=final_conclusion_expr,
                justification=final_justification,
                label=None,
                is_assumption=False,
                is_sibling=False,
                children=children_list,
                indent_level=0,
                line=start_token.line,
                column=start_token.column,
            )
        else:
            # Standard proof: parse the conclusion node
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

        # Check for ellipsis ... (steps omitted in proof)
        if self._match(TokenType.ELLIPSIS):
            ellipsis_token = self._advance()
            # Create a text node representing omitted steps
            expr: Expr = Identifier(
                name="...",
                line=ellipsis_token.line,
                column=ellipsis_token.column,
            )
        else:
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
                # Join tokens smartly: add spaces only between consecutive identifiers
                justification = self._smart_join_justification(just_parts)
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
        self, base_indent: int, parent_indent: int | None
    ) -> CaseAnalysis:
        """Parse case analysis: case name: followed by proof steps.

        parent_indent can be None for top-level cases.
        """
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
