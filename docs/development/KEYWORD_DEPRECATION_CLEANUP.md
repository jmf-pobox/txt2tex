# Keyword Deprecation Cleanup Analysis

**Date:** November 2025
**Author:** Design Guardian
**Purpose:** Identify and document complexity that can be removed after deprecating English keywords

---

## Executive Summary

The txt2tex project recently migrated from English logical keywords (`and`, `or`, `not`, `in`) to LaTeX-style keywords (`land`, `lor`, `lnot`, `elem`). This migration was motivated by ambiguity between prose and logical operators. A comprehensive analysis of the codebase reveals **significant complexity** that was introduced to handle this ambiguity and can now be simplified or removed.

### Key Findings
- **1,100+ lines of prose detection logic** in the lexer
- **40+ hardcoded prose words** in parser and generator
- **Complex lookahead patterns** for distinguishing prose from operators
- **Duplicated word lists** across multiple files
- **No actual support** for English keywords remains (already removed)

### Impact Assessment
- **High complexity** areas: Prose detection (lexer lines 956-1180)
- **Medium complexity** areas: Parser prose rejection, LaTeX generator prose detection
- **Low risk** for removal: No backward compatibility concerns since English keywords are already unsupported

---

## Detailed Findings

### 1. Lexer (`src/txt2tex/lexer.py`)

#### 1.1 Extensive Prose Detection Logic (Lines 956-1180)
**Complexity Score: HIGH**

The lexer contains ~225 lines of complex logic to detect when words like "and", "where" are prose vs operators:

```python
# Lines 960-1047: Massive prose_starters set with 87+ entries
prose_starters = {
    "The", "This", "These", "Those", "That", "We", "It", "They",
    "There", "Here", "In", "On", "At", "For", "When", "Where",
    # ... 71 more entries including contractions
}

# Lines 1146-1180: Special handling for "where" and "and" at line start
if start_column == 1 and value in ("where", "and"):
    # Complex lookahead to detect prose indicators
    prose_indicators = [" is ", " is", " by ", " by", " are ", ...]
    if any(indicator in full_line for indicator in prose_indicators):
        # Capture entire line as TEXT token
```

**Can be removed:** YES - This entire section exists solely to disambiguate English keywords from prose. With only LaTeX-style keywords (`land`, `lor`, `lnot`), this complexity is unnecessary.

#### 1.2 Article Detection Logic (Lines 1074-1145)
**Complexity Score: MEDIUM**

Special handling for "A" and "An" to determine if they're articles (prose) or type names:

```python
# Lines 1074-1145: Complex article detection
if start_column == 1 and value in ("A", "An"):
    # Peek ahead to check next word
    # Check against Z keywords list
    z_keywords = {"land", "lor", "lnot", "union", "intersect", ...}
    if next_word not in z_keywords:
        # Treat as prose, capture whole line
```

**Can be simplified:** PARTIAL - The Z keywords check is still needed, but the list no longer needs to include "and", "or", "not" since they're not keywords anymore.

#### 1.3 Keyword Recognition (Lines 1181-1189)
**Complexity Score: LOW**

Current state - only LaTeX-style keywords recognized:

```python
if value == "land":
    return Token(TokenType.AND, value, start_line, start_column)
if value == "lor":
    return Token(TokenType.OR, value, start_line, start_column)
if value == "lnot":
    return Token(TokenType.NOT, value, start_line, start_column)
```

**Already simplified:** YES - English keywords already removed. No further simplification needed.

### 2. Parser (`src/txt2tex/parser.py`)

#### 2.1 Prose Word Rejection (Lines 1552-1586)
**Complexity Score: MEDIUM**

The parser maintains a 28-word set to reject prose during expression parsing:

```python
# Lines 1555-1585: Hardcoded prose words
prose_words = {
    "is", "are", "be", "was", "were", "true", "false",
    "the", "a", "an", "to", "of", "for", "with", "as", "by",
    "from", "that", "this", "these", "those", "it", "its",
    "they", "them", "syntax", "valid", "here", "there"
}
if current.value.lower() in prose_words:
    return False
```

**Can be simplified:** YES - This exists primarily to prevent prose from being parsed as expressions when English keywords were ambiguous. With unambiguous LaTeX keywords, this check becomes less critical.

### 3. LaTeX Generator (`src/txt2tex/latex_gen.py`)

#### 3.1 Prose Text Processing (Lines 1982-2063)
**Complexity Score: LOW**

