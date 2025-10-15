#!/bin/bash
# QA Script for txt2tex PDF and LaTeX Quality Checks
# Usage: ./qa_check.sh [pdf_file]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default to solutions.pdf if no argument
PDF_FILE="${1:-examples/solutions.pdf}"
TEX_FILE="${PDF_FILE%.pdf}.tex"

echo "=========================================="
echo "txt2tex Quality Assurance Check"
echo "=========================================="
echo ""

# Check if files exist
if [ ! -f "$PDF_FILE" ]; then
    echo -e "${RED}ERROR: PDF file not found: $PDF_FILE${NC}"
    exit 1
fi

if [ ! -f "$TEX_FILE" ]; then
    echo -e "${YELLOW}WARNING: LaTeX file not found: $TEX_FILE${NC}"
    echo "Skipping LaTeX checks..."
    TEX_FILE=""
fi

echo "Checking PDF: $PDF_FILE"
if [ -n "$TEX_FILE" ]; then
    echo "Checking LaTeX: $TEX_FILE"
fi
echo ""

# Extract text from PDF
PDF_TEXT=$(pdftotext "$PDF_FILE" -)

# 1. Check for garbled characters in PDF
echo "=== 1. Garbled Characters in PDF ==="
GARBLED_CHARS=$(echo "$PDF_TEXT" | grep -o "[¿¡—]" || true)
GARBLED_COUNT=$(echo "$GARBLED_CHARS" | grep -c . || echo "0")

if [ "$GARBLED_COUNT" -gt 0 ]; then
    echo -e "${RED}FAIL: Found $GARBLED_COUNT garbled characters (¿, ¡, —)${NC}"

    # Show which solutions have garbled characters
    echo ""
    echo "Solutions with garbled characters:"
    echo "$PDF_TEXT" | grep -n "Solution [0-9]" | while read -r line; do
        line_num=$(echo "$line" | cut -d: -f1)
        solution=$(echo "$line" | sed 's/.*Solution \([0-9]*\).*/\1/')
        # Check if garbled chars appear within next 50 lines
        garbled_in_solution=$(echo "$PDF_TEXT" | tail -n +$line_num | head -n 50 | grep -o "[¿¡—]" | wc -l | tr -d ' ')
        if [ "$garbled_in_solution" -gt 0 ]; then
            echo -e "  ${RED}Solution $solution: $garbled_in_solution garbled character(s)${NC}"
        fi
    done
else
    echo -e "${GREEN}PASS: No garbled characters found${NC}"
fi
echo ""

# 2. Check for "forall" text instead of symbol
echo "=== 2. Text 'forall' instead of Symbol ==="
FORALL_TEXT=$(echo "$PDF_TEXT" | grep -o "forall" || true)
FORALL_COUNT=$(echo "$FORALL_TEXT" | grep -c . || echo "0")

if [ "$FORALL_COUNT" -gt 0 ]; then
    echo -e "${RED}FAIL: Found $FORALL_COUNT instances of text 'forall' (should be ∀ symbol)${NC}"
    # Show context
    echo "$PDF_TEXT" | grep -n "forall" | head -5
else
    echo -e "${GREEN}PASS: No text 'forall' found (using symbol ∀)${NC}"
fi
echo ""

# 3. Check for "emptyset" text instead of symbol
echo "=== 3. Text 'emptyset' instead of Symbol ==="
EMPTYSET_TEXT=$(echo "$PDF_TEXT" | grep -o "emptyset" || true)
EMPTYSET_COUNT=$(echo "$EMPTYSET_TEXT" | grep -c . || echo "0")

if [ "$EMPTYSET_COUNT" -gt 0 ]; then
    echo -e "${RED}FAIL: Found $EMPTYSET_COUNT instances of text 'emptyset' (should be ∅ symbol)${NC}"
    echo "$PDF_TEXT" | grep -n "emptyset" | head -5
else
    echo -e "${GREEN}PASS: No text 'emptyset' found (using symbol ∅)${NC}"
fi
echo ""

