"""PDF compilation utilities for txt2tex."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


def get_latex_dir() -> Path:
    """Get the path to bundled LaTeX files."""
    return Path(__file__).parent / "latex"


def format_tex(tex_path: Path) -> bool:
    """Format a .tex file with tex-fmt if available.

    Args:
        tex_path: Path to the .tex file

    Returns:
        True if formatting was applied, False if tex-fmt not available
    """
    tex_fmt = shutil.which("tex-fmt")
    if tex_fmt is None:
        print("Note: tex-fmt not found. Skipping formatting.")
        return False

    result = subprocess.run(  # noqa: S603
        [tex_fmt, str(tex_path)],
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode == 0:
        print("Formatted: tex-fmt applied")
        return True

    # tex-fmt failed - not critical, just note it
    print("Note: tex-fmt formatting failed (continuing anyway)")
    return False


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
            "-gg",  # Force complete rebuild for consistent bibliography generation
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