Comments indicate awareness but no actual English keyword conversion:

```python
# Line 1982: Comment states "Do NOT convert and/or/not - those are English words"
# Line 2038: Comment "NOTE: 'not elem' is English prose, not 'notin' keyword"
```

**Already correct:** YES - Generator already treats English words as prose only.

#### 3.2 Inline Math Detection (Lines 2941-2984)
**Complexity Score: MEDIUM**

Another hardcoded prose word set (40+ words) for detecting non-math content:

```python
# Lines 2942-2982: Duplicate prose detection
prose_words = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been",
    "have", "has", "had", "do", "does", "did", "will", "would",
    # ... 23 more entries
}
```

**Can be removed:** PARTIAL - This helps detect failed parse attempts but duplicates lexer logic.

---

## Prioritized Action Items

### Priority 1: Remove Prose Detection Logic (High Impact)
1. **Remove lines 956-1180 from lexer.py**
   - Eliminates 225 lines of complex prose detection
   - Removes 87+ hardcoded prose starters
   - Simplifies identifier scanning significantly

2. **Simplify `_scan_identifier()` method**
   - Remove prose detection branches
   - Keep only keyword recognition for LaTeX-style operators
   - Estimated reduction: ~150 lines

### Priority 2: Consolidate Prose Word Lists (Medium Impact)
1. **Create single `PROSE_WORDS` constant**
   - Define once in a common location (e.g., `constants.py`)
   - Import where needed instead of duplicating

2. **Remove duplicate lists from:**
   - Parser (lines 1555-1585)
   - LaTeX generator (lines 2942-2982)

3. **Estimated reduction:** ~80 lines of duplicated data

### Priority 3: Remove Obsolete Comments (Low Impact)
1. **Clean up misleading comments about English keywords**
   - Line 1982 in latex_gen.py
   - Line 2038 in latex_gen.py
   - Any other references to deprecated English operators

### Priority 4: Simplify Article Detection (Low Impact)
1. **Update `z_keywords` set in lexer**
   - Remove references to "and", "or", "not", "in"
   - Keep only actual Z notation keywords

---

## Risk Assessment

### Low Risk Areas
1. **Keyword recognition** - English keywords already unsupported
2. **Comment cleanup** - No functional impact
3. **Constant consolidation** - Pure refactoring

### Medium Risk Areas
1. **Prose detection removal** - May affect edge cases where prose accidentally gets tokenized
   - Mitigation: Keep minimal prose detection for true ambiguous cases

2. **Article detection simplification** - "A" and "An" still need some disambiguation
   - Mitigation: Preserve logic but simplify keyword list

### High Risk Areas
None identified - The English keywords are already deprecated and unsupported, so removing their handling logic poses no backward compatibility risk.

---

## Implementation Strategy

### Phase 1: Analysis and Testing (2 hours)
1. Create comprehensive test suite for current prose handling
2. Identify any edge cases that still rely on prose detection
3. Document actual vs perceived dependencies

### Phase 2: Incremental Removal (4 hours)
1. Start with comment cleanup (no functional change)
2. Consolidate prose word lists (refactoring only)
3. Remove prose detection logic in small commits
4. Run full test suite after each change

### Phase 3: Validation (2 hours)
1. Run all 1137 tests
2. Test with `solutions.txt` and other complex documents
3. Verify PDF generation still works correctly
4. Check for any performance improvements

---

## Expected Benefits

1. **Code Reduction:** ~400-500 lines removed
2. **Complexity Reduction:** Eliminate complex lookahead patterns and string scanning
3. **Maintainability:** Simpler lexer logic, easier to understand and modify
4. **Performance:** Marginal improvement from reduced string operations
5. **Clarity:** Clear separation between prose and logical operators

---

## Conclusion

The deprecation of English keywords (`and`, `or`, `not`, `in`) in favor of LaTeX-style keywords (`land`, `lor`, `lnot`, `elem`) presents a significant opportunity to simplify the txt2tex codebase. The analysis reveals approximately **400-500 lines of code** that exist solely to handle the ambiguity between English prose and logical operators.

Since the English keywords are already unsupported (only LaTeX-style keywords are recognized), this complexity serves no purpose and actively hinders maintainability. The recommended cleanup can be performed safely with minimal risk, as it removes code for a feature that no longer exists.

### Recommendation
**Proceed with the cleanup** in the prioritized order, using the incremental implementation strategy to ensure safety and maintain test coverage throughout the process.