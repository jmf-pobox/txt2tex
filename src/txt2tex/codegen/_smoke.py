"""Smoke-test mixin — placeholder retained after Move 0.

The PageBreak handler that originally lived here was moved to
``text_blocks.py`` in Batch 3.  This stub remains so the import chain
in ``codegen/__init__.py`` does not need rewriting mid-phase.
"""

from __future__ import annotations

from txt2tex.codegen._dispatch import CodegenDispatch


class _SmokeTestMixin(CodegenDispatch):  # pyright: ignore[reportUnusedClass]
    """Empty placeholder; behaviour now lives in _TextBlocksCodegen."""
