"""Parser rules for general expression grammar (recursive descent).

Covers the full Pratt-style expression grammar from ``_parse_expr``
down to ``_parse_atom``: conditionals, iff/implies, or/and, unary,
arithmetic, range, comparison, relation/set ops, union, cross,
intersect, postfix, plus quantifier/lambda/binding/set-comprehension
parsers and atom literals (sequence, bag).

This mixin is composed into :class:`Parser` via multiple inheritance.
Method bodies are byte-identical to their counterparts in the
pre-refactor monolithic ``parser.py``; only their file location has
changed.
"""

from __future__ import annotations

import dataclasses
from typing import ClassVar, Literal

from txt2tex.ast_nodes import (
    Aggregator,
    BagLiteral,
    BinaryOp,
    Binding,
    Conditional,
    Divide,
    Expr,
    ExtendAggregate,
    FunctionApp,
    GenericInstantiation,
    Group,
    GroupAggregate,
    GuardedBranch,
    GuardedCases,
    Identifier,
    Lambda,
    NaturalJoin,
    Number,
    Quantifier,
    Range,
    RelationalImage,
    SchemaBinding,
    SequenceLiteral,
    SetComprehension,
    SetLiteral,
    StringLit,
    Subscript,
    Superscript,
    Theta,
    Tuple,
    TupleProjection,
    UnaryOp,
    Ungroup,
)
from txt2tex.constants import PROSE_WORDS
from txt2tex.parser_pkg._base import ParserBase, ParserError
from txt2tex.tokens import Token, TokenType


