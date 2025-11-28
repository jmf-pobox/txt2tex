#!/bin/bash
# QA Script for txt2tex PDF and LaTeX Quality Checks
# Usage: ./qa_check.sh [pdf_file]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Require PDF file argument
if [ -z "$1" ]; then
    echo "Usage: ./qa_check.sh <pdf_file>"
    echo "Example: ./qa_check.sh examples/01_propositional_logic/basic_operators.pdf"
    exit 1
fi
PDF_FILE="$1"
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

# 1. Check for garbled characters in PDF (from broken relational image syntax)
echo "=== 1. Garbled Characters in PDF ==="

# First check if PDF has em dashes
EM_DASHES=$(echo "$PDF_TEXT" | grep -o "—" || true)
EM_DASH_COUNT=$(echo "$EM_DASHES" | grep -c . 2>/dev/null | tr -d '\n' || echo "0")

if [ "${EM_DASH_COUNT:-0}" -gt 0 ]; then
    # Check if LaTeX source has literal pipe characters (not \limg or \rimg)
    # Literal pipes in text mode render as em dashes
    if [ -n "$TEX_FILE" ]; then
        # Look for literal (| or |) that are NOT part of \limg or \rimg
        # Pattern: (| or |) not preceded by backslash
        LITERAL_PIPES=$(grep -E '(^|[^\\])\(\||\|\)' "$TEX_FILE" | grep -v '\\limg\|\\rimg' || true)
        LITERAL_PIPE_COUNT=$(echo "$LITERAL_PIPES" | grep -c . 2>/dev/null | tr -d '\n' || echo "0")

        if [ "${LITERAL_PIPE_COUNT:-0}" -gt 0 ]; then
            echo -e "${RED}FAIL: Found $EM_DASH_COUNT em dashes in PDF from ${LITERAL_PIPE_COUNT} literal pipe(s) in LaTeX${NC}"
            echo ""
            echo "Literal pipes in LaTeX (should use \\limg/\\rimg):"
            echo "$LITERAL_PIPES" | head -5
        else
            # Em dashes exist but no literal pipes - these are legitimate (from ---)
            echo -e "${GREEN}PASS: Em dashes are legitimate (from --- in LaTeX, not broken pipes)${NC}"
        fi
    else
        # No tex file to check - report as warning
        echo -e "${YELLOW}WARNING: Found $EM_DASH_COUNT em dashes but cannot verify LaTeX source${NC}"
    fi
else
    echo -e "${GREEN}PASS: No garbled characters found${NC}"
fi
echo ""

# 2. Check for "forall" text instead of symbol
echo "=== 2. Text 'forall' instead of Symbol ==="
# Exclude PURETEXT teaching syntax (has em dash: "forall x : T — predicate")
FORALL_TEXT=$(echo "$PDF_TEXT" | grep "forall" | grep -v " — " | grep -o "forall" || true)
FORALL_COUNT=$(echo "$FORALL_TEXT" | grep -c . 2>/dev/null | tr -d '\n' || echo "0")

if [ "${FORALL_COUNT:-0}" -gt 0 ]; then
    echo -e "${RED}FAIL: Found $FORALL_COUNT instances of text 'forall' (should be ∀ symbol)${NC}"
    # Show context (excluding PURETEXT teaching syntax with em dash)
    echo "$PDF_TEXT" | grep -n "forall" | grep -v " — " | head -5
else
    echo -e "${GREEN}PASS: No text 'forall' found (using symbol ∀)${NC}"
fi
echo ""

# 3. Check for "emptyset" text instead of symbol
echo "=== 3. Text 'emptyset' instead of Symbol ==="
# Exclude PURETEXT teaching syntax (has em dash: "emptyset — literal")
EMPTYSET_TEXT=$(echo "$PDF_TEXT" | grep "emptyset" | grep -v " — " | grep -o "emptyset" || true)
EMPTYSET_COUNT=$(echo "$EMPTYSET_TEXT" | grep -c . 2>/dev/null | tr -d '\n' || echo "0")

if [ "${EMPTYSET_COUNT:-0}" -gt 0 ]; then
    echo -e "${RED}FAIL: Found $EMPTYSET_COUNT instances of text 'emptyset' (should be ∅ symbol)${NC}"
    # Show context (excluding PURETEXT teaching syntax with em dash)
    echo "$PDF_TEXT" | grep -n "emptyset" | grep -v " — " | head -5
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
# Only count LITERAL_PIPE_COUNT as garbled (em dashes from literal pipes)
# EM_DASH_COUNT without literal pipes are legitimate and don't count as issues
TOTAL_ISSUES=$((${LITERAL_PIPE_COUNT:-0} + ${FORALL_COUNT:-0} + ${EMPTYSET_COUNT:-0}))

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
    [ ${LITERAL_PIPE_COUNT:-0} -gt 0 ] && echo "  - $LITERAL_PIPE_COUNT garbled em dashes (from literal pipes in LaTeX)"
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
