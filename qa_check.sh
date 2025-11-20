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

# Check if pdftotext is installed
if ! command -v pdftotext &> /dev/null; then
    echo -e "${RED}ERROR: pdftotext command not found${NC}"
    echo "Please install poppler-utils: brew install poppler"
    exit 1
fi

# Extract text from PDF
if ! PDF_TEXT=$(pdftotext "$PDF_FILE" - 2>&1); then
    echo -e "${RED}ERROR: Failed to extract text from PDF${NC}"
    echo "pdftotext output: $PDF_TEXT"
    exit 1
fi

# Verify PDF text extraction succeeded
if [ -z "$PDF_TEXT" ]; then
    echo -e "${RED}ERROR: PDF text extraction produced empty output${NC}"
    echo "The PDF may be corrupted or contain only images"
    exit 1
fi

# 1. Check for garbled characters in PDF
echo "=== 1. Garbled Characters in PDF ==="
GARBLED_CHARS=$(echo "$PDF_TEXT" | grep -o "[¿¡—]" || true)
GARBLED_COUNT=$(echo "$GARBLED_CHARS" | grep -c . 2>/dev/null | tr -d '\n' || echo "0")

if [ "${GARBLED_COUNT:-0}" -gt 0 ]; then
    echo -e "${RED}FAIL: Found $GARBLED_COUNT garbled characters (¿, ¡, —)${NC}"

    # Show which solutions have garbled characters
    echo ""
    echo "Solutions with garbled characters:"
    echo "$PDF_TEXT" | grep -n "Solution [0-9]\+" | while read -r line; do
        line_num=$(echo "$line" | cut -d: -f1)
        solution=$(echo "$line" | sed 's/.*Solution \([0-9]\+\).*/\1/')
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
FORALL_COUNT=$(echo "$FORALL_TEXT" | grep -c . 2>/dev/null | tr -d '\n' || echo "0")

if [ "${FORALL_COUNT:-0}" -gt 0 ]; then
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
EMPTYSET_COUNT=$(echo "$EMPTYSET_TEXT" | grep -c . 2>/dev/null | tr -d '\n' || echo "0")

if [ "${EMPTYSET_COUNT:-0}" -gt 0 ]; then
    echo -e "${RED}FAIL: Found $EMPTYSET_COUNT instances of text 'emptyset' (should be ∅ symbol)${NC}"
    echo "$PDF_TEXT" | grep -n "emptyset" | head -5
else
    echo -e "${GREEN}PASS: No text 'emptyset' found (using symbol ∅)${NC}"
fi
echo ""

# 4. Check for runon text (lines without spaces)
echo "=== 4. Runon Text (no spaces) ==="
RUNON_LINES=$(echo "$PDF_TEXT" | awk 'length($0) > 80 && gsub(/[^ ]/,"&") > length($0) * 0.95' || true)
RUNON_COUNT=$(echo "$RUNON_LINES" | grep -c . 2>/dev/null | tr -d '\n' || echo "0")

if [ "${RUNON_COUNT:-0}" -gt 0 ]; then
    echo -e "${YELLOW}WARNING: Found $RUNON_COUNT potential runon lines (>80 chars, >95% non-space)${NC}"
    echo "This may indicate missing spaces or math mode issues"
else
    echo -e "${GREEN}PASS: No obvious runon text detected${NC}"
fi
echo ""


