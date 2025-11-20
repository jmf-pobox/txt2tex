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

# 4a. Check for common operator text in PDF (Phase 1 - warnings due to false positives)
echo "=== 4a. Operator Text in PDF (Warning) ==="
OPERATOR_WORDS=("and" "or" "not" "exists" "mu")
OPERATOR_TOTAL=0

for word in "${OPERATOR_WORDS[@]}"; do
    COUNT=$(echo "$PDF_TEXT" | grep -o -E "[^[:alpha:]]${word}[^[:alpha:]]" | grep -c . 2>/dev/null | tr -d '\n' || echo "0")
    if [ "${COUNT:-0}" -gt 0 ]; then
        echo -e "${YELLOW}WARNING: Found $COUNT instances of text '${word}' (should be symbol)${NC}"
        echo "Note: This may be false positive if '${word}' appears in prose"
        OPERATOR_TOTAL=$((OPERATOR_TOTAL + COUNT))
    fi
done

if [ "${OPERATOR_TOTAL:-0}" -eq 0 ]; then
    echo -e "${GREEN}PASS: No operator text found (or only in prose)${NC}"
fi
echo ""

# 5. Check LaTeX file for common issues
if [ -n "$TEX_FILE" ]; then
    echo "=== 5. LaTeX Source Issues ==="

    # Check for bare < and > outside math mode
    BARE_ANGLES=$(grep -n "[^$]<[^>]*>[^$]" "$TEX_FILE" | grep -v "\\langle\\|\\rangle\\|\\begin\\|\\end\\|%\\|\\usepackage" || true)
    BARE_COUNT=$(echo "$BARE_ANGLES" | grep -c . 2>/dev/null | tr -d '\n' || echo "0")

    if [ "${BARE_COUNT:-0}" -gt 0 ]; then
        echo -e "${RED}FAIL: Found $BARE_COUNT potential bare < > characters (should be \\langle \\rangle)${NC}"
        echo "$BARE_ANGLES" | head -5
    else
        echo -e "${GREEN}PASS: No bare angle brackets detected${NC}"
    fi
    echo ""

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

    # 5a. Check for plain operator text (Phase 2 - High Priority)
    echo "=== 5a. Plain Operator Text in LaTeX ==="
    TEX_OPERATOR_COUNT=0

    # Check for plain "and" (should be \land)
    TEX_AND_TEXT=$(grep -n -E "\band\b" "$TEX_FILE" | grep -v "^[[:space:]]*%" | grep -v "\\\\land" | grep -v "\\\\begin" | grep -v "\\\\end" || true)
    TEX_AND_COUNT=$(echo "$TEX_AND_TEXT" | grep -c . 2>/dev/null | tr -d '\n' || echo "0")
    if [ "${TEX_AND_COUNT:-0}" -gt 0 ]; then
        echo -e "${RED}FAIL: Found $TEX_AND_COUNT instances of plain 'and' (should be \\land)${NC}"
        echo "$TEX_AND_TEXT" | head -5
        TEX_OPERATOR_COUNT=$((TEX_OPERATOR_COUNT + TEX_AND_COUNT))
    fi

    # Check for plain "or" (should be \lor)
    TEX_OR_TEXT=$(grep -n -E "\bor\b" "$TEX_FILE" | grep -v "^[[:space:]]*%" | grep -v "\\\\lor" | grep -v "\\\\begin" | grep -v "\\\\end" || true)
    TEX_OR_COUNT=$(echo "$TEX_OR_TEXT" | grep -c . 2>/dev/null | tr -d '\n' || echo "0")
    if [ "${TEX_OR_COUNT:-0}" -gt 0 ]; then
        echo -e "${RED}FAIL: Found $TEX_OR_COUNT instances of plain 'or' (should be \\lor)${NC}"
        echo "$TEX_OR_TEXT" | head -5
        TEX_OPERATOR_COUNT=$((TEX_OPERATOR_COUNT + TEX_OR_COUNT))
    fi

    # Check for plain "not" (should be \lnot)
    TEX_NOT_TEXT=$(grep -n -E "\bnot\b" "$TEX_FILE" | grep -v "^[[:space:]]*%" | grep -v "\\\\lnot" | grep -v "\\\\begin" | grep -v "\\\\end" | grep -v "\\\\notin" || true)
    TEX_NOT_COUNT=$(echo "$TEX_NOT_TEXT" | grep -c . 2>/dev/null | tr -d '\n' || echo "0")
    if [ "${TEX_NOT_COUNT:-0}" -gt 0 ]; then
        echo -e "${RED}FAIL: Found $TEX_NOT_COUNT instances of plain 'not' (should be \\lnot)${NC}"
        echo "$TEX_NOT_TEXT" | head -5
        TEX_OPERATOR_COUNT=$((TEX_OPERATOR_COUNT + TEX_NOT_COUNT))
    fi

    # Check for plain "exists" (should be \exists)
    TEX_EXISTS_TEXT=$(grep -n -E "\bexists\b" "$TEX_FILE" | grep -v "^[[:space:]]*%" | grep -v "\\\\exists" | grep -v "exists1" || true)
    TEX_EXISTS_COUNT=$(echo "$TEX_EXISTS_TEXT" | grep -c . 2>/dev/null | tr -d '\n' || echo "0")
    if [ "${TEX_EXISTS_COUNT:-0}" -gt 0 ]; then
        echo -e "${RED}FAIL: Found $TEX_EXISTS_COUNT instances of plain 'exists' (should be \\exists)${NC}"
        echo "$TEX_EXISTS_TEXT" | head -5
        TEX_OPERATOR_COUNT=$((TEX_OPERATOR_COUNT + TEX_EXISTS_COUNT))
    fi

    # Check for plain "exists1" (should be \exists_1)
    TEX_EXISTS1_TEXT=$(grep -n -E "\bexists1\b" "$TEX_FILE" | grep -v "^[[:space:]]*%" | grep -v "\\\\exists_1" || true)
    TEX_EXISTS1_COUNT=$(echo "$TEX_EXISTS1_TEXT" | grep -c . 2>/dev/null | tr -d '\n' || echo "0")
    if [ "${TEX_EXISTS1_COUNT:-0}" -gt 0 ]; then
        echo -e "${RED}FAIL: Found $TEX_EXISTS1_COUNT instances of plain 'exists1' (should be \\exists_1)${NC}"
        echo "$TEX_EXISTS1_TEXT" | head -5
        TEX_OPERATOR_COUNT=$((TEX_OPERATOR_COUNT + TEX_EXISTS1_COUNT))
    fi

    # Check for plain "mu" (should be \mu)
    TEX_MU_TEXT=$(grep -n -E "\bmu\b" "$TEX_FILE" | grep -v "^[[:space:]]*%" | grep -v "\\\\mu" | grep -v "lambda" || true)
    TEX_MU_COUNT=$(echo "$TEX_MU_TEXT" | grep -c . 2>/dev/null | tr -d '\n' || echo "0")
    if [ "${TEX_MU_COUNT:-0}" -gt 0 ]; then
        echo -e "${RED}FAIL: Found $TEX_MU_COUNT instances of plain 'mu' (should be \\mu)${NC}"
        echo "$TEX_MU_TEXT" | head -5
        TEX_OPERATOR_COUNT=$((TEX_OPERATOR_COUNT + TEX_MU_COUNT))
    fi

    if [ "${TEX_OPERATOR_COUNT:-0}" -eq 0 ]; then
        echo -e "${GREEN}PASS: All operators use LaTeX commands${NC}"
    fi
    echo ""

    # 5b. Check for plain implication/equivalence operators (=>, <=>)
    echo "=== 5b. Plain Arrow Operators in LaTeX ==="
    TEX_ARROW_COUNT=0

    # Check for plain "=>" (should be \Rightarrow or \implies)
    TEX_ARROW_TEXT=$(grep -n "=>" "$TEX_FILE" | grep -v "^[[:space:]]*%" | grep -v "\\\\Rightarrow" | grep -v "\\\\implies" || true)
    TEX_ARROW_COUNT1=$(echo "$TEX_ARROW_TEXT" | grep -c . 2>/dev/null | tr -d '\n' || echo "0")
    if [ "${TEX_ARROW_COUNT1:-0}" -gt 0 ]; then
        echo -e "${RED}FAIL: Found $TEX_ARROW_COUNT1 instances of plain '=>' (should be \\Rightarrow or \\implies)${NC}"
        echo "$TEX_ARROW_TEXT" | head -5
        TEX_ARROW_COUNT=$((TEX_ARROW_COUNT + TEX_ARROW_COUNT1))
    fi

    # Check for plain "<=>" (should be \Leftrightarrow or \iff)
    TEX_BIARROW_TEXT=$(grep -n "<=>" "$TEX_FILE" | grep -v "^[[:space:]]*%" | grep -v "\\\\Leftrightarrow" | grep -v "\\\\iff" || true)
    TEX_ARROW_COUNT2=$(echo "$TEX_BIARROW_TEXT" | grep -c . 2>/dev/null | tr -d '\n' || echo "0")
    if [ "${TEX_ARROW_COUNT2:-0}" -gt 0 ]; then
        echo -e "${RED}FAIL: Found $TEX_ARROW_COUNT2 instances of plain '<=>' (should be \\Leftrightarrow or \\iff)${NC}"
        echo "$TEX_BIARROW_TEXT" | head -5
        TEX_ARROW_COUNT=$((TEX_ARROW_COUNT + TEX_ARROW_COUNT2))
    fi

    if [ "${TEX_ARROW_COUNT:-0}" -eq 0 ]; then
        echo -e "${GREEN}PASS: All arrow operators use LaTeX commands${NC}"
    fi
    echo ""

    # 5c. Check for plain type names (N, Z) - Phase 2 High Priority
    echo "=== 5c. Plain Type Names in LaTeX ==="
    TEX_TYPE_COUNT=0

    # Check for plain "N" (should be \nat or \mathbb{N}, but careful - N can be a variable)
    # Only flag if it looks like a type (e.g., " : N" or "N " after certain patterns)
    TEX_N_TEXT=$(grep -n "[^a-zA-Z_]:[[:space:]]*N[^a-zA-Z_]" "$TEX_FILE" | grep -v "^[[:space:]]*%" | grep -v "\\\\nat" | grep -v "\\\\mathbb{N}" || true)
    TEX_N_COUNT=$(echo "$TEX_N_TEXT" | grep -c . 2>/dev/null | tr -d '\n' || echo "0")
    if [ "${TEX_N_COUNT:-0}" -gt 0 ]; then
        echo -e "${RED}FAIL: Found $TEX_N_COUNT instances of plain 'N' as type (should be \\nat or \\mathbb{N})${NC}"
        echo "$TEX_N_TEXT" | head -5
        TEX_TYPE_COUNT=$((TEX_TYPE_COUNT + TEX_N_COUNT))
    fi

    # Check for plain "Z" (should be \num or \mathbb{Z})
    TEX_Z_TEXT=$(grep -n "[^a-zA-Z_]:[[:space:]]*Z[^a-zA-Z_]" "$TEX_FILE" | grep -v "^[[:space:]]*%" | grep -v "\\\\num" | grep -v "\\\\mathbb{Z}" || true)
    TEX_Z_COUNT=$(echo "$TEX_Z_TEXT" | grep -c . 2>/dev/null | tr -d '\n' || echo "0")
    if [ "${TEX_Z_COUNT:-0}" -gt 0 ]; then
        echo -e "${RED}FAIL: Found $TEX_Z_COUNT instances of plain 'Z' as type (should be \\num or \\mathbb{Z})${NC}"
        echo "$TEX_Z_TEXT" | head -5
        TEX_TYPE_COUNT=$((TEX_TYPE_COUNT + TEX_Z_COUNT))
    fi

    if [ "${TEX_TYPE_COUNT:-0}" -eq 0 ]; then
        echo -e "${GREEN}PASS: All type names use LaTeX commands${NC}"
    fi
    echo ""

    # 5d. Check for unconverted citations - Phase 2 Medium Priority
    echo "=== 5d. Citation Conversion Check ==="
    TEX_CITE_TEXT=$(grep -n "\[cite " "$TEX_FILE" | grep -v "^[[:space:]]*%" || true)
    TEX_CITE_COUNT=$(echo "$TEX_CITE_TEXT" | grep -c . 2>/dev/null | tr -d '\n' || echo "0")

    if [ "${TEX_CITE_COUNT:-0}" -gt 0 ]; then
        echo -e "${RED}FAIL: Found $TEX_CITE_COUNT unconverted citations '[cite ' (should be \\citep{})${NC}"
        echo "$TEX_CITE_TEXT" | head -5
    else
        echo -e "${GREEN}PASS: All citations converted to \\citep{}${NC}"
    fi
    echo ""

    # 5e. Check document structure - Phase 2 High Priority
    echo "=== 5e. Document Structure Check ==="
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

    # 5f. Check environment matching - Phase 2 High Priority
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
    TOTAL_ISSUES=$((TOTAL_ISSUES + ${BARE_COUNT:-0} + ${TEX_FORALL_COUNT:-0} + ${TEX_EMPTYSET_COUNT:-0} + ${TEX_OPERATOR_COUNT:-0} + ${TEX_ARROW_COUNT:-0} + ${TEX_TYPE_COUNT:-0} + ${TEX_CITE_COUNT:-0} + ${DOC_ISSUES:-0} + ${ENV_ISSUES:-0}))
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
        [ ${BARE_COUNT:-0} -gt 0 ] && echo "  - $BARE_COUNT bare angle brackets"
        [ ${TEX_FORALL_COUNT:-0} -gt 0 ] && echo "  - $TEX_FORALL_COUNT plain 'forall' in LaTeX"
        [ ${TEX_EMPTYSET_COUNT:-0} -gt 0 ] && echo "  - $TEX_EMPTYSET_COUNT plain 'emptyset' in LaTeX"
        [ ${TEX_OPERATOR_COUNT:-0} -gt 0 ] && echo "  - $TEX_OPERATOR_COUNT plain operator text in LaTeX"
        [ ${TEX_ARROW_COUNT:-0} -gt 0 ] && echo "  - $TEX_ARROW_COUNT plain arrow operators in LaTeX"
        [ ${TEX_TYPE_COUNT:-0} -gt 0 ] && echo "  - $TEX_TYPE_COUNT plain type names in LaTeX"
        [ ${TEX_CITE_COUNT:-0} -gt 0 ] && echo "  - $TEX_CITE_COUNT unconverted citations"
        [ ${DOC_ISSUES:-0} -gt 0 ] && echo "  - $DOC_ISSUES document structure issues"
        [ ${ENV_ISSUES:-0} -gt 0 ] && echo "  - $ENV_ISSUES environment matching issues"
    fi
    exit 1
fi
