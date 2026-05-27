"""Parser for txt2tex - converts tokens into AST."""

from __future__ import annotations

from typing import ClassVar

from txt2tex.ast_nodes import (
    Declaration,
    Document,
    DocumentItem,
    Expr,
    SchemaInclusion,
    TitleMetadata,
)
from txt2tex.parser_pkg._base import ParserBase, ParserError as ParserError
from txt2tex.parser_pkg.algebra import (
    _AlgebraParser,  # pyright: ignore[reportPrivateUsage]
)
from txt2tex.parser_pkg.errors import (
    _ErrorsParser,  # pyright: ignore[reportPrivateUsage]
)
from txt2tex.parser_pkg.expressions import (
    _ExpressionsParser,  # pyright: ignore[reportPrivateUsage]
)
from txt2tex.parser_pkg.lexer_state import (
    _LexerStateParser,  # pyright: ignore[reportPrivateUsage]
)
from txt2tex.parser_pkg.paragraphs import (
    _ParagraphsParser,  # pyright: ignore[reportPrivateUsage]
)
from txt2tex.parser_pkg.proofs import (
    _ProofsParser,  # pyright: ignore[reportPrivateUsage]
)
from txt2tex.parser_pkg.schemas import (
    _SchemasParser,  # pyright: ignore[reportPrivateUsage]
)
from txt2tex.parser_pkg.text_blocks import (
    _TextBlocksParser,  # pyright: ignore[reportPrivateUsage]
)
from txt2tex.parser_pkg.types import (
    _TypesParser,  # pyright: ignore[reportPrivateUsage]
)
from txt2tex.tokens import Token, TokenType


