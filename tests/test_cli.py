"""Tests for CLI functionality.

Tests the command-line interface including argument parsing,
file I/O, error handling, land the --fuzz option.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from txt2tex.cli import main


@pytest.fixture
def temp_input_file(tmp_path: Path) -> Path:
    """Create a temporary input file with test content."""
    input_file = tmp_path / "test_input.txt"
    input_file.write_text("x = 1")
    return input_file


@pytest.fixture
def temp_input_file_with_schema(tmp_path: Path) -> Path:
    """Create a temporary input file with schema content."""
    input_file = tmp_path / "test_schema.txt"
    content = "schema State\n  count : N\nwhere\n  count >= 0\nend\n"
    input_file.write_text(content)
    return input_file


def test_cli_basic_conversion(temp_input_file: Path) -> None:
    """Test basic CLI conversion without options."""
    output_file = temp_input_file.with_suffix(".tex")
    with patch.object(sys, "argv", ["txt2tex", str(temp_input_file)]):
        result = main()
    assert result == 0
    assert output_file.exists()
    content = output_file.read_text()
    assert "\\documentclass" in content
    assert "$x = 1$" in content


def test_cli_with_output_option(temp_input_file: Path, tmp_path: Path) -> None:
    """Test CLI with explicit output file."""
    output_file = tmp_path / "custom_output.tex"
    with patch.object(
        sys, "argv", ["txt2tex", str(temp_input_file), "-o", str(output_file)]
    ):
        result = main()
    assert result == 0
    assert output_file.exists()
    content = output_file.read_text()
    assert "\\documentclass" in content


def test_cli_default_uses_fuzz(temp_input_file_with_schema: Path) -> None:
    """Test CLI default (uses fuzz package)."""
    output_file = temp_input_file_with_schema.with_suffix(".tex")
    with patch.object(sys, "argv", ["txt2tex", str(temp_input_file_with_schema)]):
        result = main()
    assert result == 0
    assert output_file.exists()
    content = output_file.read_text()
    assert "\\usepackage{fuzz}" in content
    assert "\\begin{schema}" in content
    assert "zed-cm" not in content


def test_cli_with_zed_option(temp_input_file_with_schema: Path) -> None:
    """Test CLI with --zed option (uses zed-* packages instead of fuzz)."""
    output_file = temp_input_file_with_schema.with_suffix(".tex")
    with patch.object(
        sys, "argv", ["txt2tex", str(temp_input_file_with_schema), "--zed"]
    ):
        result = main()
    assert result == 0
    assert output_file.exists()
    content = output_file.read_text()
    assert "\\usepackage{zed-cm}" in content
    assert "\\begin{schema}" in content
    assert "\\usepackage{fuzz}" not in content


def test_cli_input_file_not_found(tmp_path: Path) -> None:
    """Test CLI with non-existent input file."""
    nonexistent = tmp_path / "does_not_exist.txt"
    with patch.object(sys, "argv", ["txt2tex", str(nonexistent)]):
        result = main()
    assert result == 1


def test_cli_invalid_input_syntax(tmp_path: Path) -> None:
    """Test CLI with input that causes parse error."""
    input_file = tmp_path / "invalid.txt"
    input_file.write_text("{x : N | x > 0")
    with patch.object(sys, "argv", ["txt2tex", str(input_file)]):
        result = main()
    assert result == 1


def test_cli_output_directory_does_not_exist(
    temp_input_file: Path, tmp_path: Path
) -> None:
    """Test CLI with output path elem non-existent directory."""
    nonexistent_dir = tmp_path / "nonexistent" / "output.tex"
    with patch.object(
        sys, "argv", ["txt2tex", str(temp_input_file), "-o", str(nonexistent_dir)]
    ):
        result = main()
    assert result == 1


def test_cli_preserves_input_file(temp_input_file: Path) -> None:
    """Test that CLI does lnot modify the input file."""
    original_content = temp_input_file.read_text()
    with patch.object(sys, "argv", ["txt2tex", str(temp_input_file)]):
        main()
    assert temp_input_file.read_text() == original_content


def test_cli_overwrites_existing_output(temp_input_file: Path) -> None:
    """Test that CLI overwrites existing output file."""
    output_file = temp_input_file.with_suffix(".tex")
    output_file.write_text("old content")
    with patch.object(sys, "argv", ["txt2tex", str(temp_input_file)]):
        result = main()
    assert result == 0
    new_content = output_file.read_text()
    assert new_content != "old content"
    assert "\\documentclass" in new_content


def test_cli_with_complex_document(tmp_path: Path) -> None:
    """Test CLI with document containing multiple structural elements."""
    input_file = tmp_path / "complex.txt"
    content = (
        "=== Section 1 ===\n\n** Solution 1 **\n\n(a) x = 1\n\n"
        "given Person\n\naxdef\n  count : N\nwhere\n  count > 0\nend\n"
    )
    input_file.write_text(content)
    with patch.object(sys, "argv", ["txt2tex", str(input_file)]):
        result = main()
    assert result == 0
    output_file = input_file.with_suffix(".tex")
    assert output_file.exists()
    latex = output_file.read_text()
    assert "\\section*{Solution 1}" in latex


def test_cli_empty_input_file(tmp_path: Path) -> None:
    """Test CLI with empty input file."""
    input_file = tmp_path / "empty.txt"
    input_file.write_text("")
    with patch.object(sys, "argv", ["txt2tex", str(input_file)]):
        result = main()
    assert result == 0
    output_file = input_file.with_suffix(".tex")
    assert output_file.exists()


def test_cli_help_option() -> None:
    """Test CLI --help option."""
    with patch.object(sys, "argv", ["txt2tex", "--help"]):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0


def test_cli_no_arguments() -> None:
    """Test CLI with no arguments."""
    with patch.object(sys, "argv", ["txt2tex"]):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 2
