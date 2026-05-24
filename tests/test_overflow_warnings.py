"""Tests for LaTeXGenerator overflow-warning behaviour (`_check_overflow`).

Round-4 fixed an operator-precedence bug in the Python preview
expression. Without parentheses, ``content_preview or X if Y else Z``
parses as ``(content_preview or X) if Y else Z`` — silently discarding
the caller-supplied preview whenever the short-latex branch was taken.
These tests pin the corrected behaviour.
"""

from __future__ import annotations

from txt2tex.latex_gen import LaTeXGenerator


def _make_gen(threshold: int = 5) -> LaTeXGenerator:
    """Build a generator with overflow warnings on and a tight threshold."""
    return LaTeXGenerator(warn_overflow=True, overflow_threshold=threshold)


def test_short_latex_uses_supplied_preview() -> None:
    """When len(latex) <= 50 and content_preview is supplied, the preview is used.

    This is the case Round-4 fixed: previously `content_preview or latex[:50] + "..."`
    bound the `or` tighter than the conditional, so the caller-supplied
    preview was silently dropped for short latex.
    """
    gen = _make_gen(threshold=3)
    gen._check_overflow(
        latex="aaaaaa",  # 6 chars, exceeds threshold=3, fits under 50
        source_line=1,
        context="test",
        content_preview="my-preview",
    )
    warnings = gen.get_warnings()
    assert len(warnings) == 1
    assert "my-preview" in warnings[0]


def test_short_latex_falls_back_to_full_latex_when_no_preview() -> None:
    """Without a preview, short latex (<=50) is embedded verbatim."""
    gen = _make_gen(threshold=3)
    gen._check_overflow(
        latex="aaaaaa",
        source_line=1,
        context="test",
        content_preview=None,
    )
    warnings = gen.get_warnings()
    assert len(warnings) == 1
    assert "aaaaaa" in warnings[0]


def test_long_latex_uses_supplied_preview_over_truncation() -> None:
    """When latex > 50 chars and preview is supplied, prefer the preview."""
    gen = _make_gen(threshold=3)
    gen._check_overflow(
        latex="x" * 80,
        source_line=1,
        context="test",
        content_preview="my-preview",
    )
    warnings = gen.get_warnings()
    assert len(warnings) == 1
    assert "my-preview" in warnings[0]


def test_long_latex_truncates_when_no_preview() -> None:
    """When latex > 50 chars and no preview, embed the first 50 + ellipsis."""
    gen = _make_gen(threshold=3)
    long_latex = "x" * 80
    gen._check_overflow(
        latex=long_latex,
        source_line=1,
        context="test",
        content_preview=None,
    )
    warnings = gen.get_warnings()
    assert len(warnings) == 1
    assert long_latex[:50] in warnings[0]
    assert "..." in warnings[0]


def test_overflow_below_threshold_emits_no_warning() -> None:
    """Latex shorter than threshold raises no warning."""
    gen = _make_gen(threshold=50)
    gen._check_overflow(
        latex="short",
        source_line=1,
        context="test",
        content_preview="anything",
    )
    assert gen.get_warnings() == []


def test_overflow_warnings_disabled_emits_nothing() -> None:
    """warn_overflow=False suppresses all warnings."""
    gen = LaTeXGenerator(warn_overflow=False, overflow_threshold=1)
    gen._check_overflow(
        latex="x" * 100,
        source_line=1,
        context="test",
        content_preview=None,
    )
    assert gen.get_warnings() == []
