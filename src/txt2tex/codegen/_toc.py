"""TOC depth keyword mapping — shared between latex_gen and text_blocks."""

from __future__ import annotations


def toc_depth_from_keyword(value: str) -> int:
    """Return numeric TOC depth from a CONTENTS: keyword string.

    Maps: "1" → 1; empty / "2" / unrecognised → 2; "3" / "full" / "all" → 3.
    Bare CONTENTS: and unknown values default to 2 (sections + subsections).
    """
    normalised = value.strip().lower()
    if normalised == "1":
        return 1
    if normalised in ("3", "full", "all"):
        return 3
    return 2
