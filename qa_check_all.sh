#!/bin/bash
# QA Script for checking all PDFs in hw/ and examples/
# Usage: ./qa_check_all.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Create unique temporary file and ensure cleanup on exit
TEMP_FILE=$(mktemp /tmp/qa_check_output.XXXXXX)
trap "rm -f $TEMP_FILE" EXIT

echo "=========================================="
echo "txt2tex QA Check - All PDFs"
echo "=========================================="
echo ""

# Find all PDFs in hw/ and examples/ (excluding reference/ and infrastructure/)
PDFS=$(find hw/ examples/ -name "*.pdf" ! -path "*/reference/*" ! -path "*/infrastructure/*" | sort)

if [ -z "$PDFS" ]; then
    echo -e "${YELLOW}WARNING: No PDF files found in hw/ or examples/${NC}"
    exit 0
fi

TOTAL_COUNT=$(echo "$PDFS" | wc -l | tr -d ' ')
echo "Found $TOTAL_COUNT PDF file(s) to check"
echo ""

# Counters
TOTAL_PASSED=0
TOTAL_FAILED=0
FAILED_FILES=""

# Check each PDF
for PDF in $PDFS; do
    echo -e "${BLUE}Checking: $PDF${NC}"
    
    # Run qa_check.sh but capture output and exit code
    if ./qa_check.sh "$PDF" > "$TEMP_FILE" 2>&1; then
        echo -e "${GREEN}✓ PASS: $PDF${NC}"
        TOTAL_PASSED=$((TOTAL_PASSED + 1))
    else
        EXIT_CODE=$?
        echo -e "${RED}✗ FAIL: $PDF${NC}"
        TOTAL_FAILED=$((TOTAL_FAILED + 1))
        FAILED_FILES="$FAILED_FILES\n  - $PDF"
        
        # Show summary of issues (last few lines of output)
        echo "  Issues found:"
        tail -n 10 "$TEMP_FILE" | grep -E "Found|garbled|forall|emptyset" | head -5 | sed 's/^/    /' || true
    fi
    echo ""
done

# Final summary
echo "=========================================="
echo "QA Check Summary - All PDFs"
echo "=========================================="
echo ""
echo "Total PDFs checked: $TOTAL_COUNT"
echo -e "${GREEN}Passed: $TOTAL_PASSED${NC}"
if [ $TOTAL_FAILED -gt 0 ]; then
    echo -e "${RED}Failed: $TOTAL_FAILED${NC}"
    echo -e "\nFailed files:"
    echo -e "$FAILED_FILES"
    exit 1
else
    echo -e "${GREEN}Failed: 0${NC}"
    echo -e "\n${GREEN}✓ All PDFs passed QA checks!${NC}"
    exit 0
fi