class _ExpressionsParser(ParserBase):  # pyright: ignore[reportUnusedClass]
    """Mixin: full expression-grammar parser."""

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
            TokenType.BAG_DIFF,
        ):
            # Lookahead for +: only treat as infix if followed by operand
            # CAT, FILTER, BAG_UNION, BAG_DIFF, and MINUS are always infix
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
            TokenType.SIGMA,  # sigma[...](...)
            TokenType.PI,  # pi[...](...)
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
            TokenType.BAG_DIFF,  # bag_diff bag difference
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
            TokenType.JOIN,  # join (natural join / theta-join)
            TokenType.DIV,  # div (relational division)
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
            TokenType.SIGMA,
            TokenType.PI,
        )

    def _parse_quantifier(self) -> Expr:
        """Parse quantifier: (forall|exists|exists1|mu) var [, var]* : domain | body.

        Supports:
            - Multiple variables with shared domain: forall x, y : N | pred
            - Tuple patterns for destructuring: forall (x, y) : T | pred
            - Semicolon-separated bindings (nested): forall x : T; y : U | pred
            - Mu-operator with expression: mu x : N | pred . expr
            - Schema-text quantification (Z RM §3.10):
                exists Delta S | P
                exists Xi S | P
                exists S | P
                exists S' | P
                forall Delta S | P

        Disambiguation rule (Z RM §3.10):
            If `:` follows the identifier  → value-binding (existing path).
            If `Delta`/`Xi` precedes the identifier, or
            if the identifier is followed directly by `|` or NEWLINE→`|`
                → schema-binding (new path).

        Examples:
            forall x : N | pred
            forall x, y : N | pred
            forall (x, y) : T | pred
            exists1 x : N | pred
            mu x : N | pred . expr
            exists Delta S | P
            exists Xi S | P
            exists S | P
            exists S' | P
        """
        quant_token = self._advance()  # Consume 'forall', 'exists', 'exists1', or 'mu'

        # --- Schema-text quantification (Z RM §3.10) ---
        #
        # Check for Delta/Xi decoration before identifier.
        if self._match(TokenType.DELTA, TokenType.XI):
            decoration: Literal["Delta", "Xi", "None", "Prime"] = (
                "Delta" if self._match(TokenType.DELTA) else "Xi"
            )
            self._advance()  # Consume Delta or Xi
            if not self._match(TokenType.IDENTIFIER):
                raise ParserError(
                    f"Expected schema name after {decoration}",
                    self._current(),
                )
            schema_token = self._advance()
            schema_binding = SchemaBinding(
                decoration=decoration,
                schema_name=schema_token.value,
                line=schema_token.line,
                column=schema_token.column,
            )
            return self._parse_schema_quantifier_body(quant_token, schema_binding)

        # Check for bare IDENTIFIER followed by | (schema-as-declaration or primed).
        #
        # Disambiguation (Z naming convention, Z RM §3.2):
        #   - Schema names begin with an uppercase letter.
        #   - Variable names begin with a lowercase letter.
        #   - Presence of `:` after the identifier → value binding regardless.
        #   - Uppercase initial + no `:` or `,` follows → schema binding.
        #
        # Examples:
        #   exists S | P        → schema binding  (S is uppercase)
        #   exists S' | P       → schema binding  (S' is uppercase-initial)
        #   exists x | P        → value binding   (x is lowercase, no domain)
        #   exists x : T | P    → value binding   (: follows)
        if self._match(TokenType.IDENTIFIER):
            ident_token = self._peek_ahead(0)  # peek at current without consuming
            next_tok = self._peek_ahead(1)
            schema_name = ident_token.value
            # Strip trailing prime for the uppercase check
            base_name = schema_name.rstrip("'")
            is_schema_name = bool(base_name) and base_name[0].isupper()
            not_decl = next_tok.type not in (TokenType.COLON, TokenType.COMMA)
            if is_schema_name and not_decl:
                # Schema binding: bare S | P or S' | P
                self._advance()  # consume the identifier
                deco: Literal["Delta", "Xi", "None", "Prime"] = (
                    "Prime" if schema_name.endswith("'") else "None"
                )
                schema_binding = SchemaBinding(
                    decoration=deco,
                    schema_name=schema_name,
                    line=ident_token.line,
                    column=ident_token.column,
                )
                return self._parse_schema_quantifier_body(quant_token, schema_binding)
            # Fall through to value-binding path (: follows, or lowercase name)

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
                quant_token.value,
                nested_line,
                nested_column,
                inherited_vars=set(variables),
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
        # Also record all declared variables so _parse_postfix can distinguish
        # bullet `.` from field projection (Z RM §3.16: declared variables are
        # not field selectors of sibling bindings in the same schema-text).
        prev_quantifier_vars = self._current_quantifier_vars
        self._current_quantifier_vars = set(variables)
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
            self._current_quantifier_vars = prev_quantifier_vars

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

    def _parse_schema_quantifier_body(
        self,
        quant_token: Token,
        schema_binding: SchemaBinding,
    ) -> Quantifier:
        """Parse the ``| body`` tail of a schema-text quantifier (Z RM §3.10).

        Called after the schema binding (Delta S / Xi S / S / S') has been
        consumed.  Expects ``|`` followed by the predicate body.

        The body is the predicate after the spot character; fuzz expands the
        schema invariant, so the engine emits the binding literally.
        """
        # Expect | separator
        if not self._match(TokenType.PIPE):
            raise ParserError(
                "Expected '|' after schema binding in quantifier",
                self._current(),
            )
        self._advance()  # Consume |

        # Detect line continuation after |
        has_continuation = False
        if self._match(TokenType.CONTINUATION):
            self._advance()
            has_continuation = True
            if self._match(TokenType.NEWLINE):
                self._advance()
            self._skip_newlines()
        elif self._match(TokenType.NEWLINE):
            has_continuation = True
            self._skip_newlines()
        else:
            self._skip_newlines()

        self._in_comprehension_body = True
        try:
            body = self._parse_expr()
        finally:
            self._in_comprehension_body = False

        return Quantifier(
            quantifier=quant_token.value,
            variables=[],
            domain=None,
            body=body,
            expression=None,
            line_break_after_pipe=has_continuation,
            line_break_after_bullet=False,
            tuple_pattern=None,
            schema_binding=schema_binding,
            line=quant_token.line,
            column=quant_token.column,
        )

    def _parse_quantifier_continuation(
        self,
        quantifier: str,
        line: int,
        column: int,
        inherited_vars: set[str] | None = None,
    ) -> Expr:
        """Parse continuation of semicolon-separated quantifier bindings.

        Helper for parsing y : U | body or y : U; z : V | body
        after we've already parsed x : T;

        inherited_vars accumulates all variables declared in earlier bindings of
        the same schema-text chain so that _parse_postfix can see the full set
        when disambiguating bullet `.` from field projection (Z RM §3.16).
        """
        prior_vars: set[str] = inherited_vars if inherited_vars is not None else set()

        # After ';' the caller may have placed a natural newline or an explicit
        # `\` continuation before the next binding.  Mirror the post-`|` handling
        # (lines 2810-2820) so that `;`-chained quantifier prefixes may span
        # source lines (Z RM authoring convenience).
        if self._match(TokenType.CONTINUATION):
            self._advance()
            if self._match(TokenType.NEWLINE):
                self._advance()
            self._skip_newlines()
        elif self._match(TokenType.NEWLINE):
            self._skip_newlines()

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
            # Parse type expression to match main quantifier parser.
            # Mirror _parse_quantifier (parser.py:2305-2309): set the flag so
            # compound domain types like X -> Y stop at PIPE/PERIOD correctly.
            self._parsing_schema_text = True
            try:
                domain = self._parse_function_type()
            finally:
                self._parsing_schema_text = False

        # Check for another semicolon (more bindings)
        if self._match(TokenType.SEMICOLON):
            self._advance()  # Consume ';'
            nested_quant = self._parse_quantifier_continuation(
                quantifier,
                self._current().line,
                self._current().column,
                inherited_vars=prior_vars | set(variables),
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

        # Detect line continuation (backslash or natural newline).
        # Mirrors the logic in _parse_quantifier so that semicolon-chained
        # quantifier bindings (forall x : T; y : U; z : V | body) honour an
        # explicit `\` continuation and bare WYSIWYG newlines after `|`.
        has_continuation = False
        if self._match(TokenType.CONTINUATION):
            self._advance()  # consume \
            has_continuation = True
            if self._match(TokenType.NEWLINE):
                self._advance()
            self._skip_newlines()
        elif self._match(TokenType.NEWLINE):
            has_continuation = True
            self._skip_newlines()
        else:
            self._skip_newlines()

        # Set flag: we're in quantifier body where . can be separator (for mu)
        # Expose the full declared-variable set (this level + all inherited levels)
        # so _parse_postfix can apply the Z RM §3.16 bullet disambiguation rule.
        prev_quantifier_vars = self._current_quantifier_vars
        self._current_quantifier_vars = prior_vars | set(variables)
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
            self._current_quantifier_vars = prev_quantifier_vars

        return Quantifier(
            quantifier=quantifier,
            variables=variables,
            domain=domain,
            body=body,
            expression=expression,
            line_break_after_pipe=has_continuation,
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

        # Multi-decl form: lambda s : Ship; c : Class | P . E
        # Delegate to _parse_quantifier_continuation (same path as forall/exists/mu),
        # which handles PIPE + optional bullet, producing nested Quantifier nodes.
        if self._match(TokenType.SEMICOLON):
            self._advance()  # Consume ';'
            nested_quant = self._parse_quantifier_continuation(
                "lambda",
                self._current().line,
                self._current().column,
                inherited_vars=set(variables),
            )
            return Quantifier(
                quantifier="lambda",
                variables=variables,
                domain=domain,
                body=nested_quant,
                expression=None,
                tuple_pattern=None,
                line=lambda_token.line,
                column=lambda_token.column,
            )

        # Single-decl form with predicate pipe: lambda s : Ship | P . E
        # Produces Quantifier(quantifier="lambda") consistent with multi-decl path.
        if self._match(TokenType.PIPE):
            self._advance()  # Consume '|'
            self._skip_newlines()
            prev_quantifier_vars = self._current_quantifier_vars
            self._current_quantifier_vars = set(variables)
            self._in_comprehension_body = True
            try:
                body = self._parse_iff()
                expression: Expr | None = None
                if self._match(TokenType.PERIOD):
                    self._advance()  # Consume '.'
                    self._in_comprehension_body = False
                    expression = self._parse_iff()
            finally:
                self._in_comprehension_body = False
                self._current_quantifier_vars = prev_quantifier_vars
            return Quantifier(
                quantifier="lambda",
                variables=variables,
                domain=domain,
                body=body,
                expression=expression,
                tuple_pattern=None,
                line=lambda_token.line,
                column=lambda_token.column,
            )

        # Original PERIOD-only path: lambda x : T . body  (no pipe, no semicolon)
        # Produces a Lambda node — single-decl abstraction.
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

    def _parse_binding(self) -> Binding:
        r"""Parse a Z binding literal: {| name == expr, ... |} (Z RM §3.7).

        Consumes LBIND, then a comma-separated list of ``IDENTIFIER == expr``
        pairs, then RBIND.  Empty bindings ``{| |}`` are accepted (Z RM §3.7
        permits them).

        The ``==`` inside binding context reuses the ABBREV token; the parser
        disambiguates by position — we are inside ``{| ... |}``, not at
        top-level abbreviation position.

        Raises:
            ParserError: Missing ``==``, missing label, missing value, missing
                closing ``|}``, or semicolon used between components.
        """
        start_token = self._current()
        self._advance()  # consume {|

        pairs: list[tuple[str, Expr]] = []

        # Empty binding: {| |}
        if self._match(TokenType.RBIND):
            self._advance()  # consume |}
            return Binding(pairs=[], line=start_token.line, column=start_token.column)

        # Parse first component
        pairs.append(self._parse_binding_component())

        # Parse remaining components
        while self._match(TokenType.COMMA):
            self._advance()  # consume ,
            # Skip any newlines between components
            self._skip_newlines()
            pairs.append(self._parse_binding_component())

        # Closing |}
        if not self._match(TokenType.RBIND):
            cur = self._current()
            if cur.type == TokenType.SEMICOLON:
                raise ParserError(
                    "binding components are comma-separated, not semicolons;"
                    " use ',' between components",
                    cur,
                )
            if cur.type == TokenType.EOF:
                raise ParserError(
                    "unclosed binding: expected '|}' to close '{|'",
                    cur,
                )
            raise ParserError(
                f"expected ',' or '|}}' in binding, got {cur.type.name}",
                cur,
            )
        self._advance()  # consume |}

        return Binding(pairs=pairs, line=start_token.line, column=start_token.column)

    def _parse_binding_component(self) -> tuple[str, Expr]:
        """Parse a single binding component: IDENTIFIER == expr.

        Raises:
            ParserError: If label is missing, ``==`` is missing, or value is
                missing.
        """
        # Expect an identifier as the label
        if not self._match(TokenType.IDENTIFIER):
            cur = self._current()
            if cur.type == TokenType.ABBREV:
                raise ParserError(
                    "binding component requires a label before '==';"
                    " got '==' with no label",
                    cur,
                )
            if cur.type in (TokenType.RBIND, TokenType.EOF):
                raise ParserError(
                    "expected binding label (identifier) before '=='",
                    cur,
                )
            raise ParserError(
                f"expected identifier as binding label, got {cur.type.name}",
                cur,
            )
        label_token = self._advance()  # consume identifier

        # Expect ==
        if not self._match(TokenType.ABBREV):
            cur = self._current()
            raise ParserError(
                f"expected '==' after binding label {label_token.value!r},"
                f" got {cur.type.name}",
                cur,
            )
        self._advance()  # consume ==

        # Parse value expression — stop before , or |}
        # Use _parse_expr to allow full expressions as values
        if self._match(TokenType.COMMA, TokenType.RBIND, TokenType.EOF):
            cur = self._current()
            raise ParserError(
                f"expected expression after '==' in binding component"
                f" {label_token.value!r}",
                cur,
            )
        value = self._parse_expr()

        return (label_token.value, value)

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

        # Parse optional extra declarations: ; var : Type ; var : Type ...
        # Handles multi-typed set comprehensions like { s : Ship; c : Class | ... }
        extra_declarations: list[tuple[str, Expr]] | None = None
        while self._match(TokenType.SEMICOLON):
            self._advance()  # Consume ';'
            # After ';' the caller may have placed a natural newline or an explicit
            # `\` continuation before the next binding.  Mirror the post-`|` handling
            # so that `;`-chained set-comprehension prefixes may span source lines.
            if self._match(TokenType.CONTINUATION):
                self._advance()
                if self._match(TokenType.NEWLINE):
                    self._advance()
                self._skip_newlines()
            elif self._match(TokenType.NEWLINE):
                self._skip_newlines()
            if not self._match(TokenType.IDENTIFIER):
                raise ParserError(
                    "Expected variable name after ';' in set comprehension",
                    self._current(),
                )
            extra_var = self._advance().value
            extra_domain: Expr | None = None
            if self._match(TokenType.COLON):
                self._advance()  # Consume ':'
                self._parsing_schema_text = True
                try:
                    extra_domain = self._parse_function_type()
                finally:
                    self._parsing_schema_text = False
            if extra_domain is None:
                raise ParserError(
                    f"Expected ':' and type after '{extra_var}' in set comprehension",
                    self._current(),
                )
            if extra_declarations is None:
                extra_declarations = []
            extra_declarations.append((extra_var, extra_domain))

        # Parse separator | or . for set comprehension
        # Syntax: {x : T | predicate . expr} or {x : T . expr} (no predicate)
        predicate: Expr | None
        expression: Expr | None
        pipe_continuation = False
        bullet_continuation = False

        if self._match(TokenType.PERIOD):
            # Period separator: no predicate, directly to expression
            self._advance()  # Consume '.'
            if self._match(TokenType.CONTINUATION):
                self._advance()
                bullet_continuation = True
                if self._match(TokenType.NEWLINE):
                    self._advance()
                self._skip_newlines()
            elif self._match(TokenType.NEWLINE):
                bullet_continuation = True
                self._skip_newlines()
            predicate = None
            expression = self._parse_set_expression()
        elif self._match(TokenType.PIPE):
            # Pipe separator: parse predicate, optionally followed by . expr
            self._advance()  # Consume '|'
            # Detect line continuation after | (backslash or bare newline).
            pipe_continuation = False
            if self._match(TokenType.CONTINUATION):
                self._advance()
                pipe_continuation = True
                if self._match(TokenType.NEWLINE):
                    self._advance()
                self._skip_newlines()
            elif self._match(TokenType.NEWLINE):
                pipe_continuation = True
                self._skip_newlines()
            # Set flag: we're in comprehension body where . can be separator.
            # Expose all declared variables (primary + extra) for bullet
            # disambiguation in _parse_postfix (Z RM §3.16).
            all_comp_vars: set[str] = set(variables)
            if extra_declarations is not None:
                for ev, _ in extra_declarations:
                    all_comp_vars.add(ev)
            prev_quantifier_vars = self._current_quantifier_vars
            self._current_quantifier_vars = all_comp_vars
            self._in_comprehension_body = True
            try:
                predicate = self._parse_set_predicate()

                # Parse optional expression part (. expression)
                expression = None
                bullet_continuation = False
                if self._match(TokenType.PERIOD):
                    self._advance()  # Consume '.'
                    # Detect line continuation after bullet.
                    if self._match(TokenType.CONTINUATION):
                        self._advance()
                        bullet_continuation = True
                        if self._match(TokenType.NEWLINE):
                            self._advance()
                        self._skip_newlines()
                    elif self._match(TokenType.NEWLINE):
                        bullet_continuation = True
                        self._skip_newlines()
                    expression = self._parse_set_expression()
            finally:
                self._in_comprehension_body = False
                self._current_quantifier_vars = prev_quantifier_vars
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

        # Expect closing brace (skip newlines for multi-line comprehensions)
        self._skip_newlines()
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
            extra_declarations=extra_declarations,
            line_break_after_pipe=pipe_continuation,
            line_break_after_bullet=bullet_continuation,
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
        """Parse expression in set comprehension (after . and up to }).

        Newlines between the bullet separator and the expression are skipped
        to support multi-line comprehensions like:
            { s : Ship | pred .
              {| name == s.name |}
            }
        """
        # Skip newlines before expression (multi-line comprehension support)
        self._skip_newlines()
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

            prev_in_comparison_rhs = self._in_comparison_rhs
            self._in_comparison_rhs = True
            try:
                right = self._parse_function_type()
            finally:
                self._in_comparison_rhs = prev_in_comparison_rhs

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

        Supports multi-line expressions with natural line breaks.
        """
        left = self._parse_cross()

        while self._match(TokenType.UNION, TokenType.OVERRIDE):
            op_token = self._advance()
            # Detect line continuation (backslash or natural newline)
            has_continuation = False
            if self._match(TokenType.CONTINUATION):
                self._advance()  # consume \
                has_continuation = True
                if self._match(TokenType.NEWLINE):
                    self._advance()
                self._skip_newlines()
            elif self._match(TokenType.NEWLINE):
                has_continuation = True
                self._skip_newlines()
            else:
                self._skip_newlines()
            right = self._parse_cross()
            left = BinaryOp(
                operator=op_token.value,
                left=left,
                right=right,
                line_break_after=has_continuation,
                line=op_token.line,
                column=op_token.column,
            )

        return left

    def _parse_cross(self) -> Expr:
        """Parse Cartesian product, natural join, theta-join, division, GROUP, UNGROUP.

        CROSS, JOIN, DIV, GROUP, and UNGROUP sit at the same precedence
        level between set operators and arithmetic (Phase 2.2 / 4.1).
        JOIN handles an optional subscript bracket: R join [p] S.
        GROUP and UNGROUP are Date's nested-relation operators.

        Supports multi-line expressions with natural line breaks.
        """
        left = self._parse_intersect()

        while self._match(
            TokenType.CROSS,
            TokenType.JOIN,
            TokenType.DIV,
            TokenType.GROUP,
            TokenType.UNGROUP,
            TokenType.EXTEND,
        ):
            op_token = self._advance()

            if op_token.type == TokenType.JOIN:
                # Check for theta-join subscript: join [predicate]
                subscript: Expr | None = None
                if self._match(TokenType.LBRACKET):
                    bracket_tok = self._advance()  # consume '['
                    if self._match(TokenType.RBRACKET):
                        raise ParserError(
                            "Expected predicate in join subscript", self._current()
                        )
                    subscript = self._parse_expr()
                    if not self._match(TokenType.RBRACKET):
                        raise ParserError(
                            "Expected ']' after join predicate", bracket_tok
                        )
                    self._advance()  # consume ']'
                # Detect line continuation after optional subscript
                has_continuation = False
                if self._match(TokenType.CONTINUATION):
                    self._advance()  # consume \
                    has_continuation = True
                    if self._match(TokenType.NEWLINE):
                        self._advance()
                    self._skip_newlines()
                elif self._match(TokenType.NEWLINE):
                    has_continuation = True
                    self._skip_newlines()
                else:
                    self._skip_newlines()
                prev_relational = self._in_relational_context
                self._in_relational_context = True
                try:
                    right = self._parse_intersect()
                finally:
                    self._in_relational_context = prev_relational
                left = NaturalJoin(
                    left=left,
                    right=right,
                    subscript=subscript,
                    line_break_after=has_continuation,
                    line=op_token.line,
                    column=op_token.column,
                )
            elif op_token.type == TokenType.DIV:
                # Detect line continuation
                has_continuation = False
                if self._match(TokenType.CONTINUATION):
                    self._advance()  # consume \
                    has_continuation = True
                    if self._match(TokenType.NEWLINE):
                        self._advance()
                    self._skip_newlines()
                elif self._match(TokenType.NEWLINE):
                    has_continuation = True
                    self._skip_newlines()
                else:
                    self._skip_newlines()
                prev_relational = self._in_relational_context
                self._in_relational_context = True
                try:
                    right = self._parse_intersect()
                finally:
                    self._in_relational_context = prev_relational
                left = Divide(
                    left=left,
                    right=right,
                    line_break_after=has_continuation,
                    line=op_token.line,
                    column=op_token.column,
                )
            elif op_token.type == TokenType.GROUP:
                group_node = self._parse_group_rhs(left, op_token)
                # Detect line continuation after full GROUP expression.
                # Unlike Divide/Join (which check *before* their right
                # operand), GROUP checks *after* its fully-parsed RHS.
                # A bare NEWLINE is only a continuation when a chaining
                # relational operator immediately follows on the next line
                # (join, div, cross, group, ungroup).  A NEWLINE before
                # EOF or any non-relational token is just a statement
                # terminator; treating it as a continuation injects \\
                # into inline math, producing invalid LaTeX.
                has_continuation = False
                if self._match(TokenType.CONTINUATION):
                    self._advance()  # consume \
                    has_continuation = True
                    if self._match(TokenType.NEWLINE):
                        self._advance()
                    self._skip_newlines()
                elif self._match(TokenType.NEWLINE):
                    has_continuation = self._next_non_newline_is_cross_op()
                    self._skip_newlines()
                else:
                    self._skip_newlines()
                if has_continuation:
                    # Replace the frozen node with line_break_after=True
                    if isinstance(group_node, GroupAggregate):
                        left = GroupAggregate(
                            relation=group_node.relation,
                            clauses=group_node.clauses,
                            line_break_after=True,
                            line=group_node.line,
                            column=group_node.column,
                        )
                    else:
                        left = Group(
                            relation=group_node.relation,
                            attrs=group_node.attrs,
                            alias=group_node.alias,
                            line_break_after=True,
                            line=group_node.line,
                            column=group_node.column,
                        )
                else:
                    left = group_node
            elif op_token.type == TokenType.UNGROUP:
                ungroup_node = self._parse_ungroup_rhs(left, op_token)
                # Detect line continuation after full UNGROUP expression
                has_continuation = False
                if self._match(TokenType.CONTINUATION):
                    self._advance()  # consume \
                    has_continuation = True
                    if self._match(TokenType.NEWLINE):
                        self._advance()
                    self._skip_newlines()
                elif self._match(TokenType.NEWLINE):
                    has_continuation = True
                    self._skip_newlines()
                else:
                    self._skip_newlines()
                if has_continuation:
                    # Replace the frozen Ungroup node with line_break_after=True
                    left = Ungroup(
                        relation=ungroup_node.relation,
                        alias=ungroup_node.alias,
                        line_break_after=True,
                        line=ungroup_node.line,
                        column=ungroup_node.column,
                    )
                else:
                    left = ungroup_node
            elif op_token.type == TokenType.EXTEND:
                left = self._parse_extend_full(left, op_token)
            else:
                # CROSS
                has_continuation = False
                if self._match(TokenType.CONTINUATION):
                    self._advance()  # consume \
                    has_continuation = True
                    if self._match(TokenType.NEWLINE):
                        self._advance()
                    self._skip_newlines()
                elif self._match(TokenType.NEWLINE):
                    has_continuation = True
                    self._skip_newlines()
                else:
                    self._skip_newlines()
                right = self._parse_intersect()
                left = BinaryOp(
                    operator=op_token.value,
                    left=left,
                    right=right,
                    line_break_after=has_continuation,
                    line=op_token.line,
                    column=op_token.column,
                )

            # After constructing the node, check for trailing continuation
            # that marks a break before the next operator in the chain.
            # Example: R join S \    ← \ after RHS, before next join
            #            join T
            # The just-constructed node gets line_break_after=True so the
            # caller knows to emit \\ before the next operator.
            left = self._apply_trailing_continuation(left)

        return left

    def _next_non_newline_is_cross_op(self) -> bool:
        """Peek ahead past newlines to see if a cross-level operator follows.

        Returns True when the next non-newline token is one of CROSS, JOIN,
        DIV, GROUP, or UNGROUP, indicating a natural line break in a chain.
        """
        pos = self.pos
        while pos < len(self.tokens) and self.tokens[pos].type == TokenType.NEWLINE:
            pos += 1
        if pos >= len(self.tokens):
            return False
        return self.tokens[pos].type in (
            TokenType.CROSS,
            TokenType.JOIN,
            TokenType.DIV,
            TokenType.GROUP,
            TokenType.UNGROUP,
            TokenType.EXTEND,
        )

    def _parse_extend_full(self, left: Expr, op_token: Token) -> Expr:
        """Parse an extend expression and handle post-expression line continuation.

        Mirrors the GROUP branch continuation logic: a bare NEWLINE only sets
        line_break_after when a chaining relational operator follows immediately.
        """
        extend_node = self._parse_extend_aggregate_rhs(left, op_token)
        has_continuation = False
        if self._match(TokenType.CONTINUATION):
            self._advance()  # consume \
            has_continuation = True
            if self._match(TokenType.NEWLINE):
                self._advance()
            self._skip_newlines()
        elif self._match(TokenType.NEWLINE):
            has_continuation = self._next_non_newline_is_cross_op()
            self._skip_newlines()
        else:
            self._skip_newlines()
        if has_continuation:
            return ExtendAggregate(
                relation=extend_node.relation,
                clauses=extend_node.clauses,
                line_break_after=True,
                line=extend_node.line,
                column=extend_node.column,
            )
        return extend_node

    def _apply_trailing_continuation(self, left: Expr) -> Expr:
        """Apply trailing continuation marker after a cross-level operator.

        Checks for a ``\\`` or natural newline-before-cross-op pattern after
        the just-constructed node.  Returns left with line_break_after=True
        if a continuation was detected, otherwise returns left unchanged.
        """
        if self._match(TokenType.CONTINUATION):
            self._advance()  # consume \
            if self._match(TokenType.NEWLINE):
                self._advance()
            self._skip_newlines()
            return dataclasses.replace(left, line_break_after=True)  # type: ignore[arg-type]
        if self._match(TokenType.NEWLINE) and self._next_non_newline_is_cross_op():
            self._skip_newlines()
            return dataclasses.replace(left, line_break_after=True)  # type: ignore[arg-type]
        return left

    # Token types that start an aggregator clause.
    _AGGREGATOR_TOKEN_TYPES: ClassVar[frozenset[TokenType]] = frozenset(
        {
            TokenType.COUNT,
            TokenType.SUM,
            TokenType.AVG,
            TokenType.MIN,
            TokenType.MAX,
            TokenType.MEDIAN,
        }
    )

    # Mapping from aggregator token type to Aggregator enum value.
    _TOKEN_TO_AGGREGATOR: ClassVar[dict[TokenType, Aggregator]] = {
        TokenType.COUNT: Aggregator.COUNT,
        TokenType.SUM: Aggregator.SUM,
        TokenType.AVG: Aggregator.AVG,
        TokenType.MIN: Aggregator.MIN,
        TokenType.MAX: Aggregator.MAX,
        TokenType.MEDIAN: Aggregator.MEDIAN,
    }

    def _parse_intersect(self) -> Expr:
        """Parse intersect and set difference operators.

        Supports multi-line expressions with natural line breaks.
        """
        left = self._parse_unary()

        while self._match(TokenType.INTERSECT, TokenType.SETMINUS):
            op_token = self._advance()
            # Detect line continuation (backslash or natural newline)
            has_continuation = False
            if self._match(TokenType.CONTINUATION):
                self._advance()  # consume \
                has_continuation = True
                if self._match(TokenType.NEWLINE):
                    self._advance()
                self._skip_newlines()
            elif self._match(TokenType.NEWLINE):
                has_continuation = True
                self._skip_newlines()
            else:
                self._skip_newlines()
            right = self._parse_unary()
            left = BinaryOp(
                operator=op_token.value,
                left=left,
                right=right,
                line_break_after=has_continuation,
                line=op_token.line,
                column=op_token.column,
            )

        return left

    def _dot_is_spaced(self, next_token: Token) -> bool:
        """True when the current PERIOD token has whitespace before the next token.

        Used to disambiguate the bullet separator (spaced: `pred . expr`)
        from field access (tight: `s.x`).  The current token must be a PERIOD.
        """
        period_token = self._current()
        return period_token.column + 1 < next_token.column

    def _parse_postfix(self, *, allow_space_separated: bool = True) -> Expr:
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

        # Check for generic instantiation S[X] or schema rename S[a/b].
        # Only treat [ as such if:
        # 1. Base is a type-like construct (Identifier or GenericInstantiation)
        # 2. The '[' immediately follows the last consumed token (no whitespace)
        # This prevents consuming '[' meant for justifications in equiv chains.
        while isinstance(base, (Identifier, GenericInstantiation)) and self._match(
            TokenType.LBRACKET
        ):
            # Check if '[' immediately follows the last token (no whitespace)
            # Use the tracked end position of the last consumed token
            lbracket_col = self._current().column

            # If on different lines or there's a gap,
            # don't treat as generic instantiation or schema rename
            if (
                self._current().line != self.last_token_line
                or lbracket_col > self.last_token_end_column
            ):
                # There's whitespace - likely a justification, not generic
                break

            if self._in_relational_context and self._bracket_contains_slash():
                # In a relational context, S[new/old] → RelationRename
                base = self._parse_relation_rename(base)
            else:
                base = self._parse_schema_rename_or_generic(base)

        # ANY expression base can take a [new/old] postfix to form a
        # RelationRename — handles compound operands such as
        # (S join T)[a/x] or sigma[p](R)[a/x].
        # The '[' must immediately follow the closing token (no whitespace),
        # and the bracket must contain a '/' to disambiguate from generic
        # instantiation.
        if (
            not isinstance(base, (Identifier, GenericInstantiation))
            and self._match(TokenType.LBRACKET)
            and self._current().line == self.last_token_line
            and self._current().column <= self.last_token_end_column
            and self._bracket_contains_slash()
        ):
            base = self._parse_relation_rename(base)

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

                    # In a comprehension/quantifier body, `.NUMBER` is not a valid
                    # tuple-projection: the base (last declared variable) has a
                    # basic type (N, Z, etc.), so §3.16 projection is ill-typed.
                    # The period must be the bullet separator.
                    if self._in_comprehension_body:
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
                    # Exception: allow the projection when we are parsing the RHS
                    # of a comparison operator (e.g. 'c.class = s.name }'), where
                    # the field is genuinely part of the predicate, not a body expr.
                    if (
                        self._in_comprehension_body
                        and token_after_id.type == TokenType.RBRACE
                        and not self._in_comparison_rhs
                        and self._dot_is_spaced(next_token)
                    ):
                        break

                    # In a comprehension body, do not allow chaining a second
                    # projection onto an existing TupleProjection.  The pattern
                    # 'base.field . bullet' (where base is already a projection)
                    # is always a bullet separator followed by a simple expression,
                    # never a doubly-chained projection.  Doubly-chained projections
                    # in comprehension bodies require explicit parentheses.
                    if self._in_comprehension_body and isinstance(
                        base, TupleProjection
                    ):
                        break

                    # Z RM §3.16: field selection requires the LHS to have a
                    # schema (binding) type.  If the identifier after `.` is itself
                    # a declared variable in the current schema-text, the period
                    # COULD be the bullet separator — but only if there is
                    # whitespace around the dot.  Tight `s.x` (no space) is always
                    # field access; spaced `. s` is the bullet.
                    # Example: `{ s : S | pred . s.x }` — the spaced `. ` is the
                    # bullet; the tight `.x` is field access on `s`.
                    if (
                        self._in_comprehension_body
                        and next_token.value in self._current_quantifier_vars
                        and self._dot_is_spaced(next_token)
                    ):
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
                        TokenType.RBIND,  # .field |} (inside binding {| ... |})
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

        When _in_schema_expr_context is True, the inner expression is parsed
        with schema-calculus precedence so that ``(S ; T)`` works correctly.
        """
        lparen_token = self._advance()  # Consume '('

        # Parse first expression — use schema-calculus entry point when in
        # schema-expression context so that ';' is treated as composition.
        if self._in_schema_expr_context:
            first_expr = self._parse_schema_pipe()
        else:
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
                if self._in_schema_expr_context:
                    elements.append(self._parse_schema_pipe())
                else:
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

    # ------------------------------------------------------------------
    # Relational algebra parsers (Phase 2.2)
    # ------------------------------------------------------------------

    def _parse_atom(self) -> Expr:
        """Parse atom.

        Handles: identifier, number, parenthesized expression, set comprehension,
        prefix operators (dom, ran, inv, id, P, P1, F, F1, bigcup, bigcap),
        function application f(x), lambda expressions, and relational algebra
        prefix operators (sigma, pi).
        """
        # Relational algebra prefix-with-args operators (Phase 2.2): sigma and pi
        if self._match(TokenType.SIGMA):
            return self._parse_restrict()
        if self._match(TokenType.PI):
            return self._parse_project()

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

        # θ-expression: theta SchemaRef  (Z RM §3.10)
        # Binds tightly at primary-expression level.
        if self._match(TokenType.THETA):
            theta_token = self._advance()
            # Require a schema reference (identifier-shaped atom) to follow.
            if not self._match(
                TokenType.IDENTIFIER,
                TokenType.DELTA,
                TokenType.XI,
            ):
                cur = self._current()
                if cur.type == TokenType.EOF:
                    raise ParserError(
                        "Unexpected end of input after 'theta';"
                        " expected schema name (e.g. theta S)",
                        cur,
                    )
                raise ParserError(
                    f"Expected schema name after theta,"
                    f" got {cur.type.name} ({cur.value!r})",
                    cur,
                )
            schema_ref = self._parse_atom()
            return Theta(
                expr=schema_ref,
                line=theta_token.line,
                column=theta_token.column,
            )

        # Identifiers (including keywords allowed as function names)
        # Note: Function application expr(...) is handled in _parse_postfix()
        # Note: Generic instantiation Type[X] is handled in _parse_postfix()
        # Note: Relational image R(| S |) is handled in _parse_postfix()
        if self._match(
            TokenType.IDENTIFIER,
            TokenType.UNION,
            TokenType.INTERSECT,
            TokenType.FILTER,
            # Delta and Xi are keywords in declaration context but remain
            # valid identifiers in expression context (e.g. Gamma shows Delta).
            TokenType.DELTA,
            TokenType.XI,
        ):
            name_token = self._advance()
            return Identifier(
                name=name_token.value, line=name_token.line, column=name_token.column
            )

        if self._match(TokenType.NUMBER):
            token = self._advance()
            return Number(value=token.value, line=token.line, column=token.column)

        if self._match(TokenType.STRING):
            token = self._advance()
            return StringLit(value=token.value, line=token.line, column=token.column)

        if self._match(TokenType.LPAREN):
            return self._parse_parenthesized_expr_or_tuple()

        # Binding literal {| name == expr, ... |} (Z RM §3.7)
        if self._match(TokenType.LBIND):
            return self._parse_binding()

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
            f"Expected identifier, number, '(', '{{', '{{|', '⟨', or lambda,"
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
