"""Parser rules for Z paragraph constructs.

Covers: GivenType, FreeType (and FreeBranch), SyntaxBlock,
Abbreviation, AxDef, GenDef, Zed.  Includes the small helper
``_parse_compound_identifier_name`` that is consumed only by
``_parse_abbreviation``.

This mixin is composed into :class:`Parser` via multiple inheritance.
Method bodies are byte-identical to their counterparts in the
pre-refactor monolithic ``parser.py``; only their file location has
changed.
"""

from __future__ import annotations

from txt2tex.ast_nodes import (
    Abbreviation,
    AxDef,
    Declaration,
    Document,
    DocumentItem,
    Expr,
    FreeBranch,
    FreeType,
    GenDef,
    GivenType,
    SchemaInclusion,
    SequenceLiteral,
    SyntaxBlock,
    SyntaxDefinition,
    Zed,
)
from txt2tex.parser_pkg._base import ParserBase, ParserError
from txt2tex.tokens import Token, TokenType


class _ParagraphsParser(ParserBase):  # pyright: ignore[reportUnusedClass]
    """Mixin: rules for Z paragraph constructs."""

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

        # Parse expression in relational context: a top-level abbreviation RHS
        # is an expression, not a Z paragraph body, so a postfix `R[a/b]` is a
        # relational rename (RelationRename → inline math) rather than a
        # schema rename (SchemaRename, which fuzz rejects when emitted with a
        # `/` inside a Z paragraph).
        prev_relational = self._in_relational_context
        self._in_relational_context = True
        try:
            expr = self._parse_expr()
        finally:
            self._in_relational_context = prev_relational

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
        Comma-separated variable lists share a type: var1, var2 : Type.
        Schema inclusions (bare, Delta, Xi) are also permitted.
        """
        start_token = self._advance()  # Consume 'axdef'
        self._skip_newlines()

        # Check for generic parameters after 'axdef'
        generic_params = self._parse_generic_params()
        self._skip_newlines()

        declarations: list[Declaration | SchemaInclusion] = []

        # Parse declarations until 'where' or 'end'
        while not self._at_end() and not self._match(TokenType.WHERE, TokenType.END):
            if self._match(TokenType.NEWLINE):
                self._advance()
                continue

            # pk is only valid in schema bodies — reject it here with a clear message.
            if self._match(TokenType.PK):
                raise ParserError(
                    "Primary-key annotation is only valid in schema bodies,"
                    " not inside axdef",
                    self._current(),
                )

            # Three forms: Delta/Xi inclusion, bare inclusion, typed decl.
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

                # Semicolons are only valid after typed declarations.
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

        declarations: list[Declaration | SchemaInclusion] = []

        # Parse declarations until 'where' or 'end'
        while not self._at_end() and not self._match(TokenType.WHERE, TokenType.END):
            if self._match(TokenType.NEWLINE):
                self._advance()
                continue

            # pk is only valid in schema bodies — reject it here with a clear message.
            if self._match(TokenType.PK):
                raise ParserError(
                    "Primary-key annotation is only valid in schema bodies,"
                    " not inside gendef",
                    self._current(),
                )

            # Three forms: Delta/Xi inclusion, bare inclusion, typed declaration.
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
            continue

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