class Parser(
    _ParagraphsParser,
    _SchemasParser,
    _ProofsParser,
    _AlgebraParser,
    _ExpressionsParser,
    _TypesParser,
    _TextBlocksParser,
    _LexerStateParser,
    _ErrorsParser,
    ParserBase,
):
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
    _in_schema_expr_context: bool
    _in_comparison_rhs: bool
    _current_quantifier_vars: set[str]
    _in_relational_context: bool

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
        # Track whether we're parsing a schema-expression context (RHS of defs,
        # schema inclusion body) where ';' is schema composition, not a separator.
        self._in_schema_expr_context = False
        # Track whether we're parsing the RHS of a comparison operator inside
        # a comprehension body.  Used to allow field projections like 's.name'
        # in 'c.class = s.name }' even though the RBRACE follows immediately.
        self._in_comparison_rhs = False
        # All variable names declared in the current comprehension/quantifier
        # schema-text (across the entire semicolon chain).  Used by _parse_postfix
        # to distinguish bullet `.` from named-field projection: `.IDENT` where
        # IDENT is a declared variable cannot be a field selector (Z RM §3.16).
        self._current_quantifier_vars: set[str] = set()
        # True when parsing a relational-algebra argument position (inside sigma,
        # pi, join, div, group, ungroup operands).  Governs disambiguation of
        # Expr[new/old] postfix: RelationRename when True, SchemaRename when False.
        self._in_relational_context: bool = False

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
        # or horizontal schema definition (identifier [generics]? defs ...)
        # Note: Partial support for compound identifiers like "R+ =="
        # (GitHub #3 still open)
        #
        # Prefix-operator keywords (F, P, F1, P1) can also be abbreviation
        # names when followed by ==.  Check for that before falling through
        # to expression parsing, which would consume them as operators.
        if self._match(
            TokenType.IDENTIFIER,
            TokenType.FINSET,
            TokenType.FINSET1,
            TokenType.POWER,
            TokenType.POWER1,
        ):
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
            # Detect horizontal schema definition: Name defs ... or Name[X] defs ...
            is_horiz = next_token.type == TokenType.DEFS or (
                next_token.type == TokenType.LBRACKET
                and self._scan_for_defs_after_brackets(offset=1)
            )
            if is_horiz:
                first_hd = self._parse_horiz_def()
                self._skip_newlines()
                if not self._at_end():
                    items_with_hd: list[DocumentItem] = [first_hd]
                    while not self._at_end():
                        items_with_hd.append(self._parse_document_item())
                        self._skip_newlines()
                    return Document(
                        items=items_with_hd,
                        title_metadata=None,
                        parts_format=parts_format,
                        bibliography_metadata=None,
                        line=first_line,
                        column=1,
                    )
                return Document(
                    items=[first_hd],
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
                    self._reject_stray_slash()
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
            self._reject_stray_slash()
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
            TokenType.B_BLOCK,
            TokenType.RAW_LATEX_BLOCK,
            TokenType.PAGEBREAK,
            TokenType.LINEBREAK,
            TokenType.CONTENTS,
            TokenType.PARTS,
            TokenType.ARGUE,  # Both EQUIV: and ARGUE: map to this token
            TokenType.EQUAL,  # EQUAL: expression equality chain
            TokenType.INFRULE,
            TokenType.GIVEN,
            TokenType.AXDEF,
            TokenType.GENDEF,
            TokenType.ZED,
            TokenType.SCHEMA,
            TokenType.SYNTAX,
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
        if self._match(TokenType.ARGUE):  # Handles both EQUIV: and ARGUE: keywords
            return self._parse_argue_chain(connector="iff")
        if self._match(TokenType.EQUAL):  # Expression equality chain
            return self._parse_argue_chain(connector="eq")
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
            return self._parse_paragraph_coalesced()
        if self._match(TokenType.PURETEXT):
            return self._parse_pure_paragraph()
        if self._match(TokenType.LATEX):
            return self._parse_latex_block()
        if self._match(TokenType.RAW_LATEX_BLOCK):
            return self._parse_raw_latex_block()
        if self._match(TokenType.B_BLOCK):
            return self._parse_b_block()
        if self._match(TokenType.PAGEBREAK):
            return self._parse_pagebreak()
        if self._match(TokenType.LINEBREAK):
            return self._parse_linebreak()
        if self._match(TokenType.CONTENTS):
            return self._parse_contents()
        if self._match(TokenType.PARTS):
            return self._parse_parts_directive()

        # Check for abbreviation (identifier == expr) or free type (identifier ::= ...)
        # or horizontal schema definition (identifier [generics]? defs ...)
        if self._match(
            TokenType.IDENTIFIER,
            TokenType.FINSET,
            TokenType.FINSET1,
            TokenType.POWER,
            TokenType.POWER1,
        ):
            return self._parse_identifier_document_item()

        # Check for abbreviation with generic parameters [X, Y] Name == expression
        # Note: Bag literals [[x]] start with [[ which is distinct
        if self._match(TokenType.LBRACKET):
            return self._parse_bracket_document_item()

        # Default: parse as expression
        return self._parse_expr()

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
            TokenType.GROUP,  # group (relational operator; legal as attr name)
            TokenType.UNGROUP,  # ungroup (relational operator; legal as attr name)
        )

    # Operator keywords whose LaTeX expansion (e.g. \id, \dom) collides
    # with declaration-name use. Even though the parser can accept these
    # as attribute names, the LaTeX generator emits the operator symbol,
    # which fuzz then rejects in declaration position. Reject at the
    # parser level with a clear error.
    _RESERVED_DECL_NAMES: ClassVar[frozenset[str]] = frozenset(
        {"id", "dom", "ran", "inv", "comp", "mod", "bigcup", "bigcap", "filter"}
    )

    def _scan_for_colon_before_newline(self) -> bool:
        """Lookahead scan: return True if ':' appears before NEWLINE/WHERE/END/EOF.

        Used to disambiguate a bare identifier line from a typed declaration.
        ``count, count' : N`` returns True (typed declaration).
        ``Counter``           returns False (bare schema inclusion).
        Commas and identifiers between the current position and the colon are
        allowed — they are the multi-name variable list.

        Bracket depth is tracked so a COLON inside ``[...]`` (e.g., in a
        type expression within generic args) is not mistaken for the
        declaration colon.  Only a COLON at depth 0 signals a typed declaration.
        """
        offset = 0
        depth = 0
        while True:
            tok = self._peek_ahead(offset)
            if tok.type in (
                TokenType.NEWLINE,
                TokenType.WHERE,
                TokenType.END,
                TokenType.SEMICOLON,
                TokenType.EOF,
            ):
                return False
            if tok.type == TokenType.LBRACKET:
                depth += 1
            elif tok.type == TokenType.RBRACKET:
                depth -= 1
            elif tok.type == TokenType.COLON and depth == 0:
                return True
            offset += 1

    def _parse_inclusion_generic_args(self) -> list[Expr] | None:
        """Parse optional generic instantiation arguments: [expr, expr, ...].

        Returns None when no '[' is present.  Consumes the brackets and their
        contents when present (e.g., ``[Int]``, ``[N cross N]``).

        Raises ParserError for:
        - Empty brackets ``[]`` or comma-only ``[,]`` (Z RM §3.9 requires ≥1 expr)
        - Unclosed bracket — error points at the opening ``[``
        """
        if not self._match(TokenType.LBRACKET):
            return None
        open_tok = self._advance()  # consume '[', save for error reporting
        args: list[Expr] = []

        terminators = (
            TokenType.NEWLINE,
            TokenType.WHERE,
            TokenType.END,
            TokenType.EOF,
        )

        while not self._match(TokenType.RBRACKET):
            if self._at_end() or self._match(*terminators):
                raise ParserError("Unclosed '[' in generic argument list", open_tok)
            if self._match(TokenType.COMMA):
                if not args:
                    # Leading comma — no expression before it
                    raise ParserError(
                        "Expected type expression in generic argument list",
                        self._current(),
                    )
                self._advance()
                # Trailing comma before ']'
                if self._match(TokenType.RBRACKET):
                    raise ParserError(
                        "Expected type expression in generic argument list",
                        self._current(),
                    )
                continue
            args.append(self._parse_expr())

        if not args:
            raise ParserError(
                "Empty generic argument list — at least one type expression required",
                open_tok,
            )

        self._advance()  # consume ']'
        return args

    def _parse_declaration_or_inclusion(
        self,
    ) -> Declaration | SchemaInclusion | list[Declaration]:
        """Parse one declaration line or schema-inclusion line.

        Five forms:
        1. ``pk name1, name2, ... : Type``  → list[Declaration] with is_primary_key=True
        2. ``Delta Name [generic-args]?``   → SchemaInclusion(decoration="delta")
        3. ``Xi Name [generic-args]?``      → SchemaInclusion(decoration="xi")
        4. ``name1, name2, ... : Type``     → list[Declaration]  (typed, ≥1 item)
        5. ``Name [generic-args]?``         → SchemaInclusion(decoration=None)
           (bare inclusion — only when no ':' follows on the same line)

        Returns a list of Declarations for the typed form so the caller can
        extend its declaration list directly; returns a single SchemaInclusion
        otherwise.
        """
        start_tok = self._current()

        # --- pk prefix: primary-key declaration ---
        if self._match(TokenType.PK):
            pk_tok = self._advance()  # consume 'pk'
            cur = self._current()
            # Reject pk before Delta/Xi or bare-schema inclusion (no attribute name)
            if self._match(TokenType.DELTA):
                raise ParserError(
                    "pk cannot precede Delta inclusion"
                    " (no attribute name to underline)",
                    cur,
                )
            if self._match(TokenType.XI):
                raise ParserError(
                    "pk cannot precede Xi inclusion (no attribute name to underline)",
                    cur,
                )
            # Must have an identifier (attribute name) followed eventually by ':'
            is_ident = self._match(TokenType.IDENTIFIER)
            is_kw_as_ident = self._is_keyword_usable_as_identifier()
            if not is_ident and not is_kw_as_ident:
                raise ParserError(
                    f"pk must be followed by an attribute name,"
                    f" got {cur.type.name} ({cur.value!r})",
                    cur,
                )
            if not self._scan_for_colon_before_newline():
                raise ParserError(
                    "pk declaration requires a type annotation (name : Type)",
                    cur,
                )
            pk_var_tokens: list[Token] = []
            pk_var_tok = self._current()
            self._reject_reserved_decl_name(pk_var_tok)
            pk_var_tokens.append(pk_var_tok)
            self._advance()
            while self._match(TokenType.COMMA):
                self._advance()  # consume ','
                if not (
                    self._match(TokenType.IDENTIFIER)
                    or self._is_keyword_usable_as_identifier()
                ):
                    raise ParserError(
                        "Expected variable name after ','", self._current()
                    )
                self._reject_reserved_decl_name(self._current())
                pk_var_tokens.append(self._current())
                self._advance()
            if not self._match(TokenType.COLON):
                raise ParserError("Expected ':' in pk declaration", self._current())
            self._advance()  # consume ':'
            pk_type_expr = self._parse_expr()
            return [
                Declaration(
                    variable=vt.value,
                    type_expr=pk_type_expr,
                    is_primary_key=True,
                    line=pk_tok.line,
                    column=pk_tok.column,
                )
                for vt in pk_var_tokens
            ]

        # --- Delta / Xi decorated inclusion ---
        if self._match(TokenType.DELTA, TokenType.XI):
            decoration = "delta" if self._match(TokenType.DELTA) else "xi"
            kw = "Delta" if decoration == "delta" else "Xi"
            self._advance()  # consume Delta / Xi
            # Must be followed by an identifier (schema name)
            if not self._match(TokenType.IDENTIFIER):
                cur = self._current()
                raise ParserError(
                    f"Expected schema name after {kw},"
                    f" got {cur.type.name} ({cur.value!r})",
                    cur,
                )
            name_tok = self._advance()
            generics = self._parse_inclusion_generic_args()
            return SchemaInclusion(
                name=name_tok.value,
                decoration=decoration,
                generics=generics,
                line=start_tok.line,
                column=start_tok.column,
            )

        # --- IDENTIFIER (or keyword-as-identifier) ---
        # Scan ahead to decide: typed declaration vs bare inclusion.
        if not self._scan_for_colon_before_newline():
            # No colon before newline → bare schema inclusion
            name_tok = self._advance()
            generics = self._parse_inclusion_generic_args()
            return SchemaInclusion(
                name=name_tok.value,
                decoration=None,
                generics=generics,
                line=start_tok.line,
                column=start_tok.column,
            )

        # Colon found → typed declaration (original path)
        var_tokens: list[Token] = []
        var_tok = self._current()
        self._reject_reserved_decl_name(var_tok)
        var_tokens.append(var_tok)
        self._advance()

        while self._match(TokenType.COMMA):
            self._advance()  # consume ','
            if not (
                self._match(TokenType.IDENTIFIER)
                or self._is_keyword_usable_as_identifier()
            ):
                raise ParserError("Expected variable name after ','", self._current())
            self._reject_reserved_decl_name(self._current())
            var_tokens.append(self._current())
            self._advance()

        if not self._match(TokenType.COLON):
            raise ParserError("Expected ':' in declaration", self._current())
        self._advance()  # consume ':'

        type_expr = self._parse_expr()

        return [
            Declaration(
                variable=vt.value,
                type_expr=type_expr,
                line=vt.line,
                column=vt.column,
            )
            for vt in var_tokens
        ]

    def _scan_for_defs_after_brackets(self, offset: int) -> bool:
        """Return True when a balanced bracket group starting at ``offset`` is
        followed immediately by a DEFS token.

        Used for lookahead disambiguation: ``Name[X, Y] defs ...`` is a
        horizontal definition, not an expression.  The bracket group at
        ``offset`` must start with LBRACKET; the scan terminates as soon as
        bracket depth returns to zero and checks the next token for DEFS.

        Returns False on any unexpected terminator (EOF, NEWLINE, etc.).
        Generic parameters must be on the same line as the name — a NEWLINE
        inside the bracket group ends the scan and returns False.
        """
        tok = self._peek_ahead(offset)
        if tok.type != TokenType.LBRACKET:
            return False
        depth = 1
        offset += 1
        while depth > 0:
            tok = self._peek_ahead(offset)
            if tok.type in (TokenType.EOF, TokenType.NEWLINE):
                return False
            if tok.type == TokenType.LBRACKET:
                depth += 1
            elif tok.type == TokenType.RBRACKET:
                depth -= 1
            offset += 1
        return self._peek_ahead(offset).type == TokenType.DEFS
