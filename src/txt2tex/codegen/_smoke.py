"""Smoke-test mixin — verifies the mixin dispatch pattern with one handler.

This module will be absorbed into text_blocks.py in Batch 3 (Move 8).
It exists only to validate that the codegen/ mixin infrastructure works
before Batch 1 begins.
"""

from __future__ import annotations

from txt2tex.ast_nodes import PageBreak
from txt2tex.codegen._dispatch import item_register


class _SmokeTestMixin:  # pyright: ignore[reportUnusedClass]
    """Single-handler mixin used to validate the mixin dispatch infrastructure."""

    @item_register.register(PageBreak)
    def _generate_pagebreak(self, node: PageBreak) -> list[str]:
        """Generate LaTeX for page break.

        PAGEBREAK: inserts a page break in PDF output.
        """
        return [r"\newpage", ""]
