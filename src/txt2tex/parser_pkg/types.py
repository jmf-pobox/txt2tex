"""Parser rules for type expressions and generic parameters.

Covers: ``_parse_function_type``, ``_parse_generic_instantiation``,
``_parse_generic_params``.

This mixin is composed into :class:`Parser` via multiple inheritance.
Method bodies are byte-identical to their counterparts in the
pre-refactor monolithic ``parser.py``; only their file location has
changed.
"""

from __future__ import annotations

from txt2tex.ast_nodes import Expr, FunctionType, GenericInstantiation
from txt2tex.parser_pkg._base import ParserBase, ParserError
from txt2tex.tokens import TokenType


class _TypesParser(ParserBase):  # pyright: ignore[reportUnusedClass]
    """Mixin: rules for type expressions and generic parameters."""

    def _parse_generic_instantiation(self, base: Expr) -> GenericInstantiation:
        """Parse generic instantiation S[T, ...] — '[' not yet consumed."""
        lbracket_token = self._advance()  # Consume '['

        type_params: list[Expr] = []

        if self._match(TokenType.RBRACKET):
            raise ParserError(
                "Expected at least one type parameter in generic instantiation",
                self._current(),
            )

        type_params.append(self._parse_expr())

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

        return GenericInstantiation(
            base=base,
            type_params=type_params,
            line=lbracket_token.line,
            column=lbracket_token.column,
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
