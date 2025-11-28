"""Command-line interface for txt2tex."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from txt2tex.errors import ErrorFormatter
from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer, LexerError
from txt2tex.parser import Parser, ParserError


def get_latex_dir() -> Path:
    """Get the path to bundled LaTeX files."""
    return Path(__file__).parent / "latex"


def copy_latex_files(work_dir: Path) -> list[Path]:
    """Copy bundled .sty and .mf files to working directory.

    Returns:
        List of copied file paths (for cleanup)
    """
    latex_dir = get_latex_dir()
    copied_files: list[Path] = []
    for pattern in ("*.sty", "*.mf"):
        for src_file in latex_dir.glob(pattern):
            dest = work_dir / src_file.name
            if not dest.exists():
                shutil.copy(src_file, dest)
                copied_files.append(dest)
    return copied_files


def typecheck_fuzz(tex_path: Path) -> bool:
    """Run fuzz typechecker on a .tex file.

    Args:
        tex_path: Path to the .tex file

    Returns:
        True if typechecking passed, False otherwise
    """
    fuzz = shutil.which("fuzz")
    if fuzz is None:
        return True  # Skip if not available

    work_dir = tex_path.parent

    # Copy .sty files for fuzz
    copied_files = copy_latex_files(work_dir)

    try:
        result = subprocess.run(  # noqa: S603
            [fuzz, tex_path.name],
            cwd=work_dir,
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            print("Type checking failed:", file=sys.stderr)
            # Show fuzz output (it contains the errors)
            if result.stdout:
                print(result.stdout, file=sys.stderr)
            if result.stderr:
                print(result.stderr, file=sys.stderr)
            return False

        print("Type checking: passed")
        return True

    finally:
        # Clean up copied files
        for copied in copied_files:
            copied.unlink(missing_ok=True)


def compile_pdf(tex_path: Path, *, keep_aux: bool = False) -> bool:
    """Compile a .tex file to PDF using latexmk or pdflatex.

    Uses latexmk if available (handles bibliography and multiple passes).
    Falls back to multiple pdflatex passes for TOC/references.

    Args:
        tex_path: Path to the .tex file
        keep_aux: If True, keep auxiliary files (.aux, .log, etc.)

    Returns:
        True if compilation succeeded, False otherwise
    """
    work_dir = tex_path.parent

    # Copy bundled .sty and .mf files to working directory
    copied_files = copy_latex_files(work_dir)

    # Check for bibliography in the .tex file
    tex_content = tex_path.read_text()
    has_bibliography = "\\bibliography{" in tex_content

    try:
        # Prefer latexmk if available (handles everything automatically)
        latexmk = shutil.which("latexmk")
        if latexmk is not None:
            return _compile_with_latexmk(
                latexmk,
                tex_path,
                work_dir,
                has_bibliography=has_bibliography,
                keep_aux=keep_aux,
            )

        # Fall back to pdflatex
        pdflatex = shutil.which("pdflatex")
        if pdflatex is None:
            return False

        return _compile_with_pdflatex(
            pdflatex,
            tex_path,
            work_dir,
            has_bibliography=has_bibliography,
            keep_aux=keep_aux,
        )

    finally:
        # Clean up copied .sty/.mf files
        for copied in copied_files:
            copied.unlink(missing_ok=True)


def _compile_with_latexmk(
    latexmk: str,
    tex_path: Path,
    work_dir: Path,
    *,
    has_bibliography: bool,
    keep_aux: bool,
) -> bool:
    """Compile using latexmk (handles multiple passes automatically)."""
    # latexmk -pdf handles pdflatex + bibtex + multiple passes
    bibtex_flag = [] if has_bibliography else ["-bibtex-"]

    result = subprocess.run(  # noqa: S603
        [
            latexmk,
            "-pdf",
            "-interaction=nonstopmode",
            *bibtex_flag,
            tex_path.name,
        ],
        cwd=work_dir,
        capture_output=True,
        text=True,
        check=False,
    )

    pdf_path = tex_path.with_suffix(".pdf")

    # Check for actual LaTeX errors (not just "no pages" warning)
    if result.returncode != 0:
        if _has_latex_error(tex_path):
            _show_latex_error(tex_path)
            return False
        # No real error - might be empty document with "No pages of output"
        # Check if PDF exists (even if empty)
        if not pdf_path.exists():
            _show_latex_error(tex_path)
            return False

    # Clean up with latexmk -c unless --keep-aux
    if not keep_aux:
        subprocess.run(  # noqa: S603
            [latexmk, "-c", tex_path.name],
            cwd=work_dir,
            capture_output=True,
            check=False,
        )

    return True


def _has_latex_error(tex_path: Path) -> bool:
    """Check if the LaTeX log contains actual errors."""
    log_file = tex_path.with_suffix(".log")
    if not log_file.exists():
        return False
    try:
        log_content = log_file.read_text(errors="replace")
    except OSError:
        return False
    return any(line.startswith("!") for line in log_content.split("\n"))


def _compile_with_pdflatex(
    pdflatex: str,
    tex_path: Path,
    work_dir: Path,
    *,
    has_bibliography: bool,
    keep_aux: bool,
) -> bool:
    """Compile using pdflatex with multiple passes for TOC/bibliography."""
    tex_name = tex_path.name
    base_name = tex_path.stem

    def run_pdflatex() -> subprocess.CompletedProcess[str]:
        return subprocess.run(  # noqa: S603
            [pdflatex, "-interaction=nonstopmode", "-halt-on-error", tex_name],
            cwd=work_dir,
            capture_output=True,
            text=True,
            check=False,
        )

    # First pass
    result = run_pdflatex()
    if result.returncode != 0:
        _show_latex_error(tex_path)
        return False

    # Run bibtex if bibliography present
    if has_bibliography:
        bibtex = shutil.which("bibtex")
        if bibtex is not None:
            subprocess.run(  # noqa: S603
                [bibtex, base_name],
                cwd=work_dir,
                capture_output=True,
                check=False,
            )
            # Two more passes after bibtex
            run_pdflatex()
            run_pdflatex()
    else:
        # Second pass for TOC and references
        run_pdflatex()

    # Clean up auxiliary files unless --keep-aux
    if not keep_aux:
        for ext in (".aux", ".log", ".out", ".toc", ".bbl", ".blg"):
            aux_file = tex_path.with_suffix(ext)
            aux_file.unlink(missing_ok=True)

    return True


def _show_latex_error(tex_path: Path) -> None:
    """Show relevant error from LaTeX log file."""
    log_file = tex_path.with_suffix(".log")
    if log_file.exists():
        try:
            log_content = log_file.read_text(errors="replace")
        except OSError:
            print("LaTeX compilation failed (cannot read .log file)", file=sys.stderr)
            return
        for line in log_content.split("\n"):
            if line.startswith("!"):
                print(f"LaTeX error: {line}", file=sys.stderr)
                break
    else:
        print("LaTeX compilation failed (check .log file)", file=sys.stderr)


def _check_latex_package(pdflatex: str, package: str) -> bool:
    """Check if a LaTeX package is available."""
    test_doc = (
        f"\\documentclass{{article}}\n"
        f"\\usepackage{{{package}}}\n"
        f"\\begin{{document}}\ntest\n\\end{{document}}\n"
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        tex_file = Path(tmpdir) / "test.tex"
        tex_file.write_text(test_doc)

        result = subprocess.run(  # noqa: S603
            [pdflatex, "-interaction=batchmode", "-halt-on-error", "test.tex"],
            cwd=tmpdir,
            capture_output=True,
            check=False,
        )
        return result.returncode == 0


def check_environment() -> int:
    """Check for required and optional dependencies."""
    print("txt2tex environment check")
    print("=" * 40)

    all_ok = True

    # Check pdflatex (required for PDF)
    pdflatex = shutil.which("pdflatex")
    if pdflatex:
        print(f"✓ pdflatex: {pdflatex}")
    else:
        print("✗ pdflatex: NOT FOUND (required for PDF generation)")
        all_ok = False

    # Check required LaTeX packages (only if pdflatex found)
    if pdflatex:
        required_packages = ["adjustbox", "natbib", "geometry", "amsfonts", "hyperref"]
        print("\nLaTeX packages:")
        for pkg in required_packages:
            if _check_latex_package(pdflatex, pkg):
                print(f"  ✓ {pkg}")
            else:
                print(f"  ✗ {pkg}: NOT FOUND")
                all_ok = False

    # Check latexmk (optional, but recommended)
    print("\nOptional tools:")
    latexmk = shutil.which("latexmk")
    if latexmk:
        print(f"  ✓ latexmk: {latexmk}")
    else:
        print("  ○ latexmk: not found (recommended for bibliography)")

    # Check bibtex (optional)
    bibtex = shutil.which("bibtex")
    if bibtex:
        print(f"  ✓ bibtex: {bibtex}")
    else:
        print("  ○ bibtex: not found (for bibliography)")

    # Check fuzz (optional)
    fuzz = shutil.which("fuzz")
    if fuzz:
        print(f"  ✓ fuzz: {fuzz}")
    else:
        print("  ○ fuzz: not found (for Z notation type checking)")

    print("\n" + "=" * 40)
    if all_ok:
        print("Environment OK - ready for PDF generation")
        return 0

    print("Missing required dependencies - use --tex-only or install LaTeX")
    print("On Ubuntu/Debian: sudo apt install texlive-latex-extra")
    print("On macOS: Install MacTeX from https://www.tug.org/mactex/")
    return 1


def main() -> int:
    """Main entry point for txt2tex CLI."""
    parser = argparse.ArgumentParser(
        description="Convert whiteboard notation to LaTeX",
        prog="txt2tex",
    )
    parser.add_argument(
        "input",
        type=Path,
        nargs="?",
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
        "--tex-only",
        action="store_true",
        help="Generate LaTeX only, do not compile to PDF",
    )
    parser.add_argument(
        "--keep-aux",
        action="store_true",
        help="Keep auxiliary files (.aux, .log, etc.) after PDF compilation",
    )
    parser.add_argument(
        "--check-env",
        action="store_true",
        help="Check for required dependencies (LaTeX, fuzz) and exit",
    )

    args = parser.parse_args()

    # Handle --check-env
    if args.check_env:
        return check_environment()

    # Require input file for normal operation
    if args.input is None:
        parser.error("the following arguments are required: input")

    # Check for pdflatex early unless --tex-only
    if not args.tex_only and shutil.which("pdflatex") is None:
        print(
            "Error: pdflatex not found. Install a LaTeX distribution "
            "(e.g., TeX Live, MacTeX, MiKTeX), or use --tex-only.",
            file=sys.stderr,
        )
        return 1

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

    # Type check with fuzz (if available and using fuzz package)
    if not args.zed:
        if shutil.which("fuzz") is not None:
            if not typecheck_fuzz(output_path):
                return 1
        else:
            print(
                "Note: fuzz typechecker not found. Skipping type checking.",
                file=sys.stderr,
            )
            print(
                "      Install from: https://github.com/jmf-pobox/fuzz",
                file=sys.stderr,
            )

    # Compile to PDF unless --tex-only
    if not args.tex_only:
        print(f"Compiling: {output_path.with_suffix('.pdf')}")
        if not compile_pdf(output_path, keep_aux=args.keep_aux):
            return 1
        print(f"Generated: {output_path.with_suffix('.pdf')}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
