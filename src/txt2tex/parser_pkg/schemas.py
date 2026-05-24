"""Parser rules for schema constructs.

Covers: Schema, HorizDef (with helper ``_parse_horiz_def_rhs`` and
``_parse_horiz_def_generic_params``), inline schema text
``_parse_schema_text``, schema-calculus operators
(``_parse_schema_pipe``, ``_parse_schema_compose``,
``_parse_schema_project_hide``), and the dispatcher
``_parse_schema_rename_or_generic`` plus the renaming form
``_parse_schema_rename``.

This mixin is composed into :class:`Parser` via multiple inheritance.
Method bodies are byte-identical to their counterparts in the
pre-refactor monolithic ``parser.py``; only their file location has
changed.
"""

from __future__ import annotations

from txt2tex.ast_nodes import (
    Declaration,
    Expr,
    GenericInstantiation,
    HorizDef,
    Schema,
    SchemaCompose,
    SchemaHide,
    SchemaInclusion,
    SchemaPipe,
    SchemaProject,
    SchemaRename,
    SchemaText,
)
from txt2tex.parser_pkg._base import ParserBase, ParserError
from txt2tex.tokens import TokenType


class _SchemasParser(ParserBase):  # pyright: ignore[reportUnusedClass]
    """Mixin: rules for schema constructs."""

    def _parse_schema_rename_or_generic(
        self, base: Expr
    ) -> GenericInstantiation | SchemaRename:
        """Consume '[' then dispatch to rename or generic instantiation.

        Disambiguation rule (Z RM §3.11): scan the bracket contents at
        bracket depth 0.  If any SLASH token appears before the matching
        ']', parse as schema rename pairs ``S[new/old, ...]``.  Otherwise,
        parse as a generic type instantiation ``S[T, ...]``.

        The '[' has NOT been consumed on entry; this method consumes it and
        the matching ']'.
        """
        if self._bracket_contains_slash():
            return self._parse_schema_rename(base)
        return self._parse_generic_instantiation(base)

    def _parse_schema_rename(self, schema: Expr) -> SchemaRename:
        """Parse schema rename S[old/new, ...] — '[' not yet consumed.

        Grammar:
            rename ::= '[' pair (',' pair)* ']'
            pair   ::= IDENTIFIER '/' IDENTIFIER

        Raises ParserError for:
        - Empty bracket ``S[]``
        - Missing source name ``S[/b]``
        - Missing slash ``S[a b]``
        - Missing target name ``S[a/]``
        - Trailing slash ``S[a/b/]``
        - Trailing comma ``S[a/b,]``
        """
        open_tok = self._advance()  # Consume '['

        pairs: list[tuple[str, str]] = []

        while not self._match(TokenType.RBRACKET):
            if self._at_end() or self._match(TokenType.NEWLINE, TokenType.EOF):
                raise ParserError(
                    "unclosed '[' in schema rename",
                    open_tok,
                )

            # Expect source identifier
            if not self._match(TokenType.IDENTIFIER):
                cur = self._current()
                raise ParserError(
                    f"expected identifier before '/' in schema rename pair,"
                    f" got {cur.type.name} ({cur.value!r})",
                    cur,
                )
            src_tok = self._advance()
            src = src_tok.value

            # Expect '/'
            if not self._match(TokenType.SLASH):
                cur = self._current()
                raise ParserError(
                    f"expected '/' in schema rename pair after {src!r},"
                    f" got {cur.type.name} ({cur.value!r})",
                    cur,
                )
            self._advance()  # Consume '/'

            # Expect target identifier
            if not self._match(TokenType.IDENTIFIER):
                cur = self._current()
                raise ParserError(
                    f"expected identifier after '/' in schema rename pair,"
                    f" got {cur.type.name} ({cur.value!r})",
                    cur,
                )
            tgt_tok = self._advance()
            tgt = tgt_tok.value

            pairs.append((src, tgt))

            # Optional comma separator
            if self._match(TokenType.COMMA):
                self._advance()  # Consume ','
                # Trailing comma check: next is ']'
                if self._match(TokenType.RBRACKET):
                    raise ParserError(
                        "expected rename pair after ',' in schema rename",
                        self._current(),
                    )
                continue

            # If not comma and not ']', something is wrong
            if not self._match(TokenType.RBRACKET):
                cur = self._current()
                raise ParserError(
                    f"expected ',' or ']' in schema rename,"
                    f" got {cur.type.name} ({cur.value!r})",
                    cur,
                )

        if not pairs:
            raise ParserError(
                "schema rename requires at least one pair",
                open_tok,
            )

        if not self._match(TokenType.RBRACKET):
            raise ParserError(
                "expected ']' to close schema rename",
                self._current(),
            )
        self._advance()  # Consume ']'

        return SchemaRename(
            schema=schema,
            pairs=pairs,
            line=open_tok.line,
            column=open_tok.column,
        )

    def _parse_horiz_def_generic_params(self) -> list[str] | None:
        """Parse optional generic LHS parameters for a horizontal definition.

        Identical to ``_parse_generic_params`` but records the opening bracket
        token for an improved error message when the bracket is not closed.

        Returns None when no ``[`` is present.
        """
        if not self._match(TokenType.LBRACKET):
            return None

        open_tok = self._advance()  # Consume '[', save for error reporting
        params: list[str] = []

        while not self._match(TokenType.RBRACKET) and not self._at_end():
            if self._match(TokenType.COMMA):
                self._advance()  # Skip comma
                continue

            if self._match(TokenType.NEWLINE, TokenType.EOF):
                raise ParserError(
                    "unclosed '[' in generic parameter list for horizontal definition",
                    open_tok,
                )

            if not self._match(TokenType.IDENTIFIER):
                raise ParserError(
                    "expected type parameter name in generic list",
                    self._current(),
                )

            params.append(self._current().value)
            self._advance()

        if not self._match(TokenType.RBRACKET):
            raise ParserError(
                "unclosed '[' in generic parameter list for horizontal definition",
                open_tok,
            )
        self._advance()  # Consume ']'

        return params if params else None

    # ------------------------------------------------------------------
    # Schema-calculus operators (Phase 3.2 — Z RM §3.11)
    # ------------------------------------------------------------------
    # Precedence (tightest to loosest):
    #   1. hide / project   (_parse_schema_project_hide)
    #   2. composition ;    (_parse_schema_compose)
    #   3. piping >>        (_parse_schema_pipe)
    #
    # These methods are only entered from _parse_horiz_def_rhs (and any
    # future schema-expression context) when _in_schema_expr_context is
    # True.  Inside axdef / schema / gendef bodies SEMICOLON remains a
    # plain declaration separator — those loops never call these methods.
    # ------------------------------------------------------------------

    def _parse_schema_pipe(self) -> Expr:
        """Parse schema piping ``S >> T`` (lowest schema-calculus precedence).

        Left-associative: ``A >> B >> C`` parses as ``(A >> B) >> C``.
        """
        left = self._parse_schema_compose()

        while self._match(TokenType.PIPE_PIPE):
            op_tok = self._advance()
            right = self._parse_schema_compose()
            left = SchemaPipe(
                left=left,
                right=right,
                line=op_tok.line,
                column=op_tok.column,
            )

        return left

    def _parse_schema_compose(self) -> Expr:
        """Parse schema composition ``S ; T`` (middle schema-calculus precedence).

        Left-associative: ``A ; B ; C`` parses as ``(A ; B) ; C``.
        SEMICOLON is consumed here only because _in_schema_expr_context is True;
        callers in declaration-loop contexts never invoke this method.
        """
        left = self._parse_schema_project_hide()

        while self._match(TokenType.SEMICOLON):
            op_tok = self._advance()
            right = self._parse_schema_project_hide()
            left = SchemaCompose(
                left=left,
                right=right,
                line=op_tok.line,
                column=op_tok.column,
            )

        return left

    def _parse_schema_project_hide(self) -> Expr:
        """Parse schema hiding and projection (tightest schema-calculus precedence).

        ``S hide (x, y)``  — existentially quantify named components.
        ``S project T``    — project S onto the signature of T.

        Both are left-associative and at the same precedence level, so they
        chain: ``S hide (x) project T`` is ``(S hide (x)) project T``.
        """
        # Start with a base schema expression (ordinary expression precedence).
        left = self._parse_expr()

        while self._match(TokenType.HIDE, TokenType.PROJECT):
            op_tok = self._advance()

            if op_tok.type == TokenType.HIDE:
                # Expect '(' name, name, ... ')'
                if not self._match(TokenType.LPAREN):
                    raise ParserError(
                        "expected '(' after 'hide' in schema hiding expression",
                        self._current(),
                    )
                self._advance()  # Consume '('

                names: list[str] = []
                while not self._match(TokenType.RPAREN):
                    if self._at_end():
                        raise ParserError(
                            "unclosed '(' in 'hide' expression — expected ')'",
                            op_tok,
                        )
                    if self._match(TokenType.COMMA):
                        self._advance()
                        continue
                    if not self._match(TokenType.IDENTIFIER):
                        cur = self._current()
                        raise ParserError(
                            f"expected identifier in 'hide' name list,"
                            f" got {cur.type.name} ({cur.value!r})",
                            cur,
                        )
                    names.append(self._advance().value)

                if not names:
                    raise ParserError(
                        "'hide' requires at least one component name", op_tok
                    )
                self._advance()  # Consume ')'

                left = SchemaHide(
                    schema=left,
                    names=names,
                    line=op_tok.line,
                    column=op_tok.column,
                )

            else:  # PROJECT
                right = self._parse_expr()
                left = SchemaProject(
                    left=left,
                    right=right,
                    line=op_tok.line,
                    column=op_tok.column,
                )

        return left

    def _parse_horiz_def(self) -> HorizDef:
        """Parse horizontal schema definition: Name [X, Y]? defs RHS.

        Per Z RM §3.8, the RHS is one of:
        - A schema reference — an identifier, possibly Phase-0 decorated
          (e.g. ``Counter'``, ``Delta Counter``).
        - An inline schema text ``[ decl-list | pred-list ]``.
        - A schema-calculus expression (Phase 3.2): S ; T, S >> T,
          S hide (x, y), S project T, and combinations.
        """
        start_tok = self._current()

        # Consume the LHS name
        if not self._match(TokenType.IDENTIFIER):
            raise ParserError(
                "expected schema name for horizontal definition", start_tok
            )
        name_tok = self._advance()
        name = name_tok.value

        # Optional generic parameters on the LHS: Name[X, Y]
        generics = self._parse_horiz_def_generic_params()

        # Consume 'defs'
        if not self._match(TokenType.DEFS):
            raise ParserError(
                "expected 'defs' in horizontal schema definition",
                self._current(),
            )
        self._advance()  # Consume 'defs'

        # --- Parse RHS ---
        if self._at_end() or self._match(TokenType.NEWLINE):
            raise ParserError(
                "expected RHS after 'defs' in horizontal schema definition",
                self._current(),
            )

        body: Expr | SchemaInclusion
        if self._match(TokenType.LBRACKET):
            body = self._parse_schema_text()
        else:
            # Enable schema-expression context so ';' becomes composition.
            prev = self._in_schema_expr_context
            self._in_schema_expr_context = True
            try:
                body = self._parse_horiz_def_rhs()
            finally:
                self._in_schema_expr_context = prev

        return HorizDef(
            name=name,
            generics=generics,
            body=body,
            line=start_tok.line,
            column=start_tok.column,
        )

    def _parse_horiz_def_rhs(self) -> Expr | SchemaInclusion:
        """Parse a schema expression on the RHS of a horizontal definition.

        Accepts:
        - A plain identifier (possibly Phase-0 decorated).
        - ``Delta Name [generics]?`` or ``Xi Name [generics]?`` — schema
          inclusions used as the RHS (legal in Z RM §3.8 examples).
        - A generic instantiation: ``Name[T]`` produced by ``_parse_atom``.
        - A schema-calculus expression (Phase 3.2): ``S ; T``, ``S >> T``,
          ``S hide (x, y)``, ``S project T``, and combinations.

        Returns an Expr node or SchemaInclusion for Delta/Xi decorated forms.
        Delta/Xi are handled first because they begin with reserved keywords
        that would otherwise stop expression parsing.
        """
        # Delta / Xi decorated reference → SchemaInclusion
        # These are handled before schema-calculus parsing because Delta/Xi
        # are keywords that mark the decorated form; schema-calculus operators
        # cannot apply to a bare Delta/Xi keyword start.
        if self._match(TokenType.DELTA, TokenType.XI):
            start_tok = self._current()
            decoration = "delta" if self._match(TokenType.DELTA) else "xi"
            self._advance()  # Consume Delta / Xi
            if not self._match(TokenType.IDENTIFIER):
                cur = self._current()
                kw = "Delta" if decoration == "delta" else "Xi"
                raise ParserError(
                    f"expected schema name after {kw},"
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

        # Schema-calculus expression (possibly just a plain identifier).
        # _parse_schema_pipe is the entry point of the schema-calculus
        # precedence cascade (pipe < compose < hide/project < base expr).
        return self._parse_schema_pipe()

    def _parse_schema_text(self) -> SchemaText:
        r"""Parse an inline schema text: ``[ decl-list | pred-list ]``.

        The bracket has already been detected but NOT consumed when this
        method is called.  Grammar:

            schema_text ::= '[' decl (';' decl)* '|' pred (';' pred)* ']'

        The declaration forms are the same three supported inside schema and
        axdef bodies.  Multiple predicates are separated by ``;``.
        """
        open_tok = self._advance()  # Consume '['

        # --- Declaration section ---
        declarations: list[Declaration | SchemaInclusion] = []

        while not self._at_end() and not self._match(
            TokenType.PIPE, TokenType.RBRACKET
        ):
            if self._match(TokenType.NEWLINE):
                self._advance()
                continue
            if self._match(TokenType.SEMICOLON):
                self._advance()  # Declaration separator
                continue

            # pk has no relation name in inline schema text — reject with clear message.
            if self._match(TokenType.PK):
                raise ParserError(
                    "Primary-key annotation requires a named schema;"
                    " inline schema text is anonymous",
                    self._current(),
                )

            if (
                self._match(TokenType.DELTA, TokenType.XI)
                or self._match(TokenType.IDENTIFIER)
                or self._is_keyword_usable_as_identifier()
            ):
                result = self._parse_declaration_or_inclusion()
                if isinstance(result, list):
                    declarations.extend(result)
                else:
                    declarations.append(result)
            else:
                cur = self._current()
                raise ParserError(
                    f"expected declaration or '|' in inline schema text,"
                    f" got {cur.type.name} ({cur.value!r})",
                    cur,
                )

        # FIX 2: empty declaration list is a syntax error
        if not declarations:
            raise ParserError(
                "inline schema text requires at least one declaration",
                open_tok,
            )

        # --- Predicate separator '|' ---
        if self._at_end():
            raise ParserError(
                "unclosed inline schema text '[' — expected '|' then ']'", open_tok
            )
        if self._match(TokenType.RBRACKET):
            # No predicate section — parse as [ decls ] (no pipe)
            self._advance()  # Consume ']'
            return SchemaText(
                declarations=declarations,
                predicates=[],
                line=open_tok.line,
                column=open_tok.column,
            )

        self._advance()  # Consume '|'

        # --- Predicate section (flat list; ';' and newlines are separators) ---
        predicates: list[Expr] = []

        while not self._at_end() and not self._match(TokenType.RBRACKET):
            if self._match(TokenType.NEWLINE):
                self._advance()
                continue
            if self._match(TokenType.SEMICOLON):
                self._advance()
                continue

            predicates.append(self._parse_expr())

        if not self._match(TokenType.RBRACKET):
            raise ParserError(
                "unclosed inline schema text '[' — expected closing ']'", open_tok
            )
        self._advance()  # Consume ']'

        return SchemaText(
            declarations=declarations,
            predicates=predicates,
            line=open_tok.line,
            column=open_tok.column,
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

        declarations: list[Declaration | SchemaInclusion] = []

        # Parse declarations until 'where' or 'end'
        while not self._at_end() and not self._match(TokenType.WHERE, TokenType.END):
            if self._match(TokenType.NEWLINE):
                self._advance()
                continue

            # pk requires a named schema — reject it in anonymous schemas.
            if self._match(TokenType.PK) and name is None:
                raise ParserError(
                    "Primary-key annotation requires a named schema;"
                    " anonymous schemas have no relation name for PK notation",
                    self._current(),
                )

            # Four forms: pk prefix (named schemas only), Delta/Xi inclusion,
            # bare inclusion, typed declaration.
            if (
                self._match(TokenType.PK)
                or self._match(TokenType.DELTA, TokenType.XI)
                or self._match(TokenType.IDENTIFIER)
                or self._is_keyword_usable_as_identifier()
            ):
                result = self._parse_declaration_or_inclusion()
                if isinstance(result, list):
                    declarations.extend(result)
                else:
                    declarations.append(result)

                if self._match(TokenType.SEMICOLON):
                    self._advance()  # Consume ';'
                    self._skip_newlines()
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
