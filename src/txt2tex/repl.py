"""Interactive REPL for txt2tex."""

from __future__ import annotations

import contextlib
import os
import platform
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from txt2tex.ast_nodes import Document
from txt2tex.compile import compile_pdf, copy_latex_files
from txt2tex.errors import ErrorFormatter
from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer, LexerError
from txt2tex.parser import Parser, ParserError

# Import readline for history/editing if available (side effect: enables line editing)
with contextlib.suppress(ImportError):
    import readline  # noqa: F401  # pyright: ignore[reportUnusedImport]

# Block keywords that indicate multi-line input (case-insensitive for some)
BLOCK_KEYWORDS: set[str] = {
    "PROOF:",
    "ARGUE:",
    "EQUIV:",
    "TRUTH TABLE:",
    "TEXT:",
    "PURETEXT:",
    "LATEX:",
    "INFRULE:",
    "SYNTAX:",
}

# Keywords that start a block (case-sensitive, at start of line)
BLOCK_START_WORDS: set[str] = {
    "schema",
    "axdef",
    "gendef",
    "given",
    "zed",
    "syntax",
}


def is_block_input(text: str) -> bool:
    """Check if input starts a multi-line block.

    Args:
        text: The input text to check.

    Returns:
        True if this starts a block that needs multi-line input.
    """
    stripped = text.strip()
    upper = stripped.upper()

    # Check for uppercase block keywords
    for keyword in BLOCK_KEYWORDS:
        if upper.startswith(keyword):
            return True

    # Check for block start words (first word)
    first_word = stripped.split()[0] if stripped else ""
    return first_word in BLOCK_START_WORDS


def open_pdf(pdf_path: Path) -> bool:
    """Open a PDF file with the system viewer.

    Args:
        pdf_path: Path to the PDF file.

    Returns:
        True if open command succeeded.
    """
    system = platform.system()

    if system == "Darwin":  # macOS
        cmd = ["open", str(pdf_path)]
    elif system == "Linux":
        cmd = ["xdg-open", str(pdf_path)]
    elif system == "Windows":
        cmd = ["start", "", str(pdf_path)]
    else:
        print(f"Unknown platform: {system}", file=sys.stderr)
        return False

    try:
        subprocess.run(cmd, check=False, capture_output=True)  # noqa: S603
        return True
    except FileNotFoundError:
        print("Could not open PDF viewer", file=sys.stderr)
        return False


def generate_preview_document(latex_fragment: str, *, use_fuzz: bool) -> str:
    """Wrap a LaTeX fragment in a minimal document for preview.

    Args:
        latex_fragment: The LaTeX code to wrap.
        use_fuzz: Whether to use fuzz package (vs zed-* packages).

    Returns:
        Complete LaTeX document source.
    """
    lines: list[str] = []
    lines.append(r"\documentclass[a4paper,10pt,fleqn]{article}")
    lines.append(r"\usepackage[margin=1in]{geometry}")
    lines.append(r"\usepackage{amssymb}")
    lines.append(r"\usepackage{adjustbox}")

    if use_fuzz:
        lines.append(r"\usepackage{fuzz}")
    else:
        lines.append(r"\usepackage{zed-cm}")

    lines.append(r"\usepackage{zed-maths}")
    lines.append(r"\usepackage{zed-proof}")
    lines.append(r"\newdimen\savedleftskip")
    lines.append(r"\begin{document}")
    lines.append("")
    lines.append(latex_fragment)
    lines.append("")
    lines.append(r"\end{document}")

    return "\n".join(lines)


