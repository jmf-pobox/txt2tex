"""Error-construction helpers for the recursive-descent parser.

Covers: ``_reject_stray_slash`` and ``_reject_reserved_decl_name``.
``ParserError`` itself lives in ``parser_pkg/_base.py`` because the
mixins consume it from there.

This mixin is composed into :class:`Parser` via multiple inheritance.
Method bodies are byte-identical to their counterparts in the
pre-refactor monolithic ``parser.py``; only their file location has
changed.
"""

from __future__ import annotations

from txt2tex.parser_pkg._base import ParserBase, ParserError
from txt2tex.tokens import Token, TokenType


class _ErrorsParser(ParserBase):  # pyright: ignore[reportUnusedClass]
    """Mixin: error-construction helpers."""

    def _reject_stray_slash(self) -> None:
        """Raise ParserError if the current token is a stray SLASH.

        '/' is only valid inside schema rename brackets ``S[a/b]``.
        When it appears in any other position it produces a confusing
        generic "unexpected token" message.  This helper fires first and
        gives a targeted diagnostic.
        """
        if self._match(TokenType.SLASH):
            raise ParserError(
                "'/' is not a valid operator here; the slash is only valid"
                " inside schema rename brackets S[a/b]."
                " Did you mean '/=' (not equal) or '/in' (not in)?",
                self._current(),
            )

    def _reject_reserved_decl_name(self, tok: Token) -> None:
        """Raise ParserError if `tok.value` is a reserved operator keyword.

        Operator names that have a dedicated LaTeX expansion (id → \\id,
        dom → \\dom, etc.) cannot be used as declaration variable names
        because the generator emits the operator symbol, producing
        invalid Z that fuzz rejects.
        """
        if tok.value in self._RESERVED_DECL_NAMES:
            msg = (
                f"{tok.value!r} is a reserved Z operator name and cannot be used "
                f"as a declaration variable (it would render as the operator "
                f"in LaTeX). Rename to a non-conflicting identifier "
                f"(e.g. {tok.value}1, {tok.value}Val, my{tok.value.capitalize()})."
            )
            raise ParserError(msg, tok)