# 4. Check for runon text (lines without spaces)
echo "=== 4. Runon Text (no spaces) ==="
RUNON_LINES=$(echo "$PDF_TEXT" | awk 'length($0) > 80 && gsub(/[^ ]/,"&") > length($0) * 0.95' || true)
RUNON_COUNT=$(echo "$RUNON_LINES" | grep -c . || echo "0")

if [ "$RUNON_COUNT" -gt 0 ]; then
    echo -e "${YELLOW}WARNING: Found $RUNON_COUNT potential runon lines (>80 chars, >95% non-space)${NC}"
    echo "This may indicate missing spaces or math mode issues"
else
    echo -e "${GREEN}PASS: No obvious runon text detected${NC}"
fi
echo ""

# 5. Check LaTeX file for common issues
if [ -n "$TEX_FILE" ]; then
    echo "=== 5. LaTeX Source Issues ==="

    # Check for bare < and > outside math mode
    BARE_ANGLES=$(grep -n "[^$]<[^>]*>[^$]" "$TEX_FILE" | grep -v "\\langle\\|\\rangle\\|\\begin\\|\\end\\|%\\|\\usepackage" || true)
    BARE_COUNT=$(echo "$BARE_ANGLES" | grep -c . || echo "0")

    if [ "$BARE_COUNT" -gt 0 ]; then
        echo -e "${RED}FAIL: Found $BARE_COUNT potential bare < > characters (should be \\langle \\rangle)${NC}"
        echo "$BARE_ANGLES" | head -5
    else
        echo -e "${GREEN}PASS: No bare angle brackets detected${NC}"
    fi
    echo ""

    # Check for \forall vs forall
    TEX_FORALL_TEXT=$(grep -n "[^\\]forall" "$TEX_FILE" | grep -v "^[[:space:]]*%" || true)
    TEX_FORALL_COUNT=$(echo "$TEX_FORALL_TEXT" | grep -c . || echo "0")

    if [ "$TEX_FORALL_COUNT" -gt 0 ]; then
        echo -e "${RED}FAIL: Found $TEX_FORALL_COUNT instances of plain 'forall' (should be \\forall)${NC}"
        echo "$TEX_FORALL_TEXT" | head -5
    else
        echo -e "${GREEN}PASS: All forall uses \\forall command${NC}"
    fi
    echo ""

    # Check for emptyset vs \emptyset
    TEX_EMPTYSET_TEXT=$(grep -n "[^\\]emptyset" "$TEX_FILE" | grep -v "^[[:space:]]*%" || true)
    TEX_EMPTYSET_COUNT=$(echo "$TEX_EMPTYSET_TEXT" | grep -c . || echo "0")

    if [ "$TEX_EMPTYSET_COUNT" -gt 0 ]; then
        echo -e "${RED}FAIL: Found $TEX_EMPTYSET_COUNT instances of plain 'emptyset' (should be \\emptyset)${NC}"
        echo "$TEX_EMPTYSET_TEXT" | head -5
    else
        echo -e "${GREEN}PASS: All emptyset uses \\emptyset or \\empty${NC}"
    fi
fi

# 6. Summary
echo ""
echo "=========================================="
echo "QA Check Summary"
echo "=========================================="
echo ""

TOTAL_ISSUES=$((GARBLED_COUNT + FORALL_COUNT + EMPTYSET_COUNT))

if [ $TOTAL_ISSUES -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed!${NC}"
    exit 0
else
    echo -e "${RED}✗ Found $TOTAL_ISSUES issue(s)${NC}"
    echo ""
    echo "Issues found:"
    [ $GARBLED_COUNT -gt 0 ] && echo "  - $GARBLED_COUNT garbled characters"
    [ $FORALL_COUNT -gt 0 ] && echo "  - $FORALL_COUNT text 'forall' (should be symbol)"
    [ $EMPTYSET_COUNT -gt 0 ] && echo "  - $EMPTYSET_COUNT text 'emptyset' (should be symbol)"
    exit 1
fi
