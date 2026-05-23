#!/bin/bash
# QA Script for checking all PDFs under examples/.
# Usage: ./qa_check_all.sh
#
# Runs qa_check.sh against every PDF in examples/, excluding the reference/
# and infrastructure/ subdirectories.  hw1/, hw2/, hw/, and sem/ are out of
# scope — the gate covers only the published examples corpus.

set -u

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

TEMP_FILE=$(mktemp /tmp/qa_check_output.XXXXXX)
trap 'rm -f "$TEMP_FILE"' EXIT

echo "=========================================="
echo "txt2tex QA Check — examples/ PDFs"
echo "=========================================="
echo ""

PDFS=$(find examples/ -name "*.pdf" \
    ! -path "*/reference/*" \
    ! -path "*/infrastructure/*" \
    | sort)

if [ -z "$PDFS" ]; then
    printf "${YELLOW}WARNING: No PDF files found under examples/${NC}\n"
    exit 0
fi

TOTAL_COUNT=$(printf '%s\n' "$PDFS" | wc -l | tr -d ' ')
echo "Found $TOTAL_COUNT PDF file(s) to check"
echo ""

TOTAL_PASSED=0
TOTAL_FAILED=0
FAILED_FILES=""

for PDF in $PDFS; do
    printf "${BLUE}Checking: %s${NC}\n" "$PDF"
    if ./qa_check.sh "$PDF" > "$TEMP_FILE" 2>&1; then
        printf "${GREEN}\xe2\x9c\x93 PASS: %s${NC}\n" "$PDF"
        TOTAL_PASSED=$((TOTAL_PASSED + 1))
    else
        printf "${RED}\xe2\x9c\x97 FAIL: %s${NC}\n" "$PDF"
        TOTAL_FAILED=$((TOTAL_FAILED + 1))
        FAILED_FILES="${FAILED_FILES}\n  - ${PDF}"
        echo "  Issues:"
        grep -E "FAIL|Found [0-9]+ issue" "$TEMP_FILE" | head -6 | sed 's/^/    /'
    fi
    echo ""
done

echo "=========================================="
echo "QA Check Summary — examples/ PDFs"
echo "=========================================="
echo ""
echo "Total PDFs checked: $TOTAL_COUNT"
printf "${GREEN}Passed: %d${NC}\n" "$TOTAL_PASSED"
if [ $TOTAL_FAILED -gt 0 ]; then
    printf "${RED}Failed: %d${NC}\n" "$TOTAL_FAILED"
    printf "\nFailed files:%b\n" "$FAILED_FILES"
    exit 1
else
    printf "${GREEN}Failed: 0${NC}\n"
    printf "\n${GREEN}\xe2\x9c\x93 All examples passed QA checks!${NC}\n"
    exit 0
fi
