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

# Step 3: Copy LaTeX dependencies locally
echo "Step ${STEP_NUM}: Preparing LaTeX dependencies..."

# Copy LaTeX packages and METAFONT sources to build directory
# This makes the LaTeX self-contained and portable
cp "${SCRIPT_DIR}/latex"/*.sty "$INPUT_DIR/" 2>/dev/null || true
cp "${SCRIPT_DIR}/latex"/*.mf "$INPUT_DIR/" 2>/dev/null || true

echo "  → LaTeX dependencies copied locally"

# Step 4: Compile to PDF
COMPILE_STEP=$((${STEP_NUM%%/*} + 1))
if [ -n "$FUZZ_FLAG" ]; then
    echo "Step ${COMPILE_STEP}/4: Compiling PDF..."
else
    echo "Step ${COMPILE_STEP}/3: Compiling PDF..."
fi

# Use latexmk to handle multiple passes automatically
# It runs pdflatex as many times as needed until citations/references resolve
# No TEXINPUTS/MFINPUTS needed - files are local
set +e  # Temporarily disable exit on error
cd "$INPUT_DIR" && latexmk -pdf -interaction=nonstopmode -file-line-error "${INPUT_BASE}.tex" > "${INPUT_BASE}.latexmk.log" 2>&1
LATEXMK_EXIT=$?

if [ ! -f "${INPUT_BASE}.pdf" ]; then
    echo "Error: PDF compilation failed (exit code: $LATEXMK_EXIT)" >&2
    echo "Check the LaTeX log: ${INPUT_BASE}.latexmk.log" >&2
    set -e
    exit 1
fi

set -e  # Re-enable exit on error

echo "  → Generated: $PDF_FILE"

# Clean up auxiliary files (latexmk creates several)
cd "$INPUT_DIR" && latexmk -c "${INPUT_BASE}.tex" > /dev/null 2>&1 || true

echo ""
echo "✓ Success: $PDF_FILE"