def process_input(
    text: str,
    generator: LaTeXGenerator,
    *,
    latex_only: bool = False,
    temp_dir: Path | None = None,
) -> bool:
    """Process input text and generate output.

    Args:
        text: The input text to process.
        generator: LaTeX generator instance.
        latex_only: If True, only show LaTeX (no PDF).
        temp_dir: Temp directory for PDF generation.

    Returns:
        True if processing succeeded.
    """
    formatter = ErrorFormatter(text)

    try:
        lexer = Lexer(text)
        tokens = lexer.tokenize()

        parser_obj = Parser(tokens)
        ast = parser_obj.parse()

        # Generate LaTeX for the content (not full document)
        # Parser always returns Document for full text input
        if not isinstance(ast, Document):
            # Single expression - wrap in display math
            latex_fragment = f"${generator.generate_expr(ast)}$"
        else:
            latex_fragment = generator.generate_fragment(ast)

    except LexerError as e:
        formatted = formatter.format_error(e.message, e.line, e.column)
        print(formatted, file=sys.stderr)
        return False
    except ParserError as e:
        formatted = formatter.format_error(e.message, e.token.line, e.token.column)
        print(formatted, file=sys.stderr)
        return False

    # Show LaTeX
    print("\nLaTeX:")
    print(latex_fragment)

    if latex_only or temp_dir is None:
        return True

    # Generate full document and compile to PDF
    print("\nGenerating PDF...", end=" ", flush=True)
    full_doc = generate_preview_document(latex_fragment, use_fuzz=generator.use_fuzz)

    tex_path = temp_dir / "preview.tex"
    tex_path.write_text(full_doc)

    # Copy required style files
    copy_latex_files(temp_dir)

    # Compile
    if compile_pdf(tex_path, keep_aux=False):
        pdf_path = tex_path.with_suffix(".pdf")
        if pdf_path.exists():
            print("done.")
            open_pdf(pdf_path)
            return True
        print("failed (PDF not generated).", file=sys.stderr)
        return False
    print("failed.", file=sys.stderr)
    return False


def print_help() -> None:
    """Print REPL help message."""
    print(
        """
txt2tex interactive mode commands:
  .help     - Show this help message
  .latex    - Toggle LaTeX-only mode (no PDF preview)
  .clear    - Clear the screen
  .quit     - Exit the REPL
  .exit     - Exit the REPL

Input:
  - Single-line expressions are processed immediately
  - Multi-line blocks (PROOF:, schema, etc.) accumulate until blank line
  - Press Enter twice to execute multi-line input
"""
    )


def repl_main(*, use_fuzz: bool = True) -> int:
    """Run the interactive REPL.

    Args:
        use_fuzz: Whether to use fuzz package (default) or zed-* packages.

    Returns:
        Exit code (0 for success).
    """
    # readline imported at module level with contextlib.suppress

    print("txt2tex interactive mode. Type .help for commands.")
    print("")

    generator = LaTeXGenerator(use_fuzz=use_fuzz)
    latex_only = False

    # Create persistent temp directory for PDF preview
    temp_dir = Path(tempfile.mkdtemp(prefix="txt2tex_"))

    try:
        while True:
            try:
                # Read input
                try:
                    line = input(">>> ")
                except EOFError:
                    print("")
                    break

                stripped = line.strip()

                # Handle commands
                if stripped == ".help":
                    print_help()
                    continue
                if stripped == ".quit" or stripped == ".exit":
                    break
                if stripped == ".clear":
                    os.system("clear" if platform.system() != "Windows" else "cls")  # noqa: S605
                    continue
                if stripped == ".latex":
                    latex_only = not latex_only
                    mode = "ON" if latex_only else "OFF"
                    print(f"LaTeX-only mode: {mode}")
                    continue
                if stripped.startswith("."):
                    print(f"Unknown command: {stripped}")
                    continue

                # Skip empty input
                if not stripped:
                    continue

                # Check if this is a multi-line block
                if is_block_input(line):
                    # Accumulate lines until blank line
                    lines = [line]
                    while True:
                        try:
                            continuation = input("... ")
                        except EOFError:
                            break

                        if continuation.strip() == "":
                            break
                        lines.append(continuation)

                    text = "\n".join(lines)
                else:
                    text = line

                # Process the input
                process_input(
                    text,
                    generator,
                    latex_only=latex_only,
                    temp_dir=temp_dir if not latex_only else None,
                )

            except KeyboardInterrupt:
                print("\n(Use .quit to exit)")
                continue

    finally:
        # Clean up temp directory
        shutil.rmtree(temp_dir, ignore_errors=True)

    print("Goodbye!")
    return 0
