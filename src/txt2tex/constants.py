"""Shared constants for txt2tex.

This module contains constants used across multiple modules to avoid duplication.
"""

from __future__ import annotations

# Common English prose words used to distinguish prose from mathematical expressions
# These words are checked during parsing and LaTeX generation to detect when text
# is prose rather than mathematical notation (e.g., "x >= 0 is true" vs "x >= 0")
PROSE_WORDS: frozenset[str] = frozenset(
    {
        # Articles
        "a",
        "an",
        "the",
        # Being verbs
        "be",
        "been",
        "is",
        "are",
        "was",
        "were",
        # Auxiliary verbs
        "can",
        "could",
        "do",
        "does",
        "did",
        "had",
        "has",
        "have",
        "may",
        "might",
        "must",
        "should",
        "will",
        "would",
        # Boolean
        "false",
        "true",
        # Demonstratives
        "that",
        "these",
        "this",
        "those",
        # Pronouns
        "it",
        "its",
        "them",
        "they",
        "whatever",
        "whoever",
        # Prepositions
        "as",
        "at",
        "by",
        "for",
        "from",
        "in",
        "of",
        "on",
        "to",
        "with",
        # Misc
        "here",
        "syntax",
        "there",
        "valid",
    }
)
