"""BibTeX parser for txt2tex - parses .bib files into structured entries."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class BibEntry:
    """A parsed bibliography entry.

    Represents a single entry from a BibTeX file with common fields
    extracted for citation formatting.
    """

    key: str
    entry_type: str  # book, article, misc, unpublished, etc.
    author: str = ""
    title: str = ""
    year: str = ""
    publisher: str = ""
    address: str = ""
    howpublished: str = ""
    note: str = ""
    institution: str = ""


class BibParser:
    """Parser for BibTeX .bib files.

    Parses BibTeX entries and extracts common fields used for citation
    formatting. Handles nested braces in field values correctly.

    Example:
        parser = BibParser()
        entries = parser.parse(Path("references.bib"))
        for key, entry in entries.items():
            print(f"{key}: {entry.title} ({entry.year})")
    """

    # Fields we extract from BibTeX entries
    SUPPORTED_FIELDS = frozenset(
        {
            "author",
            "title",
            "year",
            "publisher",
            "address",
            "howpublished",
            "note",
            "institution",
        }
    )

    def parse(self, bib_path: Path) -> dict[str, BibEntry]:
        """Parse a BibTeX file and return entries by citation key.

        Args:
            bib_path: Path to the .bib file.

        Returns:
            Dictionary mapping citation keys to BibEntry objects.
            Returns empty dict if file doesn't exist.
        """
        if not bib_path.exists():
            return {}

        content = bib_path.read_text(encoding="utf-8")
        return self._parse_content(content)

    def _parse_content(self, content: str) -> dict[str, BibEntry]:
        """Parse BibTeX content string into entries.

        Args:
            content: Raw BibTeX file content.

        Returns:
            Dictionary mapping citation keys to BibEntry objects.
        """
        entries: dict[str, BibEntry] = {}

        # Pattern for entry headers: @type{key,
        entry_header = re.compile(r"@(\w+)\{([^,]+),")

        for header_match in entry_header.finditer(content):
            entry_type = header_match.group(1).lower()
            key = header_match.group(2).strip()

            # Find the entry's content by matching braces
            fields_str = self._extract_entry_body(content, header_match.end())

            entry = self._parse_entry_fields(key, entry_type, fields_str)
            entries[key] = entry

        return entries

    def _extract_entry_body(self, content: str, start: int) -> str:
        """Extract the body of a BibTeX entry by matching braces.

        Args:
            content: Full file content.
            start: Position after the opening brace and comma.

        Returns:
            The content between the entry's braces.
        """
        brace_count = 1
        end = start

        while end < len(content) and brace_count > 0:
            if content[end] == "{":
                brace_count += 1
            elif content[end] == "}":
                brace_count -= 1
            end += 1

        return content[start : end - 1]  # Exclude final }

    def _parse_entry_fields(
        self, key: str, entry_type: str, fields_str: str
    ) -> BibEntry:
        """Parse individual fields from entry body.

        Args:
            key: Citation key.
            entry_type: Entry type (book, article, etc.).
            fields_str: The raw field content.

        Returns:
            Populated BibEntry.
        """
        entry = BibEntry(key=key, entry_type=entry_type)

        # Pattern for field start: name = {
        field_pattern = re.compile(r"(\w+)\s*=\s*\{")

        pos = 0
        while pos < len(fields_str):
            field_match = field_pattern.search(fields_str, pos)
            if not field_match:
                break

            field_name = field_match.group(1).lower()
            value_start = field_match.end()

            # Find matching closing brace (handles nested braces)
            field_value = self._extract_braced_value(fields_str, value_start)
            pos = value_start + len(field_value) + 1

            # Only process supported fields
            if field_name not in self.SUPPORTED_FIELDS:
                continue

            # Clean up whitespace
            field_value = " ".join(field_value.split())

            # Set the appropriate field
            if field_name == "author":
                entry.author = field_value
            elif field_name == "title":
                entry.title = field_value
            elif field_name == "year":
                entry.year = field_value
            elif field_name == "publisher":
                entry.publisher = field_value
            elif field_name == "address":
                entry.address = field_value
            elif field_name == "howpublished":
                entry.howpublished = field_value
            elif field_name == "note":
                entry.note = field_value
            elif field_name == "institution":
                entry.institution = field_value

        return entry

    def _extract_braced_value(self, content: str, start: int) -> str:
        """Extract a brace-delimited value, handling nested braces.

        Args:
            content: String containing the value.
            start: Position after the opening brace.

        Returns:
            The content between balanced braces.
        """
        brace_count = 1
        end = start

        while end < len(content) and brace_count > 0:
            if content[end] == "{":
                brace_count += 1
            elif content[end] == "}":
                brace_count -= 1
            end += 1

        return content[start : end - 1]
