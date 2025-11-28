"""Command-line interface for txt2tex."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

from txt2tex.errors import ErrorFormatter
from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer, LexerError
from txt2tex.parser import Parser, ParserError


def get_latex_dir() -> Path:
    """Get the path to bundled LaTeX files."""
    return Path(__file__).parent / "latex"


def compile_pdf(tex_path: Path, *, keep_aux: bool = False) -> bool:
    """Compile a .tex file to PDF using pdflatex.

    Args:
        tex_path: Path to the .tex file
        keep_aux: If True, keep auxiliary files (.aux, .log, etc.)

    Returns:
        True if compilation succeeded, False otherwise
    """
    latex_dir = get_latex_dir()
    work_dir = tex_path.parent

    # Find pdflatex executable
    pdflatex = shutil.which("pdflatex")
    if pdflatex is None:
        return False

    # Copy bundled .sty and .mf files to working directory
    copied_files: list[Path] = []
    for pattern in ("*.sty", "*.mf"):
        for src_file in latex_dir.glob(pattern):
            dest = work_dir / src_file.name
            if not dest.exists():
                shutil.copy(src_file, dest)
                copied_files.append(dest)

    try:
        # Run pdflatex (executable path verified by shutil.which above)
        result = subprocess.run(  # noqa: S603
            [
                pdflatex,
                "-interaction=nonstopmode",
                "-halt-on-error",
                tex_path.name,
            ],
            cwd=work_dir,
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            # Show relevant error from log
            log_file = tex_path.with_suffix(".log")
            if log_file.exists():
                log_content = log_file.read_text()
                # Find the first error line
                for line in log_content.split("\n"):
                    if line.startswith("!"):
                        print(f"LaTeX error: {line}", file=sys.stderr)
                        break
            else:
                print("pdflatex failed (check .log file)", file=sys.stderr)
            return False

        return True

    finally:
        # Clean up copied files
        for copied in copied_files:
            copied.unlink(missing_ok=True)

        # Clean up auxiliary files unless --keep-aux
        if not keep_aux:
            for ext in (".aux", ".log", ".out", ".toc"):
                aux_file = tex_path.with_suffix(ext)
                aux_file.unlink(missing_ok=True)


def main() -> int:
    """Main entry point for txt2tex CLI."""
    parser = argparse.ArgumentParser(
        description="Convert whiteboard notation to LaTeX",
        prog="txt2tex",
    )
    parser.add_argument(
        "input",
        type=Path,
        help="Input text file with whiteboard notation",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Output LaTeX file (default: input with .tex extension)",
    )
    parser.add_argument(
        "--zed",
        action="store_true",
        help="Use zed-* packages instead of fuzz package (fuzz is default)",
    )
    parser.add_argument(
        "--toc-parts",
        action="store_true",
        help="Include parts (a, b, c) in table of contents",
    )
    parser.add_argument(
        "--no-warn-overflow",
        action="store_true",
        help="Disable warnings for lines that may overflow page margins",
    )
    parser.add_argument(
        "--overflow-threshold",
        type=int,
        default=None,
        metavar="N",
        help="LaTeX character threshold for overflow warnings (default: 100)",
    )
    parser.add_argument(
        "--pdf",
        action="store_true",
        help="Compile to PDF using pdflatex (requires LaTeX installation)",
    )
    parser.add_argument(
        "--keep-aux",
        action="store_true",
        help="Keep auxiliary files (.aux, .log, etc.) after PDF compilation",
    )

    args = parser.parse_args()

    # Read input
    try:
        text = args.input.read_text()
    except FileNotFoundError:
        print(f"Error: Input file not found: {args.input}", file=sys.stderr)
        return 1
    except PermissionError:
        print(f"Error: Permission denied reading: {args.input}", file=sys.stderr)
        return 1
    except IsADirectoryError:
        print(f"Error: Expected a file, got a directory: {args.input}", file=sys.stderr)
        return 1
    except UnicodeDecodeError as e:
        print(f"Error: File encoding issue: {e}", file=sys.stderr)
        return 1

    # Process
    formatter = ErrorFormatter(text)
    try:
        lexer = Lexer(text)
        tokens = lexer.tokenize()

        parser_obj = Parser(tokens)
        ast = parser_obj.parse()

        generator = LaTeXGenerator(
            use_fuzz=not args.zed,
            toc_parts=args.toc_parts,
            warn_overflow=not args.no_warn_overflow,
            overflow_threshold=args.overflow_threshold,
        )
        latex = generator.generate_document(ast)
    except LexerError as e:
        formatted = formatter.format_error(e.message, e.line, e.column)
        print(formatted, file=sys.stderr)
        return 1
    except ParserError as e:
        formatted = formatter.format_error(e.message, e.token.line, e.token.column)
        print(formatted, file=sys.stderr)
        return 1

    # Emit any overflow warnings
    generator.emit_warnings()

    # Write output
    output_path = args.output or args.input.with_suffix(".tex")
    try:
        output_path.write_text(latex)
        print(f"Generated: {output_path}")
    except PermissionError:
        print(f"Error: Permission denied writing: {output_path}", file=sys.stderr)
        return 1
    except IsADirectoryError:
        print(f"Error: Cannot write to directory: {output_path}", file=sys.stderr)
        return 1
    except OSError as e:
        print(f"Error writing output file: {e}", file=sys.stderr)
        return 1

    # Compile to PDF if requested
    if args.pdf:
        if shutil.which("pdflatex") is None:
            print(
                "Error: pdflatex not found. Install a LaTeX distribution.",
                file=sys.stderr,
            )
            return 1

        print(f"Compiling: {output_path.with_suffix('.pdf')}")
        if not compile_pdf(output_path, keep_aux=args.keep_aux):
            return 1
        print(f"Generated: {output_path.with_suffix('.pdf')}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