# 5. Check LaTeX file for common issues
if [ -n "$TEX_FILE" ]; then
    echo "=== 5. LaTeX Source Issues ==="

    # Check for \forall vs forall
    TEX_FORALL_TEXT=$(grep -n "[^\\]forall" "$TEX_FILE" | grep -v "^[[:space:]]*%" || true)
    TEX_FORALL_COUNT=$(echo "$TEX_FORALL_TEXT" | grep -c . 2>/dev/null | tr -d '\n' || echo "0")

    if [ "${TEX_FORALL_COUNT:-0}" -gt 0 ]; then
        echo -e "${RED}FAIL: Found $TEX_FORALL_COUNT instances of plain 'forall' (should be \\forall)${NC}"
        echo "$TEX_FORALL_TEXT" | head -5
    else
        echo -e "${GREEN}PASS: All forall uses \\forall command${NC}"
    fi
    echo ""

    # Check for emptyset vs \emptyset
    TEX_EMPTYSET_TEXT=$(grep -n "[^\\]emptyset" "$TEX_FILE" | grep -v "^[[:space:]]*%" || true)
    TEX_EMPTYSET_COUNT=$(echo "$TEX_EMPTYSET_TEXT" | grep -c . 2>/dev/null | tr -d '\n' || echo "0")

    if [ "${TEX_EMPTYSET_COUNT:-0}" -gt 0 ]; then
        echo -e "${RED}FAIL: Found $TEX_EMPTYSET_COUNT instances of plain 'emptyset' (should be \\emptyset)${NC}"
        echo "$TEX_EMPTYSET_TEXT" | head -5
    else
        echo -e "${GREEN}PASS: All emptyset uses \\emptyset or \\empty${NC}"
    fi
    echo ""

    # 5a. Check for unconverted citations - Phase 2 Medium Priority
    echo "=== 5a. Citation Conversion Check ==="
    TEX_CITE_TEXT=$(grep -n "\[cite " "$TEX_FILE" | grep -v "^[[:space:]]*%" || true)
    TEX_CITE_COUNT=$(echo "$TEX_CITE_TEXT" | grep -c . 2>/dev/null | tr -d '\n' || echo "0")

    if [ "${TEX_CITE_COUNT:-0}" -gt 0 ]; then
        echo -e "${RED}FAIL: Found $TEX_CITE_COUNT unconverted citations '[cite ' (should be \\citep{})${NC}"
        echo "$TEX_CITE_TEXT" | head -5
    else
        echo -e "${GREEN}PASS: All citations converted to \\citep{}${NC}"
    fi
    echo ""

    # 5b. Check document structure - Phase 2 High Priority
    echo "=== 5b. Document Structure Check ==="
    DOC_ISSUES=0

    if ! grep -q "\\\\documentclass" "$TEX_FILE"; then
        echo -e "${RED}FAIL: Missing \\documentclass${NC}"
        DOC_ISSUES=$((DOC_ISSUES + 1))
    fi

    if ! grep -q "\\\\begin{document}" "$TEX_FILE"; then
        echo -e "${RED}FAIL: Missing \\begin{document}${NC}"
        DOC_ISSUES=$((DOC_ISSUES + 1))
    fi

    if ! grep -q "\\\\end{document}" "$TEX_FILE"; then
        echo -e "${RED}FAIL: Missing \\end{document}${NC}"
        DOC_ISSUES=$((DOC_ISSUES + 1))
    fi

    if [ "${DOC_ISSUES:-0}" -eq 0 ]; then
        echo -e "${GREEN}PASS: Document structure is complete${NC}"
    fi
    echo ""

    # 5c. Check environment matching - Phase 2 High Priority
    echo "=== 5f. Environment Matching Check ==="
    ENV_ISSUES=0

    # Check axdef environments
    AXDEF_BEGIN=$(grep -c "\\\\begin{axdef}" "$TEX_FILE" 2>/dev/null | tr -d '\n' || echo "0")
    AXDEF_END=$(grep -c "\\\\end{axdef}" "$TEX_FILE" 2>/dev/null | tr -d '\n' || echo "0")
    if [ "${AXDEF_BEGIN:-0}" != "${AXDEF_END:-0}" ]; then
        echo -e "${RED}FAIL: Mismatched axdef environments (begin: $AXDEF_BEGIN, end: $AXDEF_END)${NC}"
        ENV_ISSUES=$((ENV_ISSUES + 1))
    fi

    # Check schema environments
    SCHEMA_BEGIN=$(grep -c "\\\\begin{schema}" "$TEX_FILE" 2>/dev/null | tr -d '\n' || echo "0")
    SCHEMA_END=$(grep -c "\\\\end{schema}" "$TEX_FILE" 2>/dev/null | tr -d '\n' || echo "0")
    if [ "${SCHEMA_BEGIN:-0}" != "${SCHEMA_END:-0}" ]; then
        echo -e "${RED}FAIL: Mismatched schema environments (begin: $SCHEMA_BEGIN, end: $SCHEMA_END)${NC}"
        ENV_ISSUES=$((ENV_ISSUES + 1))
    fi

    # Check zed environments
    ZED_BEGIN=$(grep -c "\\\\begin{zed}" "$TEX_FILE" 2>/dev/null | tr -d '\n' || echo "0")
    ZED_END=$(grep -c "\\\\end{zed}" "$TEX_FILE" 2>/dev/null | tr -d '\n' || echo "0")
    if [ "${ZED_BEGIN:-0}" != "${ZED_END:-0}" ]; then
        echo -e "${RED}FAIL: Mismatched zed environments (begin: $ZED_BEGIN, end: $ZED_END)${NC}"
        ENV_ISSUES=$((ENV_ISSUES + 1))
    fi

    if [ "${ENV_ISSUES:-0}" -eq 0 ]; then
        echo -e "${GREEN}PASS: All environments are properly matched${NC}"
    fi
    echo ""
fi

# 6. Summary
echo ""
echo "=========================================="
echo "QA Check Summary"
echo "=========================================="
echo ""

# Calculate total issues (PDF errors only - warnings don't count toward failure)
TOTAL_ISSUES=$((${GARBLED_COUNT:-0} + ${FORALL_COUNT:-0} + ${EMPTYSET_COUNT:-0}))

# Add LaTeX source issues if available
if [ -n "$TEX_FILE" ]; then
    TOTAL_ISSUES=$((TOTAL_ISSUES + ${TEX_FORALL_COUNT:-0} + ${TEX_EMPTYSET_COUNT:-0} + ${TEX_CITE_COUNT:-0} + ${DOC_ISSUES:-0} + ${ENV_ISSUES:-0}))
fi

if [ ${TOTAL_ISSUES:-0} -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed!${NC}"
    exit 0
else
    echo -e "${RED}✗ Found $TOTAL_ISSUES issue(s)${NC}"
    echo ""
    echo "Issues found:"
    [ ${GARBLED_COUNT:-0} -gt 0 ] && echo "  - $GARBLED_COUNT garbled characters"
    [ ${FORALL_COUNT:-0} -gt 0 ] && echo "  - $FORALL_COUNT text 'forall' (should be symbol)"
    [ ${EMPTYSET_COUNT:-0} -gt 0 ] && echo "  - $EMPTYSET_COUNT text 'emptyset' (should be symbol)"
    if [ -n "$TEX_FILE" ]; then
        [ ${TEX_FORALL_COUNT:-0} -gt 0 ] && echo "  - $TEX_FORALL_COUNT plain 'forall' in LaTeX"
        [ ${TEX_EMPTYSET_COUNT:-0} -gt 0 ] && echo "  - $TEX_EMPTYSET_COUNT plain 'emptyset' in LaTeX"
        [ ${TEX_CITE_COUNT:-0} -gt 0 ] && echo "  - $TEX_CITE_COUNT unconverted citations"
        [ ${DOC_ISSUES:-0} -gt 0 ] && echo "  - $DOC_ISSUES document structure issues"
        [ ${ENV_ISSUES:-0} -gt 0 ] && echo "  - $ENV_ISSUES environment matching issues"
    fi
    exit 1
fi
