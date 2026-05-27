"""Parser rules for relational-algebra constructs.

Covers: ``_parse_restrict`` (sigma), ``_parse_project`` (pi),
``_parse_relation_rename`` (R[B/A]), the GROUP family
(``_parse_group_rhs``, ``_parse_group_regroup_rhs``,
``_parse_group_aggregate_rhs``, ``_parse_aggregator_clause``,
``_parse_ungroup_rhs``), and the ``_is_attr_name_token`` helper
consumed by ``_parse_relation_rename``.

This mixin is composed into :class:`Parser` via multiple inheritance.
Method bodies are byte-identical to their counterparts in the
pre-refactor monolithic ``parser.py``; only their file location has
changed.
"""

from __future__ import annotations

from txt2tex.ast_nodes import (
    AggregatorClause,
    Expr,
    Group,
    GroupAggregate,
    Project,
    RelationRename,
    Restrict,
    Ungroup,
)
from txt2tex.parser_pkg._base import ParserBase, ParserError
from txt2tex.tokens import Token, TokenType


class _AlgebraParser(ParserBase):  # pyright: ignore[reportUnusedClass]
    """Mixin: rules for relational-algebra constructs."""

    def _parse_group_rhs(
        self, relation: Expr, group_tok: Token
    ) -> Group | GroupAggregate:
        """Parse the RHS of a GROUP expression.

        Dispatches on the first token after '(':
        - LBRACE → regroup form: ({A, B, ...} as alias)
        - aggregator keyword → aggregate form: (Count(x) as t, Sum(y) as g)

        Mixing the two forms in one GROUP RHS is rejected with a clear message.
        """
        if not self._match(TokenType.LPAREN):
            raise ParserError("Expected '(' after 'group'", self._current())
        self._advance()  # consume '('

        if self._match(TokenType.LBRACE):
            return self._parse_group_regroup_rhs(relation, group_tok)
        if self._current().type in self._AGGREGATOR_TOKEN_TYPES:
            return self._parse_group_aggregate_rhs(relation, group_tok)
        cur = self._current()
        raise ParserError(
            f"Expected '{{' (regroup form) or an aggregator keyword "
            f"(Count, Sum, Avg, Min, Max, Median) after '(' in 'group', "
            f"got {cur.type.name} ({cur.value!r})",
            cur,
        )

    def _parse_group_regroup_rhs(self, relation: Expr, group_tok: Token) -> Group:
        """Parse the regroup form: {A, B, ...} as alias ).

        The opening '(' has already been consumed by _parse_group_rhs.
        """
        self._advance()  # consume '{'
        attrs: list[str] = []
        if not self._is_attr_name_token():
            raise ParserError(
                "Expected at least one attribute name in 'group' attribute list",
                self._current(),
            )
        attrs.append(self._advance().value)
        while self._match(TokenType.COMMA):
            self._advance()  # consume ','
            if not self._is_attr_name_token():
                raise ParserError(
                    "Expected attribute name after ',' in 'group' attribute list",
                    self._current(),
                )
            attrs.append(self._advance().value)
        if not self._match(TokenType.RBRACE):
            raise ParserError(
                "Expected '}' after attribute list in 'group'", self._current()
            )
        self._advance()  # consume '}'
        if not self._match(TokenType.AS):
            cur = self._current()
            raise ParserError(
                f"Expected 'as' after attribute list in 'group', "
                f"got {cur.type.name} ({cur.value!r})",
                cur,
            )
        self._advance()  # consume 'as'
        if not self._is_attr_name_token():
            raise ParserError(
                "Expected alias name after 'as' in 'group'", self._current()
            )
        alias = self._advance().value
        if not self._match(TokenType.RPAREN):
            raise ParserError(
                "Expected ')' to close 'group' expression", self._current()
            )
        self._advance()  # consume ')'
        return Group(
            relation=relation,
            attrs=attrs,
            alias=alias,
            line=group_tok.line,
            column=group_tok.column,
        )

    def _parse_group_aggregate_rhs(
        self, relation: Expr, group_tok: Token
    ) -> GroupAggregate:
        """Parse the aggregate form: Count(x) as t, Sum(y) as g ).

        The opening '(' has already been consumed by _parse_group_rhs.
        Parses one or more comma-separated AggregatorClause entries,
        then expects ')' to close the GROUP RHS.
        """
        clauses: list[AggregatorClause] = []
        clauses.append(self._parse_aggregator_clause())
        while self._match(TokenType.COMMA):
            self._advance()  # consume ','
            # Guard: if the next token is a '{', reject the mix
            if self._match(TokenType.LBRACE):
                raise ParserError(
                    "cannot mix regroup and aggregator forms in the same 'group' RHS",
                    self._current(),
                )
            clauses.append(self._parse_aggregator_clause())
        if not self._match(TokenType.RPAREN):
            raise ParserError(
                "Expected ')' to close 'group' expression", self._current()
            )
        self._advance()  # consume ')'
        return GroupAggregate(
            relation=relation,
            clauses=clauses,
            line=group_tok.line,
            column=group_tok.column,
        )

    def _parse_aggregator_clause(self) -> AggregatorClause:
        """Parse a single ``Count(attr) as alias`` clause."""
        agg_tok = self._current()
        if agg_tok.type not in self._AGGREGATOR_TOKEN_TYPES:
            raise ParserError(
                f"Expected aggregator keyword (Count, Sum, Avg, Min, Max, Median), "
                f"got {agg_tok.type.name} ({agg_tok.value!r})",
                agg_tok,
            )
        agg = self._TOKEN_TO_AGGREGATOR[agg_tok.type]
        self._advance()  # consume aggregator keyword
        if not self._match(TokenType.LPAREN):
            raise ParserError(
                f"Expected '(' after '{agg_tok.value}' in aggregator clause",
                self._current(),
            )
        self._advance()  # consume '('
        if not self._is_attr_name_token():
            raise ParserError(
                f"Expected attribute name inside '{agg_tok.value}(...)'",
                self._current(),
            )
        attr = self._advance().value
        if not self._match(TokenType.RPAREN):
            raise ParserError(
                f"Expected ')' after attribute in '{agg_tok.value}({attr})'",
                self._current(),
            )
        self._advance()  # consume ')'
        if not self._match(TokenType.AS):
            cur = self._current()
            raise ParserError(
                f"Expected 'as' after '{agg_tok.value}({attr})', "
                f"got {cur.type.name} ({cur.value!r})",
                cur,
            )
        self._advance()  # consume 'as'
        if not self._is_attr_name_token():
            raise ParserError(
                f"Expected alias name after 'as' in '{agg_tok.value}({attr}) as ...'",
                self._current(),
            )
        alias = self._advance().value
        return AggregatorClause(
            agg=agg,
            attr=attr,
            alias=alias,
            line=agg_tok.line,
            column=agg_tok.column,
        )

    def _parse_ungroup_rhs(self, relation: Expr, ungroup_tok: Token) -> Ungroup:
        """Parse the RHS of an UNGROUP expression: alias.

        Called after the 'ungroup' keyword has been consumed.  Expects a
        single identifier naming the nested-relation attribute to flatten.
        """
        if not self._is_attr_name_token():
            raise ParserError("Expected alias name after 'ungroup'", self._current())
        alias = self._advance().value
        return Ungroup(
            relation=relation,
            alias=alias,
            line=ungroup_tok.line,
            column=ungroup_tok.column,
        )

    def _parse_restrict(self) -> Restrict:
        """Parse sigma[predicate](relation) or sigma[predicate]relation."""
        op_tok = self._advance()  # consume 'sigma'
        if not self._match(TokenType.LBRACKET):
            raise ParserError("Expected '[' after sigma", self._current())
        bracket_tok = self._advance()  # consume '['
        if self._match(TokenType.RBRACKET):
            raise ParserError(
                "Expected predicate expression in sigma[...]", self._current()
            )
        try:
            predicate = self._parse_expr()
        except ParserError as inner:
            if "⟩" in inner.message or "sequence literal" in inner.message:
                raise ParserError(
                    "Unspaced '<' inside sigma[...] is parsed as an angle "
                    "bracket — add spaces around the operator "
                    "(e.g. sigma[x < 1] not sigma[x<1])",
                    bracket_tok,
                ) from None
            raise
        if not self._match(TokenType.RBRACKET):
            if self._match(TokenType.RANGLE):
                raise ParserError(
                    "Unspaced '>' inside sigma[...] is parsed as an angle "
                    "bracket — add spaces around the operator "
                    "(e.g. sigma[x > 1] not sigma[x>1])",
                    bracket_tok,
                )
            raise ParserError("Expected ']' after sigma predicate", bracket_tok)
        self._advance()  # consume ']'
        prev_relational = self._in_relational_context
        self._in_relational_context = True
        try:
            if self._match(TokenType.LPAREN):
                self._advance()  # consume '('
                relation = self._parse_expr()
                if not self._match(TokenType.RPAREN):
                    raise ParserError(
                        "Expected ')' after sigma relation argument", self._current()
                    )
                self._advance()  # consume ')'
            else:
                relation = self._parse_postfix(allow_space_separated=False)
        finally:
            self._in_relational_context = prev_relational
        return Restrict(
            predicate=predicate,
            relation=relation,
            line=op_tok.line,
            column=op_tok.column,
        )

    def _parse_project(self) -> Project:
        """Parse pi[A, B, ...](relation) or pi[A, B, ...]relation."""
        op_tok = self._advance()  # consume 'pi'
        if not self._match(TokenType.LBRACKET):
            raise ParserError("Expected '[' after pi", self._current())
        bracket_tok = self._advance()  # consume '['
        if self._match(TokenType.RBRACKET):
            raise ParserError("Expected attribute list in pi[...]", self._current())
        # Parse comma-separated attribute names (identifiers or keyword-identifiers)
        attrs: list[str] = []
        if not self._is_attr_name_token():
            raise ParserError("Expected attribute name in pi[...]", self._current())
        attrs.append(self._advance().value)
        while self._match(TokenType.COMMA):
            self._advance()  # consume ','
            if not self._is_attr_name_token():
                raise ParserError(
                    "Expected attribute name after ',' in pi[...]", self._current()
                )
            attrs.append(self._advance().value)
        if not self._match(TokenType.RBRACKET):
            raise ParserError("Expected ']' after pi attribute list", bracket_tok)
        self._advance()  # consume ']'
        prev_relational = self._in_relational_context
        self._in_relational_context = True
        try:
            if self._match(TokenType.LPAREN):
                self._advance()  # consume '('
                relation = self._parse_expr()
                if not self._match(TokenType.RPAREN):
                    raise ParserError(
                        "Expected ')' after pi relation argument", self._current()
                    )
                self._advance()  # consume ')'
            else:
                relation = self._parse_postfix(allow_space_separated=False)
        finally:
            self._in_relational_context = prev_relational
        return Project(
            attrs=attrs,
            relation=relation,
            line=op_tok.line,
            column=op_tok.column,
        )

    def _parse_relation_rename(self, base: Expr) -> RelationRename:
        """Parse R[new/old, ...] postfix in a relational context.

        Called from ``_parse_postfix`` when ``_in_relational_context`` is True
        and the bracket contents contain a ``/`` separator.  The ``[`` has NOT
        been consumed on entry; this method consumes it and the matching ``]``.

        Grammar:
            relation_rename ::= '[' pair (',' pair)* ']'
            pair            ::= name '/' name
            name            ::= IDENTIFIER | keyword-usable-as-identifier

        Per Z RM §3.11 the new name appears first (``new``), the old name
        second (``old``).  Pair direction: ``(new_name, old_name)``.

        Attribute names admit keywords as identifiers (``id``, ``dom``, ``ran``,
        etc.) because relation attribute names can coincide with operator keywords.
        """
        open_tok = self._advance()  # Consume '['

        pairs: list[tuple[str, str]] = []

        while not self._match(TokenType.RBRACKET):
            if self._at_end() or self._match(TokenType.NEWLINE, TokenType.EOF):
                raise ParserError(
                    "unclosed '[' in relation rename",
                    open_tok,
                )

            # Expect new (target) name (identifier or keyword-as-identifier)
            if not self._is_attr_name_token():
                cur = self._current()
                raise ParserError(
                    f"expected identifier before '/' in relation rename pair,"
                    f" got {cur.type.name} ({cur.value!r})",
                    cur,
                )
            new_name = self._advance().value

            # Expect '/'
            if not self._match(TokenType.SLASH):
                cur = self._current()
                raise ParserError(
                    f"expected '/' in relation rename pair after {new_name!r},"
                    f" got {cur.type.name} ({cur.value!r})",
                    cur,
                )
            self._advance()  # Consume '/'

            # Expect old (source) name (identifier or keyword-as-identifier)
            if not self._is_attr_name_token():
                cur = self._current()
                raise ParserError(
                    f"expected identifier after '/' in relation rename pair,"
                    f" got {cur.type.name} ({cur.value!r})",
                    cur,
                )
            old_name = self._advance().value

            pairs.append((new_name, old_name))

            # Optional comma separator
            if self._match(TokenType.COMMA):
                self._advance()  # Consume ','
                if self._match(TokenType.RBRACKET):
                    raise ParserError(
                        "expected rename pair after ',' in relation rename",
                        self._current(),
                    )
                continue

            if not self._match(TokenType.RBRACKET):
                cur = self._current()
                raise ParserError(
                    f"expected ',' or ']' in relation rename,"
                    f" got {cur.type.name} ({cur.value!r})",
                    cur,
                )

        if not pairs:
            raise ParserError(
                "relation rename requires at least one pair",
                open_tok,
            )

        self._advance()  # Consume ']'

        return RelationRename(
            relation=base,
            pairs=pairs,
            line=open_tok.line,
            column=open_tok.column,
        )

    def _is_attr_name_token(self) -> bool:
        """Return True if the current token is usable as an attribute name.

        Attribute names in pi[...] contexts are plain names.
        They admit keywords-as-identifiers (id, dom, ran, etc.) because Z
        field names can coincide with operator keywords.
        """
        return (
            self._match(TokenType.IDENTIFIER) or self._is_keyword_usable_as_identifier()
        )
