"""Parser for txt2tex - converts tokens into AST."""

from __future__ import annotations

from txt2tex.ast_nodes import BinaryOp, Expr, Identifier, UnaryOp
from txt2tex.tokens import Token, TokenType


class ParserError(Exception):
    """Raised when parser encounters invalid syntax."""

    def __init__(self, message: str, token: Token) -> None:
        """Initialize parser error with token position."""
        super().__init__(f"Line {token.line}, column {token.column}: {message}")
        self.token = token


class Parser:
    """
    Recursive descent parser for Phase 0: simple propositional logic.

    Grammar (with precedence from lowest to highest):
        expr     ::= iff
        iff      ::= implies ( '<=>' implies )*
        implies  ::= or ( '=>' or )*
        or       ::= and ( 'or' and )*
        and      ::= unary ( 'and' unary )*
        unary    ::= 'not' unary | primary
        primary  ::= IDENTIFIER
    """

    def __init__(self, tokens: list[Token]) -> None:
        """Initialize parser with token list."""
        self.tokens = tokens
        self.pos = 0

    def parse(self) -> Expr:
        """Parse tokens and return AST."""
        expr = self._parse_expr()
        if not self._at_end():
            raise ParserError(
                f"Unexpected token after expression: {self._current().value!r}",
                self._current(),
            )
        return expr

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

    def _parse_expr(self) -> Expr:
        """Parse expression (entry point)."""
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
        left = self._parse_unary()

        while self._match(TokenType.AND):
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

        return self._parse_primary()

    def _parse_primary(self) -> Expr:
        """Parse primary expression (identifier)."""
        if self._match(TokenType.IDENTIFIER):
            token = self._advance()
            return Identifier(name=token.value, line=token.line, column=token.column)

        raise ParserError(
            f"Expected identifier, got {self._current().type.name}", self._current()
        )
