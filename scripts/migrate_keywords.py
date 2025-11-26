#!/usr/bin/env python3
"""LLM-powered migration script: and/or/not → land/lor/lnot

This script uses Anthropic's Claude API to intelligently distinguish between
mathematical expressions and English prose when migrating keywords.

Usage:
    python scripts/migrate_keywords.py <file.txt> --dry-run    # Preview changes
    python scripts/migrate_keywords.py <file.txt> --apply      # Apply changes
    python scripts/migrate_keywords.py <file.txt> --threshold 0.8  # Custom threshold

Environment:
    ANTHROPIC_API_KEY: Required API key for Claude
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

try:
    import anthropic
except ImportError:
    print("ERROR: anthropic package not installed")
    print("Install with: pip install anthropic")
    sys.exit(1)


# Keyword mappings
KEYWORD_MAP = {
    "and": "land",
    "or": "lor",
    "not": "lnot",
}


@dataclass
class KeywordOccurrence:
    """Represents a single keyword occurrence in a line."""

    keyword: str  # Original keyword (and/or/not)
    replacement: str  # New keyword (land/lor/lnot)
    position: int  # Character position in line
    end_position: int  # End of keyword
    is_math_probability: float  # 0.0-1.0
    reasoning: str  # LLM explanation
    should_replace: bool  # Based on threshold


@dataclass
class LineAnalysis:
    """Analysis result for a single line."""

    line_number: int
    original_line: str
    occurrences: list[KeywordOccurrence]
    modified_line: str | None  # None if no changes


class KeywordMigrator:
    """LLM-powered keyword migration engine."""

    def __init__(
        self,
        api_key: str,
        threshold: float = 0.7,
        model: str = "claude-sonnet-4-5-20250929",
    ):
        """Initialize migrator.

        Args:
            api_key: Anthropic API key
            threshold: Confidence threshold for replacement (0.0-1.0)
            model: Claude model to use
        """
        self.client = anthropic.Anthropic(api_key=api_key)
        self.threshold = threshold
        self.model = model

    def analyze_keyword_occurrence(
        self,
        keyword: str,
        position: int,
        current_line: str,
        prev_line: str | None,
        next_line: str | None,
    ) -> tuple[float, str]:
        """Use LLM to determine if keyword is mathematical.

        Args:
            keyword: The keyword (and/or/not)
            position: Character position in current_line
            current_line: The line containing the keyword
            prev_line: Previous line (context)
            next_line: Next line (context)

        Returns:
            (probability, reasoning) where probability is 0.0-1.0
        """
        replacement = KEYWORD_MAP[keyword]

        # Build prompt with context
        prompt = f"""You are analyzing a Z notation mathematical specification file.

Context (3-line window):
Previous line: {prev_line or "(start of file)"}
Current line:  {current_line}
Next line:     {next_line or "(end of file)"}

In the current line, the word "{keyword}" appears at position {position}.

Question: Is this occurrence mathematical notation (should become "{replacement}")
or English prose (should stay "{keyword}")?

Context clues for mathematical usage:
- In formulas: p and q, x or y, not p
- In schemas/axdef/gendef blocks
- Near math operators: =>, <=>, forall, exists, in, subset
- In TRUTH TABLE: column headers
- In EQUIV: blocks (equivalence reasoning)
- In PROOF: blocks (proof trees)
- In quantified predicates: forall x | ...

