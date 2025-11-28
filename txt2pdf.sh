#!/usr/bin/env bash
#
# txt2pdf.sh - Convert whiteboard notation to PDF with advanced features
#
# This script wraps the txt2tex CLI and adds:
# - latexmk for robust compilation (handles bibliographies, multiple passes)
# - tex-fmt for LaTeX formatting (if available)
# - fuzz type checking (if --typecheck specified)
#
# For simple conversions, use the CLI directly: txt2tex input.txt
#
# Usage: ./txt2pdf.sh input.txt [--zed] [--typecheck]
#

set -e

# Check arguments
if [ $# -lt 1 ]; then
    echo "Usage: $0 input.txt [--zed] [--typecheck]" >&2
    echo "" >&2
    echo "Options:" >&2
    echo "  --zed         Use zed-* packages instead of fuzz (default: fuzz)" >&2
    echo "  --typecheck   Run fuzz type checker before compilation" >&2
    echo "" >&2
    echo "For simple conversions, use: txt2tex input.txt" >&2
    exit 1
fi

INPUT="$1"
ZED_FLAG=""
TYPECHECK=""

# Parse flags
for arg in "$@"; do
    case "$arg" in
        --zed) ZED_FLAG="--zed" ;;
        --typecheck) TYPECHECK="1" ;;
    esac
done

# Validate input file exists
if [ ! -f "$INPUT" ]; then
    echo "Error: Input file not found: $INPUT" >&2
    exit 1
fi

# Get absolute paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INPUT="$(cd "$(dirname "$INPUT")" && pwd)/$(basename "$INPUT")"
INPUT_DIR="$(dirname "$INPUT")"
INPUT_BASE="$(basename "$INPUT" .txt)"
TEX_FILE="${INPUT_DIR}/${INPUT_BASE}.tex"
PDF_FILE="${INPUT_DIR}/${INPUT_BASE}.pdf"

echo "Converting: $INPUT"

# Step 1: Generate LaTeX using CLI
echo "Generating LaTeX..."
(cd "$SCRIPT_DIR" && PYTHONPATH="${SCRIPT_DIR}/src" python -m txt2tex.cli "$INPUT" -o "$TEX_FILE" --tex-only $ZED_FLAG)

# Step 2: Format with tex-fmt (if available)
if command -v tex-fmt > /dev/null 2>&1; then
    echo "Formatting LaTeX..."
    cd "$INPUT_DIR" && tex-fmt "${INPUT_BASE}.tex" 2>&1 || true
fi

# Step 3: Type check with fuzz (if requested)
if [ -n "$TYPECHECK" ]; then
    echo "Type checking with fuzz..."
    if ! command -v fuzz > /dev/null 2>&1; then
        echo "Error: fuzz command not found" >&2
        exit 1
    fi
    cd "$INPUT_DIR" && fuzz "${INPUT_BASE}.tex" || exit 1
fi

# Step 4: Copy LaTeX dependencies
cp "${SCRIPT_DIR}/src/txt2tex/latex"/*.sty "$INPUT_DIR/" 2>/dev/null || true
cp "${SCRIPT_DIR}/src/txt2tex/latex"/*.mf "$INPUT_DIR/" 2>/dev/null || true

# Step 5: Compile with latexmk (handles bibliographies automatically)
echo "Compiling PDF..."
BIBTEX_FLAG="-bibtex-"
if grep -q "\\\\bibliography{" "$TEX_FILE" 2>/dev/null; then
    BIBTEX_FLAG=""
fi

cd "$INPUT_DIR" && latexmk -pdf -gg $BIBTEX_FLAG -interaction=nonstopmode -quiet "${INPUT_BASE}.tex"

# Clean up
cd "$INPUT_DIR" && latexmk -c "${INPUT_BASE}.tex" > /dev/null 2>&1 || true

echo "Generated: $PDF_FILE"
