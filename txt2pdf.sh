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

# Step 2: Type check with fuzz (if --fuzz flag is set)
if [ -n "$FUZZ_FLAG" ]; then
    echo "Step 2/3: Type checking with fuzz..."

    # Check if fuzz command exists
    if ! command -v fuzz > /dev/null 2>&1; then
        echo "Error: fuzz command not found in PATH" >&2
        echo "The fuzz type checker is required when using --fuzz option" >&2
        exit 1
    fi

    # Run fuzz type checker
    # Use full type check (not just -s syntax check)
    cd "$INPUT_DIR" && fuzz "${INPUT_BASE}.tex" > "${INPUT_BASE}.fuzz.log" 2>&1
    FUZZ_EXIT=$?

    if [ $FUZZ_EXIT -ne 0 ]; then
        echo "Error: Fuzz type checking failed (exit code: $FUZZ_EXIT)" >&2
        echo "Check the fuzz log: ${INPUT_BASE}.fuzz.log" >&2
        echo "" >&2
        echo "Fuzz output:" >&2
        cat "${INPUT_BASE}.fuzz.log" >&2
        exit 1
    fi

    echo "  → Type check passed"
    STEP_NUM="3/3"
else
    STEP_NUM="2/2"
fi

# Step 3: Compile to PDF
echo "Step ${STEP_NUM}: Compiling PDF..."

# Determine tex package directory (relative to script dir)
TEX_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)/tex"

# pdflatex may return non-zero even on success (warnings), so check PDF creation instead
# Include both local latex/ and fuzz location in TEXINPUTS and MFINPUTS
set +e  # Temporarily disable exit on error
cd "$INPUT_DIR" && TEXINPUTS="${SCRIPT_DIR}/latex//:${TEX_DIR}//:" MFINPUTS="${SCRIPT_DIR}/latex//:${TEX_DIR}//:" pdflatex -interaction=nonstopmode "${INPUT_BASE}.tex" > "${INPUT_BASE}.pdflatex.log" 2>&1
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
