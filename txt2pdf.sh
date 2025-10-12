#!/usr/bin/env bash
#
# txt2pdf.sh - Convert whiteboard notation to PDF
#
# Usage: ./txt2pdf.sh input.txt [--fuzz]
#

set -e  # Exit on error (disabled for pdflatex step)

# Check arguments
if [ $# -lt 1 ]; then
    echo "Usage: $0 input.txt [--fuzz]" >&2
    echo "" >&2
    echo "Options:" >&2
    echo "  --fuzz    Use fuzz package instead of zed-*" >&2
    exit 1
fi

INPUT="$1"
FUZZ_FLAG=""

# Check for --fuzz flag
if [ $# -ge 2 ] && [ "$2" = "--fuzz" ]; then
    FUZZ_FLAG="--fuzz"
fi

# Validate input file exists
if [ ! -f "$INPUT" ]; then
    echo "Error: Input file not found: $INPUT" >&2
    exit 1
fi

# Get absolute path to script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Convert input to absolute path
INPUT="$(cd "$(dirname "$INPUT")" && pwd)/$(basename "$INPUT")"

# Derive output paths (same directory as input)
INPUT_DIR="$(dirname "$INPUT")"
INPUT_BASE="$(basename "$INPUT" .txt)"
TEX_FILE="${INPUT_DIR}/${INPUT_BASE}.tex"
PDF_FILE="${INPUT_DIR}/${INPUT_BASE}.pdf"

echo "Converting: $INPUT"
echo "Output: $PDF_FILE"
echo ""

# Step 1: Generate LaTeX
echo "Step 1/2: Generating LaTeX..."
(cd "$SCRIPT_DIR" && PYTHONPATH="${SCRIPT_DIR}/src" python -m txt2tex.cli "$INPUT" -o "$TEX_FILE" $FUZZ_FLAG)

if [ ! -f "$TEX_FILE" ]; then
    echo "Error: LaTeX generation failed" >&2
    exit 1
fi

echo "  → Generated: $TEX_FILE"

# Step 2: Compile to PDF
echo "Step 2/2: Compiling PDF..."

# Determine tex package directory (relative to script dir)
TEX_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)/tex"

# pdflatex may return non-zero even on success (warnings), so check PDF creation instead
# Include both local latex/ and fuzz location in TEXINPUTS
set +e  # Temporarily disable exit on error
cd "$INPUT_DIR" && TEXINPUTS="${SCRIPT_DIR}/latex//:${TEX_DIR}//:" pdflatex -interaction=nonstopmode "${INPUT_BASE}.tex" > "${INPUT_BASE}.pdflatex.log" 2>&1
PDFLATEX_EXIT=$?
set -e  # Re-enable exit on error

if [ ! -f "${INPUT_BASE}.pdf" ]; then
    echo "Error: PDF compilation failed (exit code: $PDFLATEX_EXIT)" >&2
    echo "Check the LaTeX log: ${INPUT_BASE}.pdflatex.log" >&2
    exit 1
fi

echo "  → Generated: $PDF_FILE"

# Clean up auxiliary files
rm -f "${INPUT_BASE}.aux" "${INPUT_BASE}.log"

echo ""
echo "✓ Success: $PDF_FILE"
