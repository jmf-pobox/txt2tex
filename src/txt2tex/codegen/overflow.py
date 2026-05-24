"""Overflow-warning helpers extracted from latex_gen.py.

These methods inspect generated LaTeX for likely page-margin overflow,
collect human-readable warnings, and expose them through
``emit_warnings`` / ``get_warnings`` / ``clear_warnings``.

State lives on :class:`LaTeXGenerator` instances (``_warn_overflow``,
``_overflow_warnings``, ``_overflow_threshold``) and is initialised in
``LaTeXGenerator.__init__``; this mixin only carries the methods.

Methods are byte-identical to their counterparts in the pre-refactor
monolithic ``latex_gen.py``; only their file location has changed.
"""

from __future__ import annotations

import sys
from typing import ClassVar

from txt2tex.codegen._dispatch import CodegenDispatch


class _OverflowCodegen(CodegenDispatch):  # pyright: ignore[reportUnusedClass]
    """Mixin: page-overflow warning collection."""

    # Default threshold for line-wrap (LaTeX characters).
    # Z math content is denser than plain text; empirical observation shows
    # predicates of 100+ LaTeX chars frequently overflow the column width.
    # The lower bound (100) is conservative enough to wrap genuinely long
    # predicates while leaving normal one-line schema predicates alone.
    # Use --overflow-threshold to adjust for specific documents.
    DEFAULT_OVERFLOW_THRESHOLD: ClassVar[int] = 80

    def _check_overflow(
        self,
        latex: str,
        source_line: int,
        context: str,
        content_preview: str | None = None,
    ) -> None:
        """Check if generated LaTeX may overflow page margins.

        Args:
            latex: The generated LaTeX string to check.
            source_line: Source file line number for the warning.
            context: Description of where overflow occurs (e.g., "axdef where").
            content_preview: Optional preview of source content for warning.
        """
        if not self._warn_overflow:
            return

        # Split on LaTeX line breaks (\\) and check each line individually
        # This respects user-inserted line breaks via \ continuation
        lines = latex.split("\\\\")

        # Find the longest line (strip leading whitespace like \t1)
        max_line_len = 0
        for line in lines:
            # Strip common indentation markers
            stripped = line.lstrip()
            if stripped.startswith("\\t1 "):
                stripped = stripped[4:]
            max_line_len = max(max_line_len, len(stripped))

        if max_line_len <= self._overflow_threshold:
            return

        # Build warning message.  Parenthesise to avoid the `or` binding
        # tighter than the conditional expression, which would discard a
        # caller-supplied `content_preview` whenever `len(latex) <= 50`.
        preview = (
            (content_preview or (latex[:50] + "..."))
            if len(latex) > 50
            else (content_preview or latex)
        )
        warning = (
            f"Warning: Line {source_line} may overflow page margin "
            f"(~{max_line_len} chars)\n"
            f"  In: {context}\n"
            f"  Content: {preview}\n"
            f"  Suggestion: Break long expressions using indentation continuation"
        )
        self._overflow_warnings.append(warning)

    def emit_warnings(self) -> None:
        """Emit all collected overflow warnings to stderr."""
        for warning in self._overflow_warnings:
            print(warning, file=sys.stderr)

    def get_warnings(self) -> list[str]:
        """Return collected overflow warnings (for testing)."""
        return self._overflow_warnings.copy()

    def clear_warnings(self) -> None:
        """Clear the collected warning buffer.

        Call after consuming warnings (e.g. between REPL turns) so that
        warnings from one turn do not reappear in subsequent turns.
        """
        self._overflow_warnings.clear()

    # -------------------------------------------------------------------------
    # Fuzz/Standard LaTeX mode helpers
    # -------------------------------------------------------------------------
