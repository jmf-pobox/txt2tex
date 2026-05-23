#!/bin/bash
# QA Script for txt2tex PDF and LaTeX Quality Checks
# Usage: ./qa_check.sh <pdf_file>
#
# Checks a single PDF + .tex pair for rendering defects that are not caught
# by fuzz typecheck or unit tests. Each check is narrowly scoped to avoid
# false positives — e.g. the `forall`/`emptyset` keyword checks only fire
# inside math environments, because the engine correctly preserves these
# words as English in TEXT/section prose post-#136.

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Use printf for output that contains backslashes; echo -e interprets
# backslash escapes (\f, \c, etc.) and mangles LaTeX command names in
# success messages.
pass() { printf "${GREEN}PASS: %s${NC}\n" "$1"; }
fail() { printf "${RED}FAIL: %s${NC}\n" "$1"; }
warn() { printf "${YELLOW}WARNING: %s${NC}\n" "$1"; }

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

if [ ! -f "$PDF_FILE" ]; then
    fail "PDF file not found: $PDF_FILE"
    exit 1
fi

if [ ! -f "$TEX_FILE" ]; then
    warn "LaTeX file not found: $TEX_FILE — skipping LaTeX checks"
    TEX_FILE=""
fi

echo "Checking PDF: $PDF_FILE"
[ -n "$TEX_FILE" ] && echo "Checking LaTeX: $TEX_FILE"
echo ""

if ! command -v pdftotext &> /dev/null; then
    fail "pdftotext command not found (install poppler-utils: brew install poppler)"
    exit 1
fi

if ! PDF_TEXT=$(pdftotext "$PDF_FILE" - 2>&1); then
    fail "Failed to extract text from PDF"
    echo "pdftotext output: $PDF_TEXT"
    exit 1
fi

if [ -z "$PDF_TEXT" ]; then
    fail "PDF text extraction produced empty output (image-only PDF?)"
    exit 1
fi

# ---------------------------------------------------------------------------
# 1. Garbled em dashes from broken relational image syntax `R(| S |)`.
#    If the LaTeX has literal `(|` or `|)` (rather than `\limg` / `\rimg`),
#    the PDF renders those literal pipes as em dashes.
# ---------------------------------------------------------------------------
echo "=== 1. Garbled Em Dashes (broken relational image) ==="
EM_DASH_COUNT=$(printf '%s' "$PDF_TEXT" | grep -o "—" | wc -l | tr -d ' ')
LITERAL_PIPE_COUNT=0
if [ "${EM_DASH_COUNT:-0}" -gt 0 ] && [ -n "$TEX_FILE" ]; then
    LITERAL_PIPES=$(grep -E '(^|[^\\])\(\||\|\)' "$TEX_FILE" | grep -v '\\limg\|\\rimg' || true)
    LITERAL_PIPE_COUNT=$(printf '%s' "$LITERAL_PIPES" | grep -c . | tr -d '\n')
    if [ "${LITERAL_PIPE_COUNT:-0}" -gt 0 ]; then
        fail "Found $EM_DASH_COUNT em dashes in PDF from $LITERAL_PIPE_COUNT literal pipe(s) in LaTeX"
        echo "Literal pipes in LaTeX (should use \\limg/\\rimg):"
        printf '%s\n' "$LITERAL_PIPES" | head -5
    else
        pass "Em dashes are legitimate (--- in LaTeX, not broken pipes)"
    fi
else
    pass "No garbled-pipe em dashes found"
fi
echo ""

