"""Tests for error formatting module."""

from __future__ import annotations

import re

from txt2tex.errors import ERROR_HINTS, ErrorFormatter
from txt2tex.lexer import Lexer, LexerError
from txt2tex.parser import Parser, ParserError


class TestErrorFormatter:
    """Tests for ErrorFormatter class."""

    def test_format_error_basic(self) -> None:
        """Test basic error formatting with context."""
        source = "line 1\nline 2\nline 3\nline 4\nline 5"
        formatter = ErrorFormatter(source)

        result = formatter.format_error("Test error", line=3, column=5)

        assert "Error: Test error" in result
        assert "line 2" in result  # Context before
        assert "line 3" in result  # Error line
        assert "line 4" in result  # Context after
        assert "^" in result  # Caret

    def test_format_error_first_line(self) -> None:
        """Test error on first line (no context before)."""
        source = "first\nsecond\nthird"
        formatter = ErrorFormatter(source)

        result = formatter.format_error("Error at start", line=1, column=1)

        assert "first" in result
        assert "second" in result  # Context after
        assert "^" in result

    def test_format_error_last_line(self) -> None:
        """Test error on last line (no context after)."""
        source = "first\nsecond\nthird"
        formatter = ErrorFormatter(source)

        result = formatter.format_error("Error at end", line=3, column=1)

        assert "second" in result  # Context before
        assert "third" in result
        assert "^" in result

    def test_caret_position(self) -> None:
        """Test caret is positioned at correct column."""
        source = "hello world"
        formatter = ErrorFormatter(source)

        result = formatter.format_error("Error here", line=1, column=7)

        lines = result.split("\n")
        # Find the source line and caret line
        source_line = next(line for line in lines if "hello world" in line)
        caret_line = next(line for line in lines if "^" in line and "|" in line)

        # The caret should be under the 'w' in 'world' (column 7)
        # Find position of 'w' in source line and '^' in caret line
        source_w_pos = source_line.index("w")
        caret_pos = caret_line.index("^")
        assert source_w_pos == caret_pos

    def test_line_numbers_aligned(self) -> None:
        """Test line numbers are right-aligned."""
        source = "\n".join(f"line {i}" for i in range(1, 12))
        formatter = ErrorFormatter(source)

        result = formatter.format_error("Error", line=10, column=1)

        # Line 10 should have aligned numbers
        assert " 9 |" in result or "9 |" in result
        assert "10 |" in result
        assert "11 |" in result


class TestHintMatching:
    """Tests for hint pattern matching."""

    def test_hint_expected_end(self) -> None:
        """Test hint for missing 'end' keyword."""
        source = "test"
        formatter = ErrorFormatter(source)

        result = formatter.format_error(
            "Expected 'end' to close schema", line=1, column=1
        )

        assert "Hint:" in result
        assert "forget 'end'" in result

    def test_hint_section_marker(self) -> None:
        """Test hint for unclosed section marker."""
        source = "test"
        formatter = ErrorFormatter(source)

        result = formatter.format_error(
            "Expected closing '===' for section", line=1, column=1
        )

        assert "Hint:" in result
        assert "=== Title ===" in result

    def test_hint_unexpected_token(self) -> None:
        """Test hint for unexpected token."""
        source = "test"
        formatter = ErrorFormatter(source)

        result = formatter.format_error(
            "Unexpected token after expression", line=1, column=1
        )

        assert "Hint:" in result
        assert "missing operators" in result

    def test_no_hint_for_unknown_error(self) -> None:
        """Test no hint is added for unrecognized errors."""
        source = "test"
        formatter = ErrorFormatter(source)

        result = formatter.format_error("Some random error message", line=1, column=1)

        assert "Hint:" not in result

    def test_all_hints_have_patterns(self) -> None:
        """Verify all hint patterns are valid regex."""
        for pattern in ERROR_HINTS:
            # Should not raise
            re.compile(pattern)


class TestIntegration:
    """Integration tests for error formatting in CLI context."""

    def test_lexer_error_formatting(self) -> None:
        """Test formatting of lexer errors."""
        source = "test >^< error"
        try:
            lexer = Lexer(source)
            lexer.tokenize()
        except LexerError as e:
            formatter = ErrorFormatter(source)
            result = formatter.format_error(e.message, e.line, e.column)
            assert "Error:" in result
            assert "^" in result

    def test_parser_error_formatting(self) -> None:
        """Test formatting of parser errors."""
        source = "=== Test\nsome text"  # Missing closing ===
        try:
            lexer = Lexer(source)
            tokens = lexer.tokenize()
            parser = Parser(tokens)
            parser.parse()
        except ParserError as e:
            formatter = ErrorFormatter(source)
            result = formatter.format_error(e.message, e.token.line, e.token.column)
            assert "Error:" in result
            assert "^" in result
