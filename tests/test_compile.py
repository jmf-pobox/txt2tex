"""Tests for PDF compilation utilities."""

from __future__ import annotations

import stat
from pathlib import Path
from unittest.mock import patch

from txt2tex.compile import compile_pdf


def test_compile_pdf_non_utf8_stdout(tmp_path: Path) -> None:
    """compile_pdf returns True when latexmk emits non-UTF-8 bytes to stdout.

    Before the fix, subprocess.run with text=True decodes stdout as strict
    UTF-8, raising UnicodeDecodeError on byte 0xa7.  After the fix,
    errors="replace" is passed so the byte is replaced with the Unicode
    replacement character and the call succeeds.
    """
    # Stub executable: writes a raw latin-1 byte (0xa7, §) and exits 0.
    # This simulates latexmk echoing the source file's non-UTF-8 content.
    stub = tmp_path / "latexmk"
    # Emit a raw 0xa7 (§, latin-1) byte. Use a POSIX octal escape (\247) —
    # printf's \xHH hex escape is not portable (dash's printf lacks it),
    # whereas \ddd octal is required by POSIX and works in every /bin/sh.
    stub.write_text("#!/bin/sh\nprintf '\\247\\n'\nexit 0\n")
    stub.chmod(stub.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

    # Minimal .tex file — content doesn't matter; the stub exits 0.
    tex = tmp_path / "doc.tex"
    tex.write_text("\\documentclass{article}\n\\begin{document}hello\\end{document}\n")

    def fake_which(name: str) -> str | None:
        return str(stub) if name == "latexmk" else None

    # keep_aux=True skips the cleanup subprocess.run so only the one
    # text=True call (the main latexmk invocation) is exercised.
    with patch("txt2tex.compile.shutil.which", side_effect=fake_which):
        result = compile_pdf(tex, keep_aux=True)

    assert result is True