Context clues for English prose:
- In TEXT: blocks (natural language)
- In comments (// ...)
- In justification labels [...] with prose
- Surrounded by articles (a, an, the)
- In explanatory sentences

Respond with ONLY valid JSON (no markdown, no extra text):
{{"is_math": true, "confidence": 0.95, "reasoning": "Appears in formula 'p and q'"}}

JSON response:"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=200,
                temperature=0.0,  # Deterministic
                messages=[{"role": "user", "content": prompt}],
            )

            # Extract JSON from response
            content = response.content[0].text.strip()

            # Handle markdown code blocks if present
            if content.startswith("```"):
                # Extract JSON from code block
                lines = content.split("\n")
                json_lines = [
                    line for line in lines if not line.startswith("```")
                ]
                content = "\n".join(json_lines).strip()

            result = json.loads(content)

            is_math = result.get("is_math", False)
            confidence = result.get("confidence", 0.5)
            reasoning = result.get("reasoning", "No reasoning provided")

            probability = confidence if is_math else (1.0 - confidence)

            return (probability, reasoning)

        except json.JSONDecodeError as e:
            print(
                f"WARNING: Failed to parse LLM response as JSON: {e}",
                file=sys.stderr,
            )
            print(f"Response was: {content}", file=sys.stderr)
            # Default to not replacing (safer)
            return (0.0, f"JSON parse error: {e}")
        except Exception as e:
            print(
                f"WARNING: LLM API error: {e}",
                file=sys.stderr,
            )
            return (0.0, f"API error: {e}")

    def find_keyword_occurrences(
        self, line: str, keyword: str
    ) -> list[tuple[int, int]]:
        """Find all occurrences of keyword in line as whole words.

        Args:
            line: Line to search
            keyword: Keyword to find

        Returns:
            List of (start_pos, end_pos) tuples
        """
        occurrences = []
        # Use word boundaries to match whole words only
        pattern = r"\b" + re.escape(keyword) + r"\b"
        for match in re.finditer(pattern, line):
            occurrences.append((match.start(), match.end()))
        return occurrences

    def analyze_line(
        self,
        line_number: int,
        current_line: str,
        prev_line: str | None,
        next_line: str | None,
    ) -> LineAnalysis:
        """Analyze a single line for keyword replacements.

        Args:
            line_number: 1-based line number
            current_line: The line to analyze
            prev_line: Previous line (context)
            next_line: Next line (context)

        Returns:
            LineAnalysis with all occurrences scored
        """
        occurrences: list[KeywordOccurrence] = []

        # Check each keyword
        for keyword in KEYWORD_MAP:
            positions = self.find_keyword_occurrences(current_line, keyword)

            for start_pos, end_pos in positions:
                probability, reasoning = self.analyze_keyword_occurrence(
                    keyword, start_pos, current_line, prev_line, next_line
                )

                occurrence = KeywordOccurrence(
                    keyword=keyword,
                    replacement=KEYWORD_MAP[keyword],
                    position=start_pos,
                    end_position=end_pos,
                    is_math_probability=probability,
                    reasoning=reasoning,
                    should_replace=probability >= self.threshold,
                )
                occurrences.append(occurrence)

        # Sort by position (descending) for safe replacement
        occurrences.sort(key=lambda x: x.position, reverse=True)

        # Build modified line if needed
        modified_line = None
        if any(occ.should_replace for occ in occurrences):
            modified_line = current_line
            for occ in occurrences:
                if occ.should_replace:
                    modified_line = (
                        modified_line[: occ.position]
                        + occ.replacement
                        + modified_line[occ.end_position :]
                    )

        return LineAnalysis(
            line_number=line_number,
            original_line=current_line,
            occurrences=occurrences,
            modified_line=modified_line,
        )

    def analyze_file(self, file_path: Path) -> list[LineAnalysis]:
        """Analyze entire file line by line.

        Args:
            file_path: Path to file

        Returns:
            List of LineAnalysis for each line
        """
        with open(file_path, encoding="utf-8") as f:
            lines = f.readlines()

        results: list[LineAnalysis] = []

        for i, line in enumerate(lines):
            line_number = i + 1
            current_line = line.rstrip("\n")
            prev_line = lines[i - 1].rstrip("\n") if i > 0 else None
            next_line = (
                lines[i + 1].rstrip("\n") if i < len(lines) - 1 else None
            )

            analysis = self.analyze_line(
                line_number, current_line, prev_line, next_line
            )
            results.append(analysis)

        return results

    def apply_migration(
        self, file_path: Path, analyses: list[LineAnalysis]
    ) -> None:
        """Apply migration to file with backup.

        Args:
            file_path: Path to file
            analyses: List of LineAnalysis results
        """
        # Create timestamped backup
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_path = file_path.with_suffix(f".txt.backup.{timestamp}")

        # Backup original
        with open(file_path, encoding="utf-8") as f:
            original_content = f.read()
        with open(backup_path, "w", encoding="utf-8") as f:
            f.write(original_content)

        print(f"Created backup: {backup_path}")

        # Write modified file
        with open(file_path, "w", encoding="utf-8") as f:
            for analysis in analyses:
                line = (
                    analysis.modified_line
                    if analysis.modified_line is not None
                    else analysis.original_line
                )
                f.write(line + "\n")

        print(f"Applied changes to: {file_path}")


