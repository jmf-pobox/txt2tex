"""Tests for BibTeX parser."""

from __future__ import annotations

from pathlib import Path
from tempfile import NamedTemporaryFile

import pytest

from txt2tex.bib_parser import BibEntry, BibParser


class TestBibEntry:
    """Tests for BibEntry dataclass."""

    def test_creation_with_required_fields(self) -> None:
        """Test creating a BibEntry with required fields only."""
        entry = BibEntry(key="test2023", entry_type="book")
        assert entry.key == "test2023"
        assert entry.entry_type == "book"
        assert entry.author == ""
        assert entry.title == ""

    def test_creation_with_all_fields(self) -> None:
        """Test creating a BibEntry with all fields."""
        entry = BibEntry(
            key="spivey92",
            entry_type="book",
            author="Spivey, J. M.",
            title="The Z Notation",
            year="1992",
            publisher="Prentice Hall",
            address="Upper Saddle River, NJ",
            howpublished="",
            note="",
            institution="",
        )
        assert entry.key == "spivey92"
        assert entry.author == "Spivey, J. M."
        assert entry.title == "The Z Notation"
        assert entry.year == "1992"
        assert entry.publisher == "Prentice Hall"
        assert entry.address == "Upper Saddle River, NJ"


class TestBibParser:
    """Tests for BibParser class."""

    @pytest.fixture
    def parser(self) -> BibParser:
        """Create a BibParser instance."""
        return BibParser()

    def test_parse_nonexistent_file(self, parser: BibParser) -> None:
        """Test parsing a file that doesn't exist returns empty dict."""
        result = parser.parse(Path("/nonexistent/path/file.bib"))
        assert result == {}

    def test_parse_empty_file(self, parser: BibParser) -> None:
        """Test parsing an empty file returns empty dict."""
        with NamedTemporaryFile(mode="w", suffix=".bib", delete=False) as f:
            f.write("")
            f.flush()
            result = parser.parse(Path(f.name))
        assert result == {}

    def test_parse_single_book_entry(self, parser: BibParser) -> None:
        """Test parsing a single book entry."""
        bib_content = """
@book{spivey92,
  author = {Spivey, J. M.},
  title = {The Z Notation: A Reference Manual},
  publisher = {Prentice Hall},
  year = {1992},
  address = {Upper Saddle River, NJ}
}
"""
        with NamedTemporaryFile(mode="w", suffix=".bib", delete=False) as f:
            f.write(bib_content)
            f.flush()
            result = parser.parse(Path(f.name))

        assert len(result) == 1
        assert "spivey92" in result

        entry = result["spivey92"]
        assert entry.entry_type == "book"
        assert entry.author == "Spivey, J. M."
        assert entry.title == "The Z Notation: A Reference Manual"
        assert entry.publisher == "Prentice Hall"
        assert entry.year == "1992"
        assert entry.address == "Upper Saddle River, NJ"

    def test_parse_misc_entry(self, parser: BibParser) -> None:
        """Test parsing a misc entry with howpublished field."""
        bib_content = """
@misc{simpson25a,
  author = {Simpson, A.},
  title = {Introduction and propositions},
  howpublished = {Lecture slides for Software Engineering Mathematics},
  year = {2025}
}
"""
        with NamedTemporaryFile(mode="w", suffix=".bib", delete=False) as f:
            f.write(bib_content)
            f.flush()
            result = parser.parse(Path(f.name))

        assert len(result) == 1
        entry = result["simpson25a"]
        assert entry.entry_type == "misc"
        expected = "Lecture slides for Software Engineering Mathematics"
        assert entry.howpublished == expected

    def test_parse_unpublished_entry(self, parser: BibParser) -> None:
        """Test parsing an unpublished entry with note field."""
        bib_content = """
@unpublished{simpson-notes,
  author = {Simpson, A.},
  title = {From Discrete Mathematics to State-Based Models},
  note = {Unpublished course notes},
  year = {2025}
}
"""
        with NamedTemporaryFile(mode="w", suffix=".bib", delete=False) as f:
            f.write(bib_content)
            f.flush()
            result = parser.parse(Path(f.name))

        assert len(result) == 1
        entry = result["simpson-notes"]
        assert entry.entry_type == "unpublished"
        assert entry.note == "Unpublished course notes"

    def test_parse_multiple_entries(self, parser: BibParser) -> None:
        """Test parsing multiple entries."""
        bib_content = """
@book{book1,
  author = {Author One},
  title = {First Book},
  year = {2020}
}

@article{article1,
  author = {Author Two},
  title = {An Article},
  year = {2021}
}

@misc{misc1,
  author = {Author Three},
  title = {Some Notes},
  year = {2022}
}
"""
        with NamedTemporaryFile(mode="w", suffix=".bib", delete=False) as f:
            f.write(bib_content)
            f.flush()
            result = parser.parse(Path(f.name))

        assert len(result) == 3
        assert "book1" in result
        assert "article1" in result
        assert "misc1" in result

    def test_parse_entry_with_nested_braces(self, parser: BibParser) -> None:
        """Test parsing entry with nested braces in field values."""
        bib_content = """
@book{test,
  author = {Smith, {John Q.}},
  title = {A Book {With} Nested Braces},
  year = {2023}
}
"""
        with NamedTemporaryFile(mode="w", suffix=".bib", delete=False) as f:
            f.write(bib_content)
            f.flush()
            result = parser.parse(Path(f.name))

        assert len(result) == 1
        entry = result["test"]
        assert entry.author == "Smith, {John Q.}"
        assert entry.title == "A Book {With} Nested Braces"

    def test_parse_entry_with_multiline_values(self, parser: BibParser) -> None:
        """Test parsing entry with multiline field values."""
        bib_content = """
@book{multiline,
  author = {Author Name},
  title = {A Very Long Title
           That Spans Multiple Lines},
  year = {2023}
}
"""
        with NamedTemporaryFile(mode="w", suffix=".bib", delete=False) as f:
            f.write(bib_content)
            f.flush()
            result = parser.parse(Path(f.name))

        assert len(result) == 1
        entry = result["multiline"]
        # Whitespace should be normalized
        assert "That Spans Multiple Lines" in entry.title

    def test_parse_entry_with_tabs(self, parser: BibParser) -> None:
        """Test parsing entry with tab indentation (BibDesk style)."""
        bib_content = (
            "@misc{tabbed,\n\tauthor = {Author},\n\t"
            "title = {Title},\n\tyear = {2023}}"
        )
        with NamedTemporaryFile(mode="w", suffix=".bib", delete=False) as f:
            f.write(bib_content)
            f.flush()
            result = parser.parse(Path(f.name))

        assert len(result) == 1
        entry = result["tabbed"]
        assert entry.author == "Author"
        assert entry.title == "Title"

    def test_parse_ignores_unsupported_fields(self, parser: BibParser) -> None:
        """Test that unsupported fields are ignored without error."""
        bib_content = """
@book{test,
  author = {Author},
  title = {Title},
  year = {2023},
  keywords = {ignored},
  abstract = {Also ignored},
  bdsk-file-1 = {binary data}
}
"""
        with NamedTemporaryFile(mode="w", suffix=".bib", delete=False) as f:
            f.write(bib_content)
            f.flush()
            result = parser.parse(Path(f.name))

        assert len(result) == 1
        entry = result["test"]
        assert entry.author == "Author"
        assert entry.title == "Title"

    def test_parse_comments_ignored(self, parser: BibParser) -> None:
        """Test that BibTeX comments are ignored."""
        bib_content = """
%% This is a comment
%% Created by BibDesk

@book{test,
  author = {Author},
  title = {Title},
  year = {2023}
}
"""
        with NamedTemporaryFile(mode="w", suffix=".bib", delete=False) as f:
            f.write(bib_content)
            f.flush()
            result = parser.parse(Path(f.name))

        assert len(result) == 1
        assert "test" in result

    def test_parse_key_with_hyphen(self, parser: BibParser) -> None:
        """Test parsing entry with hyphenated key."""
        bib_content = """
@misc{simpson-notes-2025,
  author = {Simpson},
  title = {Notes},
  year = {2025}
}
"""
        with NamedTemporaryFile(mode="w", suffix=".bib", delete=False) as f:
            f.write(bib_content)
            f.flush()
            result = parser.parse(Path(f.name))

        assert "simpson-notes-2025" in result

    def test_parse_real_bib_file(self, parser: BibParser) -> None:
        """Test parsing a real .bib file from the examples."""
        bib_path = (
            Path(__file__).parent.parent
            / "examples"
            / "user_guide"
            / "references.bib"
        )
        if not bib_path.exists():
            pytest.skip("Example bib file not found")

        result = parser.parse(bib_path)
        assert len(result) > 0
        # Check for known entries in the example file
        assert "spivey92" in result

