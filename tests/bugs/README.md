# txt2tex Test Files: Bugs, Regressions, and Features

This directory contains test files organized into three categories:
1. **Active Bugs** (1 file) - Real bugs currently open on GitHub
2. **Broken Tests** (13 files) - Tests that fail but may represent stale test cases
3. **Passing Tests** (12 files) - Regression and feature tests that pass

## Active Bugs (1 file)

Real bugs that are currently open on GitHub and need fixing.

### Bug #1: Parser fails on prose mixed with inline math (periods)
- **File**: [bug1_prose_period.txt](bug1_prose_period.txt)
- **Issue**: [#1](https://github.com/jmf-pobox/txt2tex/issues/1)
- **Priority**: HIGH
- **Status**: ACTIVE
- **Test Command**:
  ```bash
  hatch run cli tests/bugs/bug1_prose_period.txt --tex-only
  ```
- **Expected**: Should parse and render correctly
- **Actual**: `Error: Expected ')' after expression`
- **Workaround**: Use TEXT blocks for prose with periods
- **Impact**: Blocks natural writing style, especially for homework problems

---

## Broken Tests (13 files)

These tests fail. They may represent:
- Bugs that were never actually fixed
- Test cases that use unsupported syntax
- Stale test cases that need updating

### Failing "Regression" Tests (10 files)

These were documented as "resolved" but actually fail:

| File | Error |
|------|-------|
| regression_in_operator_basic.txt | Parser error |
| regression_in_operator_with_comparison.txt | Parser error |
| regression_in_operator_multiple_same.txt | Parser error |
| regression_in_operator_multiple_nested.txt | Parser error |
| regression_in_operator_before_bullet.txt | Parser error |
| regression_in_notin_operators_combined.txt | Parser error |
| regression_in_operator_patterns.txt | Parser error |
| regression_bullet_separator_basic.txt | Parser error |
| regression_bullet_separator_with_notin.txt | Parser error |
| regression_bullet_separator_notin_paren.txt | Parser error |

### Failing Bug Files (2 files)

These were documented as "resolved" for Issue #3 but fail:

| File | Status |
|------|--------|
| bug3_compound_id.txt | FAIL - abbrev block syntax not working |
| bug3_test_simple.txt | FAIL - abbrev block syntax not working |

### Failing Feature Test (1 file)

| File | Status |
|------|--------|
| feature_semicolon_separator.txt | FAIL - semicolon separator syntax not working |

---

## Passing Tests (12 files)

### Resolved Bug (1 file)

- **bug2_multiple_pipes.txt** - Issue [#2](https://github.com/jmf-pobox/txt2tex/issues/2) appears to be fixed
  - Multiple pipes in TEXT blocks now work correctly

### TEXT Block Operators (2 files) - Issues #4, #5

- [regression_text_comma_after_parens.txt](regression_text_comma_after_parens.txt) ✓
  - **Issue**: [#4](https://github.com/jmf-pobox/txt2tex/issues/4) (CLOSED)
  - **Test**: `(not p => not q), (q => p)` → `¬ p ⇒ ¬ q, q ⇒ p`

- [regression_text_logical_operators.txt](regression_text_logical_operators.txt) ✓
  - **Issue**: [#5](https://github.com/jmf-pobox/txt2tex/issues/5) (CLOSED)
  - **Test**: `(p or q)` → `p ∨ q`, `(p and q)` → `p ∧ q`

### Set Operators (3 files)

- [regression_in_operator_simple.txt](regression_in_operator_simple.txt) ✓ - Simple `y in T`
- [regression_subset_operator.txt](regression_subset_operator.txt) ✓ - `subset` operator
- [regression_notin_operator.txt](regression_notin_operator.txt) ✓ - `notin` operator

### Feature Tests - Justification Formatting (6 files)

All justification formatting tests pass:

- [feature_justification_caret_operator.txt](feature_justification_caret_operator.txt) ✓
- [feature_justification_empty_sequence.txt](feature_justification_empty_sequence.txt) ✓
- [feature_justification_nonempty_sequence.txt](feature_justification_nonempty_sequence.txt) ✓
- [feature_justification_space_preservation.txt](feature_justification_space_preservation.txt) ✓
- [feature_justification_word_identifiers.txt](feature_justification_word_identifiers.txt) ✓
- [feature_bag_syntax_in_free_types.txt](feature_bag_syntax_in_free_types.txt) ✓

---

## Summary Statistics

| Category | Count | Status |
|----------|-------|--------|
| Active Bugs | 1 | Need fixing |
| Broken Tests | 13 | Need investigation |
| Passing Tests | 12 | All PASS |
| **Total** | **26** | **12 PASS, 14 FAIL** |

---

## Testing All Files

### Quick Status Check
```bash
cd /path/to/txt2tex/sem
for f in tests/bugs/*.txt; do
  echo -n "$(basename $f): "
  hatch run cli "$f" --tex-only >/dev/null 2>&1 && echo "PASS" || echo "FAIL"
done
```

### Test Active Bugs (expect FAIL)
```bash
hatch run cli tests/bugs/bug1_prose_period.txt --tex-only
```

### Test Passing Files (expect PASS)
```bash
for f in tests/bugs/regression_text_*.txt tests/bugs/feature_justification*.txt; do
  echo -n "$(basename $f): "
  hatch run cli "$f" --tex-only >/dev/null 2>&1 && echo "PASS" || echo "FAIL"
done
```

---

## References

- **[GitHub Issues](https://github.com/jmf-pobox/txt2tex/issues)** - Live bug tracking
- **[FUZZ_FEATURE_GAPS.md](../../docs/guides/FUZZ_FEATURE_GAPS.md)** - Missing features vs bugs

---

**Last Updated**: 2025-11-29
**Active Bugs**: 1 (Issue #1)
**Test Results**: 12 PASS, 14 FAIL
