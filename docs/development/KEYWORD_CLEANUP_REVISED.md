# Keyword Deprecation Cleanup: Revised Analysis

**Date:** November 2025
**Status:** Corrected after initial implementation failure

## Executive Summary

After English keyword deprecation (and→land, or→lor, not→lnot, in→elem), ONE specific piece of disambiguation logic can be safely removed: the "where"/"and" prose detection at column 1 (lines 1146-1179 in lexer.py).

**Key Insight**: The `prose_starters` set serves GENERAL prose detection (needed for "(a) First part") and must be retained. Only the specific "where"/"and" disambiguation logic is obsolete.

## Cleanup Opportunities (Revised)

### SAFE TO REMOVE: where/and prose detection (34 lines)

**Location**: `src/txt2tex/lexer.py` lines 1146-1179

**Purpose**: Disambiguate "where" and "and" keywords from prose by checking for indicators like " is ", " by ", " are "

**Example**:
- "where cat.1a is defined as..." → prose (not Z notation where clause)
- "and the second by induction" → prose (not logical and operator)

**Why removable**:
- "and" is no longer a keyword (we use "land")
- "where" is still a keyword but structural context makes it unambiguous

**Verification**: Test with examples containing "where" and "and" in prose contexts

### MUST KEEP: prose_starters set (87 words)

**Location**: `src/txt2tex/lexer.py` lines 960-1047

**Purpose**: Detect prose at ANY position, not just keyword disambiguation

**Critical for**:
- Part labels: "(a) First part"
- Paragraph detection: "The following theorem..."
- Solution text: "This proves the statement"

**Why needed**: Without this, prose gets parsed as math expressions

### CAN CONSOLIDATE: Duplicate prose word lists

**Locations**:
- `src/txt2tex/parser.py` lines 1555-1585 (28 words)
- `src/txt2tex/latex_gen.py` lines 2942-2982 (40+ words)

**Action**: Create shared constant, import where needed

## Revised Cleanup Plan

### Phase 1: Remove where/and detection (LOW RISK)
1. Remove lines 1146-1179 from lexer.py
2. Run full test suite
3. Verify examples compile

**Expected**: All tests pass, ~34 lines removed

### Phase 2: Consolidate prose lists (LOW RISK)
1. Create `src/txt2tex/constants.py` with PROSE_WORDS
2. Update parser.py to import
3. Update latex_gen.py to import

**Expected**: ~80 lines of duplication eliminated

### Phase 3: Documentation cleanup (NO RISK)
1. Remove obsolete comments about English keywords
2. Add comments explaining current keyword system

**Expected**: Clearer codebase

## Total Impact (Revised)

- **Lines removed**: ~120 (not 400-500)
- **Complexity reduction**: Moderate (not high)
- **Risk**: Low (tested incrementally)

## Lessons Learned

1. **Distinguish purpose from implementation**: The prose_starters set appeared to be for keyword disambiguation but actually serves general prose detection
2. **Test incrementally**: Removing large blocks without testing broke functionality
3. **Read code comments carefully**: "Examples: 'where cat.1a is', 'and the second by'" clearly indicated the where/and block was for keyword disambiguation
4. **Conservative > Aggressive**: Better to remove less with confidence than remove more and break things