# ---------------------------------------------------------------------------
# 2. Bare keywords inside math environments.
#    The engine substitutes `forall`/`emptyset`/etc. with their LaTeX
#    commands ONLY inside math contexts. If a bare `forall` appears INSIDE
#    \begin{zed}/\begin{axdef}/\begin{schema}/\begin{gendef}/\begin{argue},
#    that is a real rendering bug.  Bare keywords in TEXT prose, section
#    headers, or \noindent paragraphs are intentional English use post-#136
#    and must not be flagged.
# ---------------------------------------------------------------------------
MATH_BARE_COUNT=0
if [ -n "$TEX_FILE" ]; then
    echo "=== 2. Bare Math Keywords inside Math Environments ==="
    MATH_KEYWORDS='\b(forall|exists|exists1|emptyset|land|lor|lnot|bigcup|bigcap|union|intersect)\b'
    MATH_BARE=$(awk -v kws="$MATH_KEYWORDS" '
        /\\begin\{(zed|axdef|schema|gendef|argue)\}/ { depth++; next }
        /\\end\{(zed|axdef|schema|gendef|argue)\}/   { depth--; next }
        depth > 0 {
            # Strip already-escaped commands (\forall, \exists, ...) before
            # testing.  awk default regex implementations vary; use gensub
            # if gawk is available, else manual.
            line = $0
            gsub(/\\[A-Za-z]+/, "", line)
            if (line ~ kws) {
                printf("%d: %s\n", NR, $0)
            }
        }
    ' "$TEX_FILE" 2>/dev/null || true)
    MATH_BARE_COUNT=$(printf '%s' "$MATH_BARE" | grep -c . | tr -d '\n')
    if [ "${MATH_BARE_COUNT:-0}" -gt 0 ]; then
        fail "Found $MATH_BARE_COUNT bare keyword(s) inside math environments (should be \\command form)"
        printf '%s\n' "$MATH_BARE" | head -5
    else
        pass "No bare math keywords inside math environments"
    fi
    echo ""
fi

# ---------------------------------------------------------------------------
# 3. Runon text (potential missing-space defect).
# ---------------------------------------------------------------------------
echo "=== 3. Runon Text (warning) ==="
RUNON_LINES=$(printf '%s' "$PDF_TEXT" | awk 'length($0) > 80 && gsub(/[^ ]/,"&") > length($0) * 0.95' || true)
RUNON_COUNT=$(printf '%s' "$RUNON_LINES" | grep -c . | tr -d '\n')
if [ "${RUNON_COUNT:-0}" -gt 0 ]; then
    warn "Found $RUNON_COUNT line(s) >80 chars with >95% non-space content (possible runon)"
else
    pass "No obvious runon text detected"
fi
echo ""

# ---------------------------------------------------------------------------
# LaTeX-source-only checks below this point.
# ---------------------------------------------------------------------------
TEX_CITE_COUNT=0
DOC_ISSUES=0
ENV_ISSUES=0
if [ -n "$TEX_FILE" ]; then
    # 4. Unconverted citations: `[cite X]` should become `\citep{X}`.
    echo "=== 4. Citation Conversion ==="
    TEX_CITE_LINES=$(grep -n '\[cite ' "$TEX_FILE" | grep -v '^[[:space:]]*%' || true)
    TEX_CITE_COUNT=$(printf '%s' "$TEX_CITE_LINES" | grep -c . | tr -d '\n')
    if [ "${TEX_CITE_COUNT:-0}" -gt 0 ]; then
        fail "Found $TEX_CITE_COUNT unconverted citation(s) '[cite ...]' (should be \\citep{...})"
        printf '%s\n' "$TEX_CITE_LINES" | head -5
    else
        pass "All citations converted to \\citep{}"
    fi
    echo ""

    # 5. Document structure: required preamble + body markers present.
    echo "=== 5. Document Structure ==="
    if ! grep -q '\\documentclass' "$TEX_FILE"; then
        fail "Missing \\documentclass"
        DOC_ISSUES=$((DOC_ISSUES + 1))
    fi
    if ! grep -q '\\begin{document}' "$TEX_FILE"; then
        fail "Missing \\begin{document}"
        DOC_ISSUES=$((DOC_ISSUES + 1))
    fi
    if ! grep -q '\\end{document}' "$TEX_FILE"; then
        fail "Missing \\end{document}"
        DOC_ISSUES=$((DOC_ISSUES + 1))
    fi
    if [ "${DOC_ISSUES:-0}" -eq 0 ]; then
        pass "Document structure complete (\\documentclass, \\begin{document}, \\end{document})"
    fi
    echo ""

    # 6. Environment matching: every \begin{X} has a matching \end{X}.
    echo "=== 6. Environment Matching ==="
    for env in axdef schema zed gendef argue; do
        b=$(grep -c "\\\\begin{${env}}" "$TEX_FILE" 2>/dev/null | tr -d '\n')
        e=$(grep -c "\\\\end{${env}}" "$TEX_FILE" 2>/dev/null | tr -d '\n')
        if [ "${b:-0}" != "${e:-0}" ]; then
            fail "Mismatched ${env} environments (begin: $b, end: $e)"
            ENV_ISSUES=$((ENV_ISSUES + 1))
        fi
    done
    if [ "${ENV_ISSUES:-0}" -eq 0 ]; then
        pass "All environments properly matched"
    fi
    echo ""
fi

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
echo "=========================================="
echo "QA Check Summary"
echo "=========================================="
echo ""

TOTAL_ISSUES=$(( ${LITERAL_PIPE_COUNT:-0} + ${MATH_BARE_COUNT:-0} + ${TEX_CITE_COUNT:-0} + ${DOC_ISSUES:-0} + ${ENV_ISSUES:-0} ))

if [ ${TOTAL_ISSUES:-0} -eq 0 ]; then
    printf "${GREEN}\xe2\x9c\x93 All checks passed!${NC}\n"
    exit 0
else
    printf "${RED}\xe2\x9c\x97 Found %d issue(s)${NC}\n" "$TOTAL_ISSUES"
    echo ""
    echo "Issues found:"
    [ ${LITERAL_PIPE_COUNT:-0} -gt 0 ] && echo "  - $LITERAL_PIPE_COUNT garbled em dashes from literal pipes"
    [ ${MATH_BARE_COUNT:-0}    -gt 0 ] && echo "  - $MATH_BARE_COUNT bare keyword(s) inside math environments"
    [ ${TEX_CITE_COUNT:-0}     -gt 0 ] && echo "  - $TEX_CITE_COUNT unconverted [cite ...] directive(s)"
    [ ${DOC_ISSUES:-0}         -gt 0 ] && echo "  - $DOC_ISSUES document structure issue(s)"
    [ ${ENV_ISSUES:-0}         -gt 0 ] && echo "  - $ENV_ISSUES environment-matching issue(s)"
    exit 1
fi
