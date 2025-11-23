# txt2tex Test Files: Bugs, Regressions, and Features

This directory contains test files organized into three categories:
1. **Active Bugs** (4 files) - Real bugs currently open on GitHub
2. **Regression Tests** (15 files) - Previously fixed bugs, now serving as regression protection
3. **Feature Tests** (7 files) - Edge cases and features that were never bugs

## Active Bugs (4 files)

Real bugs that are currently open on GitHub and need fixing.

### Bug #1: Parser fails on prose mixed with inline math (periods)
- **File**: [bug1_prose_period.txt](bug1_prose_period.txt)
- **Issue**: [#1](https://github.com/jmf-pobox/txt2tex/issues/1)
- **Priority**: HIGH
- **Status**: ACTIVE
- **Test Command**:
  ```bash
  hatch run convert tests/bugs/bug1_prose_period.txt
  ```
- **Expected**: Should parse and render correctly
- **Actual**: `Error: Line 3, column 26: Expected identifier, number, '(', '{', '⟨', or lambda, got PERIOD`
- **Workaround**: Use TEXT blocks for prose with periods
- **Impact**: Blocks natural writing style, especially for homework problems

### Bug #2: TEXT blocks with multiple pipes close math mode prematurely
- **File**: [bug2_multiple_pipes.txt](bug2_multiple_pipes.txt)
- **Issue**: [#2](https://github.com/jmf-pobox/txt2tex/issues/2)
- **Priority**: MEDIUM
- **Status**: ACTIVE
- **Test Command**:
  ```bash
  hatch run convert tests/bugs/bug2_multiple_pipes.txt
  pdftotext tests/bugs/bug2_multiple_pipes.pdf -
  ```
- **Expected**: All pipes should be in math mode: `(µ p : ran hd • (∀ q : ran hd • p ≠ q • p.2 > q.2))`
- **Actual**: Second pipe appears as text: `p ̸= q| p.2 > q.2` (pipe outside math mode)
- **Workaround**: Use proper Z notation blocks (axdef, schema) instead of TEXT
- **Impact**: Solution 40(g) and similar complex expressions

### Bug #3: Compound identifiers with operator suffixes fail
- **Files**:
  - [bug3_compound_id.txt](bug3_compound_id.txt) - Full test with TEXT description
  - [bug3_test_simple.txt](bug3_test_simple.txt) - Minimal failing case
- **Issue**: [#3](https://github.com/jmf-pobox/txt2tex/issues/3)
- **Priority**: MEDIUM
- **Status**: ACTIVE
- **Test Command**:
  ```bash
  hatch run convert tests/bugs/bug3_compound_id.txt
  hatch run convert tests/bugs/bug3_test_simple.txt  # Both fail
  ```
- **Expected**: Should define `R+` as an identifier
- **Actual**: `Error: Line 4/5, column 6/1: Expected identifier...` (lexer tokenizes as R followed by +)
- **Workaround**: None available
- **Impact**: **Blocks Solution 31** (transitive closure R+) - only solution not working (51/52 = 98.1%)

### Bug #13: Field projection on function application in quantifiers
- **File**: None yet (documented in GitHub issue)
- **Issue**: [#13](https://github.com/jmf-pobox/txt2tex/issues/13)
- **Priority**: MEDIUM
- **Status**: ACTIVE
- **Description**: Field projection like `f(i).field` incorrectly parsed as bullet separator in quantifier bodies
- **Workaround**: Use intermediate binding with semicolon separator
- **Impact**: Blocks field access on function return values

---

## Regression Tests (15 files)

Previously fixed bugs that now serve as regression tests. All these files PASS (compile successfully).

### IN Operator Disambiguation (8 files) - Resolved Phase 18 (Nov 18, 2025)

Fixed issue where `in` operator was incorrectly parsed in various contexts.

- [regression_in_operator_basic.txt](regression_in_operator_basic.txt) - Basic `in` operator parsing
- [regression_in_operator_simple.txt](regression_in_operator_simple.txt) - Simple membership `y in T`
- [regression_in_operator_with_comparison.txt](regression_in_operator_with_comparison.txt) - `in` with comparisons
- [regression_in_operator_multiple_same.txt](regression_in_operator_multiple_same.txt) - Multiple `in` operators, same precedence
- [regression_in_operator_multiple_nested.txt](regression_in_operator_multiple_nested.txt) - Multiple `in` operators, different levels
- [regression_in_operator_before_bullet.txt](regression_in_operator_before_bullet.txt) - `in` before bullet separator
- [regression_in_notin_operators_combined.txt](regression_in_notin_operators_combined.txt) - Combined `in` and `notin`
- [regression_in_operator_patterns.txt](regression_in_operator_patterns.txt) - Various `in` patterns

**Test Command**:
```bash
for f in tests/bugs/regression_in_operator*.txt tests/bugs/regression_in_notin*.txt; do
  hatch run convert "$f"
done
```

### Bullet Separator (3 files) - Resolved Phase 18

Fixed bullet separator (`.` for constraint/body in quantifiers) parsing with `notin` operator.

- [regression_bullet_separator_basic.txt](regression_bullet_separator_basic.txt) - Basic bullet separator
- [regression_bullet_separator_with_notin.txt](regression_bullet_separator_with_notin.txt) - Bullet with `notin`
- [regression_bullet_separator_notin_paren.txt](regression_bullet_separator_notin_paren.txt) - Bullet with parenthesized `notin`

**Related**: GitHub Issue [#8](https://github.com/jmf-pobox/txt2tex/issues/8) (CLOSED)

### TEXT Block Operators (2 files) - Resolved Issues #4, #5

Fixed operator conversion in TEXT blocks.

- [regression_text_comma_after_parens.txt](regression_text_comma_after_parens.txt)
  - **Issue**: [#4](https://github.com/jmf-pobox/txt2tex/issues/4) (CLOSED)
  - **Resolved**: Commit 7f6a932 (Pattern -0.5 with balanced parenthesis matching)
  - **Fix**: Commas after parenthesized math now correctly included in math mode
  - **Test**: `(not p => not q), (q => p)` → `¬ p ⇒ ¬ q, q ⇒ p` ✓

- [regression_text_logical_operators.txt](regression_text_logical_operators.txt)
  - **Issue**: [#5](https://github.com/jmf-pobox/txt2tex/issues/5) (CLOSED)
  - **Resolved**: Commit b709351 (Pattern -0.5)
  - **Fix**: Logical operators `or`/`and` in TEXT blocks now correctly converted
  - **Test**: `(p or q)` → `p ∨ q`, `(p and q)` → `p ∧ q` ✓

### Set Operators (2 files) - Resolved Phase 18

Fixed parsing of subset and notin operators.

- [regression_subset_operator.txt](regression_subset_operator.txt) - `subset` operator parsing
- [regression_notin_operator.txt](regression_notin_operator.txt) - `notin` operator parsing

---

## Feature Tests (7 files)

Tests for complex features and edge cases. These were **never bugs** - they document features that have always worked.

### Justification Formatting (5 files)

Edge case tests for operator formatting in EQUIV and PROOF justifications.

- [feature_justification_caret_operator.txt](feature_justification_caret_operator.txt) - Caret (^) in justifications
- [feature_justification_empty_sequence.txt](feature_justification_empty_sequence.txt) - Empty sequences in justifications
- [feature_justification_nonempty_sequence.txt](feature_justification_nonempty_sequence.txt) - Non-empty sequences in justifications
- [feature_justification_space_preservation.txt](feature_justification_space_preservation.txt) - Space preservation in justifications
- [feature_justification_word_identifiers.txt](feature_justification_word_identifiers.txt) - Word identifiers in justifications

**Test Command**:
```bash
for f in tests/bugs/feature_justification*.txt; do
  hatch run convert "$f"
done
```

### Advanced Syntax (2 files)

Tests for advanced syntax features.

- [feature_semicolon_separator.txt](feature_semicolon_separator.txt)
  - **Feature**: Semicolon separator in quantifiers
  - **Related**: GitHub Issue [#7](https://github.com/jmf-pobox/txt2tex/issues/7) (CLOSED - feature implemented)
  - **Test**: `forall x : N; y : N | P` (semicolon separates multiple typed declarations)

- [feature_bag_syntax_in_free_types.txt](feature_bag_syntax_in_free_types.txt)
  - **Feature**: Bag notation `[[...]]` in free type definitions
  - **Test**: Complex free types with bag syntax

---

## Summary Statistics

| Category | Count | Status |
|----------|-------|--------|
| Active Bugs | 4 | Need fixing |
| Regression Tests | 15 | All PASS |
| Feature Tests | 7 | All PASS |
| **Total** | **26** | **22 PASS, 4 FAIL** |

**Project Coverage**: 98.1% (51/52 solutions working) - only Bug #3 blocks remaining solution

---

## Testing All Files

### Test Active Bugs (expect FAIL)
```bash
cd /Users/jfreeman/Coding/fuzz/txt2tex/sem
for f in tests/bugs/bug*.txt; do
  echo "Testing: $f"
  hatch run convert "$f" 2>&1 | head -5
done
```

### Test Regression Files (expect PASS)
```bash
for f in tests/bugs/regression_*.txt; do
  echo "Testing: $f"
  hatch run convert "$f" >/dev/null 2>&1 && echo "  PASS" || echo "  FAIL"
done
```

### Test Feature Files (expect PASS)
```bash
for f in tests/bugs/feature_*.txt; do
  echo "Testing: $f"
  hatch run convert "$f" >/dev/null 2>&1 && echo "  PASS" || echo "  FAIL"
done
```

---

## Bug Reporting Workflow

Found a new bug? Follow this workflow:

1. **Create minimal test case**:
   ```bash
   cat > tests/bugs/bugN_short_name.txt << 'EOF'
   === Bug N Test: Description ===

   [minimal failing example]
   EOF
   ```

2. **Verify it fails**:
   ```bash
   hatch run convert tests/bugs/bugN_short_name.txt
   ```

3. **Create GitHub issue**:
   - Use [bug report template](../../.github/ISSUE_TEMPLATE/bug_report.md)
   - Include test case location and exact error/output
   - See [.github/ISSUES_TO_CREATE.md](../../.github/ISSUES_TO_CREATE.md) for examples

4. **Update documentation**:
   - Add bug to this README
   - Add bug to [STATUS.md](../../docs/development/STATUS.md) Bug Tracking table
   - Add bug to [ISSUES.md](../../ISSUES.md)

---

## References

- **[STATUS.md](../../docs/development/STATUS.md)** - Implementation status with bug tracking table
- **[ISSUES.md](../../ISSUES.md)** - Comprehensive issue tracking document
- **[GitHub Issues](https://github.com/jmf-pobox/txt2tex/issues)** - Live bug tracking
- **[FUZZ_FEATURE_GAPS.md](../../docs/guides/FUZZ_FEATURE_GAPS.md)** - Missing features vs bugs

---

**Last Updated**: 2025-11-23
**Active Bugs**: 4 (Issues #1, #2, #3, #13)
**Test Coverage**: 22 regression + feature tests ensure stability