def print_analysis_report(analyses: list[LineAnalysis]) -> None:
    """Print detailed analysis report."""
    total_lines = len(analyses)
    lines_with_changes = sum(
        1 for a in analyses if a.modified_line is not None
    )
    total_occurrences = sum(len(a.occurrences) for a in analyses)
    replacements = sum(
        sum(1 for occ in a.occurrences if occ.should_replace) for a in analyses
    )

    print("\n" + "=" * 80)
    print("MIGRATION ANALYSIS REPORT")
    print("=" * 80)
    print(f"Total lines: {total_lines}")
    print(f"Lines with changes: {lines_with_changes}")
    print(f"Total keyword occurrences: {total_occurrences}")
    print(f"Replacements recommended: {replacements}")
    print("=" * 80 + "\n")

    for analysis in analyses:
        if not analysis.occurrences:
            continue

        print(f"Line {analysis.line_number}: {analysis.original_line}")

        for occ in sorted(analysis.occurrences, key=lambda x: x.position):
            action = "REPLACE" if occ.should_replace else "KEEP"
            print(
                f"  [{action}] pos={occ.position} "
                f'"{occ.keyword}" → "{occ.replacement}" '
                f"(confidence={occ.is_math_probability:.2f})"
            )
            print(f"    Reasoning: {occ.reasoning}")

        if analysis.modified_line is not None:
            print(f"  MODIFIED: {analysis.modified_line}")
        print()


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Migrate and/or/not to land/lor/lnot using LLM analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("file", type=Path, help="File to migrate")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show changes without applying",
    )
    parser.add_argument(
        "--apply", action="store_true", help="Apply changes to file"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.7,
        help="Confidence threshold for replacement (default: 0.7)",
    )
    parser.add_argument(
        "--model",
        default="claude-sonnet-4-5-20250929",
        help="Claude model to use",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Auto-confirm changes (skip interactive prompt)",
    )

    args = parser.parse_args()

    # Validate arguments
    if not args.dry_run and not args.apply:
        print("ERROR: Must specify --dry-run or --apply", file=sys.stderr)
        return 1

    if not args.file.exists():
        print(f"ERROR: File not found: {args.file}", file=sys.stderr)
        return 1

    # Get API key
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY environment variable not set", file=sys.stderr)
        return 1

    # Initialize migrator
    migrator = KeywordMigrator(
        api_key=api_key, threshold=args.threshold, model=args.model
    )

    print(f"Analyzing: {args.file}")
    print(f"Threshold: {args.threshold}")
    print(f"Model: {args.model}")
    print()

    # Analyze file
    analyses = migrator.analyze_file(args.file)

    # Print report
    print_analysis_report(analyses)

    # Apply if requested
    if args.apply:
        if args.yes:
            migrator.apply_migration(args.file, analyses)
            print("\nMigration complete!")
        else:
            response = input("Apply changes? [y/N]: ")
            if response.lower() == "y":
                migrator.apply_migration(args.file, analyses)
                print("\nMigration complete!")
            else:
                print("\nMigration cancelled.")
                return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
